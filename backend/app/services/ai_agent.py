import logging
import uuid

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.company import Company
from app.models.lead import Lead
from app.services.ai_tools import TOOLS, execute_tool

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

REGLAS GENERALES:
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
    """Generate AI response using Claude API with tools."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    system_prompt = build_system_prompt(company, lead)

    try:
        response = await client.messages.create(
            model=company.ai_model or settings.ai_model,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=conversation_history,
        )

        # Process tool calls if any
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

                # Send tool result back to Claude for final response
                follow_up = await client.messages.create(
                    model=company.ai_model or settings.ai_model,
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

                # Update usage from follow-up
                response = follow_up

        return {
            "text": result_text,
            "model": response.model,
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens,
            "tools_used": tools_used,
        }

    except anthropic.APIError:
        logger.exception("Claude API error")
        return {
            "text": "Disculpa, estoy teniendo un problema tecnico. Un miembro del equipo te va a responder pronto.",
            "model": "fallback",
            "tokens_in": 0,
            "tokens_out": 0,
            "tools_used": [],
        }
