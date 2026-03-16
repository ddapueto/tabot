import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.knowledge import KnowledgeItem

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "name": "buscar_producto",
        "description": "Busca productos o servicios en el catalogo de la empresa que coincidan con los criterios del cliente",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Busqueda en texto libre",
                },
                "category": {
                    "type": "string",
                    "description": "Categoria del producto/servicio",
                },
                "price_max": {
                    "type": "string",
                    "description": "Precio maximo (numero como texto)",
                },
            },
        },
    },
    {
        "name": "consultar_precio",
        "description": "Obtiene el precio detallado de un producto/servicio con sus opciones",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "ID del producto"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "consultar_faq",
        "description": "Busca respuestas en la base de conocimiento de la empresa (FAQs, politicas, info)",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Pregunta a buscar"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "actualizar_lead",
        "description": "Actualiza datos del lead basado en info mencionada en la conversacion",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "city": {"type": "string"},
                "budget_range": {"type": "string"},
                "timeline": {
                    "type": "string",
                    "enum": ["inmediato", "1_mes", "3_meses", "6_meses", "explorando"],
                },
                "needs_summary": {"type": "string"},
            },
        },
    },
    {
        "name": "escalar_a_humano",
        "description": "Transfiere la conversacion a un vendedor humano",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Razon del escalamiento"},
                "urgency": {"type": "string", "enum": ["normal", "high"]},
            },
            "required": ["reason"],
        },
    },
]

# OpenAI/Groq format (wraps each tool in {"type": "function", "function": {...}})
TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        },
    }
    for tool in TOOLS
]


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    db: AsyncSession,
    company_id: uuid.UUID,
) -> str:
    """Execute a tool and return the result as string."""
    try:
        if tool_name == "buscar_producto":
            return await _buscar_producto(db, company_id, tool_input)
        elif tool_name == "consultar_precio":
            return await _consultar_precio(db, company_id, tool_input)
        elif tool_name == "consultar_faq":
            return await _consultar_faq(db, company_id, tool_input)
        elif tool_name == "actualizar_lead":
            return f"Datos del lead actualizados: {tool_input}"
        elif tool_name == "escalar_a_humano":
            return f"Conversacion escalada a un vendedor. Razon: {tool_input.get('reason')}"
        else:
            return f"Tool '{tool_name}' no reconocido"
    except Exception:
        logger.exception("Error executing tool %s", tool_name)
        return f"Error al ejecutar {tool_name}"


async def _buscar_producto(db: AsyncSession, company_id: uuid.UUID, params: dict) -> str:
    """Search products by criteria."""
    query = (
        select(Product)
        .where(Product.company_id == company_id, Product.is_active.is_(True))
    )

    if params.get("category"):
        query = query.where(Product.category == params["category"])
    if params.get("price_max"):
        try:
            price_max = float(str(params["price_max"]).replace(",", ""))
            query = query.where(Product.price <= price_max)
        except (ValueError, TypeError):
            pass

    query = query.order_by(Product.display_order).limit(5)
    result = await db.execute(query)
    products = result.scalars().all()

    if not products:
        return "No se encontraron productos que coincidan con los criterios."

    lines = []
    for p in products:
        price_str = f"${p.price} {p.price_currency}" if p.price else "Consultar"
        lines.append(f"- {p.name} ({p.category or 'General'}): {price_str}")
        if p.short_desc:
            lines.append(f"  {p.short_desc}")
        lines.append(f"  ID: {p.id}")

    return "Productos encontrados:\n" + "\n".join(lines)


async def _consultar_precio(db: AsyncSession, company_id: uuid.UUID, params: dict) -> str:
    """Get detailed pricing for a product."""
    try:
        product_id = uuid.UUID(params["product_id"])
    except (ValueError, KeyError):
        return "ID de producto invalido"

    result = await db.execute(
        select(Product)
        .where(Product.id == product_id, Product.company_id == company_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        return "Producto no encontrado"

    lines = [
        f"Producto: {product.name}",
        f"Precio: ${product.price} {product.price_currency}" if product.price else "Precio: Consultar",
    ]
    if product.price_notes:
        lines.append(f"Nota: {product.price_notes}")
    if product.description:
        lines.append(f"Descripcion: {product.description}")
    if product.features:
        lines.append(f"Caracteristicas: {', '.join(product.features)}")
    if product.specs:
        specs_str = ", ".join(f"{k}: {v}" for k, v in product.specs.items())
        lines.append(f"Specs: {specs_str}")

    if product.options:
        lines.append("Opciones adicionales:")
        for opt in product.options:
            price_str = f"+${opt.price}" if opt.price else "Incluido"
            lines.append(f"  - {opt.name}: {price_str}")

    return "\n".join(lines)


async def _consultar_faq(db: AsyncSession, company_id: uuid.UUID, params: dict) -> str:
    """Search knowledge base for FAQ answers."""
    question = params.get("question", "")

    # Simple text search (pgvector semantic search will be added in Issue #7)
    result = await db.execute(
        select(KnowledgeItem)
        .where(
            KnowledgeItem.company_id == company_id,
            KnowledgeItem.is_active.is_(True),
            KnowledgeItem.content.ilike(f"%{question}%"),
        )
        .limit(3)
    )
    items = result.scalars().all()

    if not items:
        return "No se encontro informacion sobre eso en nuestra base de conocimiento."

    lines = []
    for item in items:
        lines.append(f"- {item.title or 'Info'}: {item.content[:300]}")

    return "Informacion encontrada:\n" + "\n".join(lines)
