import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.company import Company
from app.models.lead import Lead
from app.services.ai_tools import TOOLS, TOOLS_OPENAI, execute_tool

logger = logging.getLogger(__name__)


def build_system_prompt(company: Company, lead: Lead | None = None) -> str:
    """Build dynamic system prompt based on company config."""
    prompt = f"""Eres el asistente de ventas de {company.name}.
{company.description or ''}

PERSONALIDAD: {company.ai_personality or 'Amigable y profesional'}
IDIOMA: {company.ai_language or 'Espanol'}
OBJETIVO: {company.ai_sales_goal or 'Ayudar al cliente y guiarlo hacia una compra o cita'}

TIPO DE NEGOCIO: {company.business_type or 'General'}
MONEDA: {company.currency or 'USD'}

REGLAS:
1. NUNCA inventar precios, datos ni disponibilidad — siempre usar tools
2. Si no sabes algo, decir "voy a consultarlo con el equipo y te respondo"
3. Respuestas cortas (max 3 parrafos, pensando en WhatsApp)
4. Usar emojis con moderacion (max 2 por mensaje)
5. Si el lead muestra alta intencion, sugerir agendar cita/visita
6. Si piden hablar con un humano, hacer handoff inmediato
7. Ser natural y conversacional, no robotico"""

    if company.ai_custom_rules:
        prompt += f"\n\nREGLAS ADICIONALES:\n{company.ai_custom_rules}"

    if lead:
        lead_info = []
        if lead.name:
            lead_info.append(f"Nombre: {lead.name}")
        if lead.city:
            lead_info.append(f"Ciudad: {lead.city}")
        if lead.budget_range:
            lead_info.append(f"Presupuesto: {lead.budget_range}")
        if lead.timeline:
            lead_info.append(f"Timeline: {lead.timeline}")
        if lead.needs_summary:
            lead_info.append(f"Necesidades: {lead.needs_summary}")
        if lead_info:
            prompt += "\n\nDATOS DEL CLIENTE:\n" + "\n".join(lead_info)

    return prompt


async def generate_response(
    company: Company,
    lead: Lead | None,
    conversation_history: list[dict],
    db: AsyncSession,
    company_id: uuid.UUID,
) -> dict:
    """Generate AI response using configured provider (Groq or Anthropic)."""
    if settings.ai_provider == "groq":
        return await _generate_groq(company, lead, conversation_history, db, company_id)
    else:
        return await _generate_anthropic(company, lead, conversation_history, db, company_id)


async def _generate_groq(
    company: Company,
    lead: Lead | None,
    conversation_history: list[dict],
    db: AsyncSession,
    company_id: uuid.UUID,
) -> dict:
    """Generate response using Groq API (OpenAI-compatible)."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)
    system_prompt = build_system_prompt(company, lead)
    model = company.ai_model or settings.ai_model

    # Enrich system prompt with catalog (prices from DB) and KB (smart retrieval)
    catalog_context = await _get_catalog_context(db, company_id)
    from app.services.kb_manager import get_relevant_kb
    kb_items = await get_relevant_kb(db, company_id, channel="whatsapp", max_items=10)
    kb_context = "\n".join(
        f"- {item.title}: {item.content[:300]}" for item in kb_items
    ) if kb_items else ""
    enriched_prompt = system_prompt
    if catalog_context:
        enriched_prompt += f"\n\nCATALOGO DE PRODUCTOS DISPONIBLES:\n{catalog_context}"
    if kb_context:
        enriched_prompt += f"\n\nINFORMACION ADICIONAL (FAQ/KB):\n{kb_context}"

    messages = [{"role": "system", "content": enriched_prompt}, *conversation_history]

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )

        choice = response.choices[0]
        result_text = choice.message.content or ""

        return {
            "text": result_text,
            "model": response.model,
            "tokens_in": response.usage.prompt_tokens if response.usage else 0,
            "tokens_out": response.usage.completion_tokens if response.usage else 0,
            "tools_used": [],
        }

    except Exception as e:
        logger.exception("Groq API error: %s", str(e))
        return {
            "text": f"Disculpa, estoy teniendo un problema tecnico. Un miembro del equipo te va a responder pronto. (debug: {type(e).__name__}: {str(e)[:100]})",
            "model": "fallback",
            "tokens_in": 0,
            "tokens_out": 0,
            "tools_used": [],
        }


async def _get_catalog_context(db: AsyncSession, company_id: uuid.UUID) -> str:
    """Load product catalog as text for inline RAG."""
    from sqlalchemy import select
    from app.models.product import Product

    result = await db.execute(
        select(Product)
        .where(Product.company_id == company_id, Product.is_active.is_(True))
        .order_by(Product.display_order)
        .limit(20)
    )
    products = result.scalars().all()
    if not products:
        return ""

    lines = []
    for p in products:
        price_str = f"${p.price} {p.price_currency}" if p.price else "Consultar"
        lines.append(f"- {p.name} ({p.category or 'General'}): {price_str}")
        if p.short_desc:
            lines.append(f"  {p.short_desc}")
        if p.specs:
            specs_str = ", ".join(f"{k}: {v}" for k, v in p.specs.items())
            lines.append(f"  Specs: {specs_str}")
        if p.features:
            lines.append(f"  Incluye: {', '.join(p.features)}")
        if p.price_notes:
            lines.append(f"  Nota: {p.price_notes}")
    return "\n".join(lines)


async def _get_kb_context(db: AsyncSession, company_id: uuid.UUID) -> str:
    """Load knowledge base items as text for inline RAG."""
    from sqlalchemy import select
    from app.models.knowledge import KnowledgeItem

    result = await db.execute(
        select(KnowledgeItem)
        .where(KnowledgeItem.company_id == company_id, KnowledgeItem.is_active.is_(True))
        .limit(10)
    )
    items = result.scalars().all()
    if not items:
        return ""

    lines = []
    for item in items:
        lines.append(f"- {item.title or 'Info'}: {item.content[:300]}")
    return "\n".join(lines)


async def _generate_anthropic(
    company: Company,
    lead: Lead | None,
    conversation_history: list[dict],
    db: AsyncSession,
    company_id: uuid.UUID,
) -> dict:
    """Generate response using Claude API."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system_prompt = build_system_prompt(company, lead)

    try:
        response = await client.messages.create(
            model=company.ai_model or "claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=conversation_history,
        )

        result_text = ""
        tools_used = []

        for block in response.content:
            if block.type == "text":
                result_text += block.text
            elif block.type == "tool_use":
                tools_used.append(block.name)
                tool_result = await execute_tool(
                    tool_name=block.name,
                    tool_input=block.input,
                    db=db,
                    company_id=company_id,
                )

                follow_up = await client.messages.create(
                    model=company.ai_model or "claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    tools=TOOLS,
                    messages=[
                        *conversation_history,
                        {"role": "assistant", "content": response.content},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": str(tool_result),
                                }
                            ],
                        },
                    ],
                )

                for fb in follow_up.content:
                    if fb.type == "text":
                        result_text += fb.text
                response = follow_up

        return {
            "text": result_text,
            "model": response.model,
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens,
            "tools_used": tools_used,
        }

    except Exception:
        logger.exception("Claude API error")
        return {
            "text": "Disculpa, estoy teniendo un problema tecnico. Un miembro del equipo te va a responder pronto.",
            "model": "fallback",
            "tokens_in": 0,
            "tokens_out": 0,
            "tools_used": [],
        }
