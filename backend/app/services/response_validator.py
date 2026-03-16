"""Response validator — validates AI responses BEFORE sending to customer.
Checks prices, product existence, and policy compliance."""

import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

logger = logging.getLogger(__name__)

# Regex to find prices in text: $18,500, $18.500, 18500 USD, USD 18500, etc.
PRICE_REGEX = re.compile(
    r'\$\s?([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)'  # $18,500 or $18.500
    r'|'
    r'([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*(?:USD|usd|dolares|dólares)'  # 18500 USD
    r'|'
    r'(?:USD|usd)\s*([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)'  # USD 18500
)

# Keywords that should trigger escalation, not auto-response
ESCALATION_KEYWORDS = [
    "garantia legal", "demanda", "abogado", "denuncia",
    "devolucion de dinero", "estafa", "mentira",
]

# Things the bot should NEVER say
FORBIDDEN_PATTERNS = [
    r"(?i)mejor que (?:la )?competencia",
    r"(?i)(?:peor|malo|mala|pesimo) (?:que|de) \w+",  # negative competitor comparison
    r"(?i)te garantizo que",
    r"(?i)(?:100|cien) por ciento seguro",
    r"(?i)no hay riesgo",
]


def extract_prices(text: str) -> list[float]:
    """Extract all monetary values from text."""
    prices = []
    for match in PRICE_REGEX.finditer(text):
        # Get the matched group (one of 3 groups will match)
        raw = match.group(1) or match.group(2) or match.group(3)
        if raw:
            # Normalize: remove thousands separators
            clean = raw.replace(".", "").replace(",", ".")
            # If the last segment is 3 digits, it's a thousands separator not decimal
            parts = raw.split(".")
            if len(parts) > 1 and len(parts[-1]) == 3:
                clean = raw.replace(".", "")
            try:
                prices.append(float(clean))
            except ValueError:
                pass
    return prices


async def validate_response(
    db: AsyncSession,
    company_id: uuid.UUID,
    ai_response: str,
) -> dict:
    """Validate AI response before sending. Returns validation result."""
    issues = []
    corrected_response = ai_response

    # 1. Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, ai_response):
            issues.append({
                "type": "forbidden_pattern",
                "severity": "warning",
                "message": f"Respuesta contiene patron no permitido: {pattern}",
            })

    # 2. Check for escalation keywords
    text_lower = ai_response.lower()
    for keyword in ESCALATION_KEYWORDS:
        if keyword in text_lower:
            issues.append({
                "type": "escalation_needed",
                "severity": "critical",
                "message": f"Tema sensible detectado: '{keyword}' — escalar a humano",
            })

    # 3. Validate prices against catalog
    mentioned_prices = extract_prices(ai_response)
    if mentioned_prices:
        # Get all product prices for this company
        result = await db.execute(
            select(Product.name, Product.price)
            .where(Product.company_id == company_id, Product.is_active.is_(True))
        )
        catalog_prices = {str(int(float(p))): name for name, p in result.all() if p}

        for price in mentioned_prices:
            price_int = str(int(price))
            if price_int not in catalog_prices:
                # Price not in catalog — could be a hallucination
                # Check if it's close to any catalog price (within 10%)
                close_match = None
                for cat_price_str, cat_name in catalog_prices.items():
                    cat_price = float(cat_price_str)
                    if cat_price > 0 and abs(price - cat_price) / cat_price < 0.10:
                        close_match = (cat_name, cat_price)
                        break

                if close_match:
                    # Close but not exact — correct it
                    issues.append({
                        "type": "price_corrected",
                        "severity": "warning",
                        "message": f"Precio ${price:,.0f} corregido a ${close_match[1]:,.0f} ({close_match[0]})",
                        "original": price,
                        "corrected": close_match[1],
                    })
                    corrected_response = corrected_response.replace(
                        f"${price:,.0f}", f"${close_match[1]:,.0f}"
                    )
                else:
                    # Price not in catalog at all — might be a calculation or hallucination
                    # Only flag if it looks like a product price (> $100)
                    if price > 100:
                        issues.append({
                            "type": "price_unverified",
                            "severity": "info",
                            "message": f"Precio ${price:,.0f} mencionado no coincide con ningun producto del catalogo",
                        })

    # 4. Check response length (WhatsApp optimal)
    if len(ai_response) > 1500:
        issues.append({
            "type": "response_too_long",
            "severity": "info",
            "message": f"Respuesta muy larga ({len(ai_response)} chars). Optimo para WhatsApp: <1000 chars.",
        })

    # Determine overall validation result
    critical = [i for i in issues if i["severity"] == "critical"]
    should_escalate = len(critical) > 0

    return {
        "valid": not should_escalate,
        "should_escalate": should_escalate,
        "issues": issues,
        "original_response": ai_response,
        "corrected_response": corrected_response,
    }
