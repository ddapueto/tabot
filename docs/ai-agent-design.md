# Diseno del Agente IA de Ventas

## Principio Fundamental
El agente es **domain-agnostic**: se adapta a cualquier tipo de empresa
mediante configuracion y knowledge base. No tiene conocimiento hardcodeado
de ninguna industria.

## System Prompt Dinamico

El system prompt se ensambla en runtime para cada empresa:

```
Eres el asistente de ventas de {company.name}.
{company.description}

PERSONALIDAD: {company.ai_personality}
IDIOMA: {company.ai_language}
OBJETIVO: {company.ai_sales_goal}

HORARIO DE ATENCION: {company.business_hours}
MONEDA: {company.currency}

REGLAS GENERALES:
1. NUNCA inventar precios, datos ni disponibilidad — siempre usar tools
2. Si no sabes algo, decir "voy a consultarlo con el equipo y te respondo"
3. Respuestas cortas (max 3 parrafos, pensando en WhatsApp)
4. Usar emojis con moderacion (max 2 por mensaje)
5. Si el lead muestra alta intencion, sugerir agendar cita/visita
6. Si piden hablar con un humano, hacer handoff inmediato

REGLAS CUSTOM:
{company.ai_custom_rules}

CONTEXTO DEL CATALOGO (actualizado por busqueda):
{rag_context}

HISTORIAL DE CONVERSACION:
{conversation_history}

DATOS DEL LEAD:
{lead_context}
```

## Tools (Function Calling)

### buscar_producto
Busca en el catalogo por criterios flexibles.
```json
{
  "name": "buscar_producto",
  "description": "Busca productos o servicios que coincidan con los criterios del cliente",
  "input_schema": {
    "properties": {
      "query": {"type": "string", "description": "Busqueda texto libre (semantica)"},
      "category": {"type": "string"},
      "price_max": {"type": "number"},
      "specs_filter": {"type": "object", "description": "Filtros por specs (ej: {dormitorios_min: 2})"}
    }
  }
}
```

### consultar_precio
```json
{
  "name": "consultar_precio",
  "description": "Precio detallado de un producto con opciones y variantes",
  "input_schema": {
    "properties": {
      "product_id": {"type": "string"},
      "options": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["product_id"]
  }
}
```

### enviar_catalogo
```json
{
  "name": "enviar_catalogo",
  "description": "Envia fotos, documentos o videos de un producto al cliente",
  "input_schema": {
    "properties": {
      "product_id": {"type": "string"},
      "media_type": {"type": "string", "enum": ["photos", "document", "video", "all"]}
    },
    "required": ["product_id"]
  }
}
```

### agendar_cita
```json
{
  "name": "agendar_cita",
  "description": "Agenda cita, visita o reunion con el cliente",
  "input_schema": {
    "properties": {
      "type": {"type": "string", "description": "showroom, domicilio, virtual, sucursal, consulta"},
      "preferred_date": {"type": "string"},
      "preferred_time": {"type": "string"},
      "location": {"type": "string"},
      "notes": {"type": "string"}
    }
  }
}
```

### actualizar_lead
```json
{
  "name": "actualizar_lead",
  "description": "Actualiza datos del lead extraidos de la conversacion",
  "input_schema": {
    "properties": {
      "name": {"type": "string"},
      "email": {"type": "string"},
      "city": {"type": "string"},
      "budget_range": {"type": "string"},
      "timeline": {"type": "string", "enum": ["inmediato", "1_mes", "3_meses", "6_meses", "explorando"]},
      "needs_summary": {"type": "string"},
      "custom_fields": {"type": "object"}
    }
  }
}
```

### consultar_faq
```json
{
  "name": "consultar_faq",
  "description": "Busca en la knowledge base de la empresa (FAQs, politicas, info general)",
  "input_schema": {
    "properties": {"question": {"type": "string"}},
    "required": ["question"]
  }
}
```

### consultar_disponibilidad
```json
{
  "name": "consultar_disponibilidad",
  "description": "Verifica stock de producto o agenda disponible para citas",
  "input_schema": {
    "properties": {
      "product_id": {"type": "string"},
      "date": {"type": "string"},
      "check_type": {"type": "string", "enum": ["stock", "schedule"]}
    }
  }
}
```

### calcular_presupuesto
```json
{
  "name": "calcular_presupuesto",
  "description": "Genera cotizacion personalizada",
  "input_schema": {
    "properties": {
      "products": {
        "type": "array",
        "items": {"type": "object", "properties": {"product_id": {"type": "string"}, "quantity": {"type": "integer"}, "options": {"type": "array"}}}
      },
      "notes": {"type": "string"}
    },
    "required": ["products"]
  }
}
```

### escalar_a_humano
```json
{
  "name": "escalar_a_humano",
  "description": "Transfiere conversacion a vendedor humano",
  "input_schema": {
    "properties": {
      "reason": {"type": "string"},
      "urgency": {"type": "string", "enum": ["normal", "high"]}
    },
    "required": ["reason"]
  }
}
```

## Flujos de Conversacion

```
SALUDO INICIAL
  └─ Cliente dice "hola" / "info" / "quiero saber..."
     └─ IA saluda + pregunta que necesita

CONSULTA DE PRODUCTO
  └─ Cliente describe lo que busca
     └─ Tool: buscar_producto → muestra 2-3 opciones
        └─ Cliente elige → consultar_precio + enviar_catalogo
           └─ Sugerir cita/visita si hay interes

CONSULTA DE PRECIO
  └─ "Cuanto sale X?"
     └─ Calificar (que exactamente, cantidad, extras)
        └─ Tool: consultar_precio detallado
           └─ Tool: calcular_presupuesto si es complejo

AGENDAR CITA
  └─ Cliente acepta
     └─ Tool: consultar_disponibilidad
        └─ Tool: agendar_cita → confirma + follow-up 24h antes

OBJECIONES
  └─ "Es caro" → alternativas, financiacion
  └─ "No estoy seguro" → consultar_faq (garantias, testimonios)
  └─ "Necesito pensarlo" → respeta + programa follow-up

HANDOFF
  └─ Pide humano / queja / tecnico complejo
     └─ Tool: escalar_a_humano → pausa IA → notifica vendedor
```

## Lead Scoring

### Reglas Default (configurables por empresa)
```python
SCORING_RULES = {
    # Datos compartidos
    "dio_presupuesto": +15,
    "dio_email": +5,
    "dio_ubicacion": +10,
    "timeline_inmediato": +25,
    "timeline_1_mes": +20,
    "timeline_3_meses": +10,

    # Comportamiento
    "pidio_precios": +10,
    "pidio_fotos": +5,
    "pidio_presupuesto": +15,
    "acepto_cita": +30,
    "multiple_interacciones": +10,
    "respondio_followup": +10,

    # Negativas
    "dijo_solo_curiosidad": -15,
    "sin_respuesta_48h": -10,
    "precio_fuera_rango": -10,
    "cancelo_cita": -15,
}

# Prioridad:
# 0-25:  low    → respuesta IA normal
# 26-50: medium → seguimiento estandar
# 51-75: high   → seguimiento intensivo, notificar vendedor
# 76+:   urgent → alerta inmediata, contactar por telefono
```

## Modelos y Costos

| Uso | Modelo | Costo estimado |
|-----|--------|---------------|
| Conversacion normal | Claude Sonnet | ~$0.003/mensaje |
| Clasificacion/scoring | Claude Haiku | ~$0.0003/mensaje |
| Embeddings | voyage-3 o text-embedding-3-small | ~$0.0001/item |

Estimacion 5000 mensajes/mes: ~$15-25 USD
