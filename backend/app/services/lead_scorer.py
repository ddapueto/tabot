"""Lead scoring engine — configurable rules + AI signal extraction."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStageHistory

logger = logging.getLogger(__name__)

# Default scoring rules (overridable per company via companies.scoring_rules)
DEFAULT_SCORING_RULES = {
    "dio_presupuesto": 15,
    "dio_email": 5,
    "dio_ubicacion": 10,
    "timeline_inmediato": 25,
    "timeline_1_mes": 20,
    "timeline_3_meses": 10,
    "timeline_explorando": 0,
    "pidio_precios": 10,
    "pidio_fotos": 5,
    "pidio_presupuesto": 15,
    "acepto_cita": 30,
    "multiple_interacciones": 10,
    "respondio_followup": 10,
    "dijo_solo_curiosidad": -15,
    "sin_respuesta_48h": -10,
    "precio_fuera_rango": -10,
    "cancelo_cita": -15,
}

VALID_STAGES = ["new", "interested", "qualified", "negotiating", "visiting", "closing", "won", "lost"]
STAGE_ORDER = {stage: i for i, stage in enumerate(VALID_STAGES)}

# Allowed transitions (from → list of valid next stages)
STAGE_TRANSITIONS = {
    "new": ["interested", "qualified", "lost"],
    "interested": ["qualified", "negotiating", "lost"],
    "qualified": ["negotiating", "visiting", "lost"],
    "negotiating": ["visiting", "closing", "lost"],
    "visiting": ["closing", "negotiating", "lost"],
    "closing": ["won", "lost", "negotiating"],
    "won": [],
    "lost": ["new", "interested"],  # reactivation
}


def get_priority(score: int) -> str:
    """Determine priority based on score."""
    if score >= 76:
        return "urgent"
    elif score >= 51:
        return "high"
    elif score >= 26:
        return "medium"
    return "low"


async def update_score(
    db: AsyncSession,
    lead: Lead,
    signals: list[str],
    scoring_rules: dict | None = None,
) -> int:
    """Update lead score based on detected signals."""
    rules = scoring_rules or DEFAULT_SCORING_RULES
    delta = sum(rules.get(signal, 0) for signal in signals)

    new_score = max(0, min(100, lead.score + delta))
    lead.score = new_score
    lead.priority = get_priority(new_score)

    await db.flush()

    logger.info("Lead %s score updated: %d → %d (signals: %s)", lead.id, lead.score - delta, new_score, signals)
    return new_score


async def change_stage(
    db: AsyncSession,
    lead: Lead,
    new_stage: str,
    changed_by: str = "system",
    reason: str | None = None,
) -> bool:
    """Change lead stage with validation and history tracking."""
    if new_stage not in VALID_STAGES:
        logger.warning("Invalid stage: %s", new_stage)
        return False

    current_stage = lead.stage
    if current_stage == new_stage:
        return True

    valid_next = STAGE_TRANSITIONS.get(current_stage, [])
    if new_stage not in valid_next:
        logger.warning("Invalid transition: %s → %s (allowed: %s)", current_stage, new_stage, valid_next)
        return False

    # Record history
    history = LeadStageHistory(
        lead_id=lead.id,
        from_stage=current_stage,
        to_stage=new_stage,
        changed_by=changed_by,
        reason=reason,
    )
    db.add(history)

    lead.stage = new_stage
    await db.flush()

    logger.info("Lead %s stage: %s → %s (by: %s)", lead.id, current_stage, new_stage, changed_by)
    return True


def extract_signals_from_message(content: str) -> list[str]:
    """Extract scoring signals from a message text (simple keyword-based)."""
    content_lower = content.lower()
    signals = []

    price_keywords = ["precio", "cuesta", "cuanto sale", "cuánto", "cotiz", "presupuesto"]
    if any(kw in content_lower for kw in price_keywords):
        signals.append("pidio_precios")

    photo_keywords = ["foto", "imagen", "ver", "mostrar", "galeria"]
    if any(kw in content_lower for kw in photo_keywords):
        signals.append("pidio_fotos")

    budget_keywords = ["presupuesto", "cotización", "cotizacion", "cuanto me saldria"]
    if any(kw in content_lower for kw in budget_keywords):
        signals.append("pidio_presupuesto")

    visit_keywords = ["visitar", "conocer", "ir a ver", "cita", "reunion", "agendar"]
    if any(kw in content_lower for kw in visit_keywords):
        signals.append("acepto_cita")

    curiosity_keywords = ["solo pregunt", "curiosidad", "no estoy segur", "solo mirando"]
    if any(kw in content_lower for kw in curiosity_keywords):
        signals.append("dijo_solo_curiosidad")

    location_keywords = ["terreno", "canelones", "montevideo", "maldonado", "rocha", "colonia"]
    if any(kw in content_lower for kw in location_keywords):
        signals.append("dio_ubicacion")

    email_keywords = ["@", "gmail", "hotmail", "email", "correo"]
    if any(kw in content_lower for kw in email_keywords):
        signals.append("dio_email")

    timeline_keywords = {
        "timeline_inmediato": ["urgente", "ya mismo", "lo antes posible", "inmediato", "esta semana"],
        "timeline_1_mes": ["este mes", "proximo mes", "en un mes"],
        "timeline_3_meses": ["3 meses", "tres meses", "para el verano"],
    }
    for signal, keywords in timeline_keywords.items():
        if any(kw in content_lower for kw in keywords):
            signals.append(signal)
            break

    return signals
