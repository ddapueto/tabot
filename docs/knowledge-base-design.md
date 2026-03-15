# Diseno del Knowledge Base

## Concepto
Cada empresa tiene su propia base de conocimiento. El agente IA usa esta base
para responder con informacion real y actualizada del negocio.

La clave: el KB se **auto-alimenta** desde multiples fuentes,
requiriendo minimo esfuerzo del empresario.

## Fuentes de Conocimiento

### 1. Catalogo de Productos (automatico)
- **Trigger**: Crear/actualizar producto
- **Proceso**: Texto descriptivo del producto → embedding
- **Ejemplo**: "Cabana Pino Premium: 80m2, 3 dormitorios, 2 banos..."

### 2. Instagram Posts (automatico)
- **Trigger**: Webhook cuando empresa publica
- **Proceso**: Caption + hashtags → embedding
- **Impacto**: Lead pregunta por ofertas → bot sabe del post

### 3. Instagram Ads/Stories (semi-automatico)
- **Trigger**: Webhook o ingestion manual
- **Proceso**: Texto ad + CTA → embedding
- **Impacto**: Lead llega por ad → bot continua la conversacion

### 4. Documentos (manual)
- **Trigger**: Upload desde dashboard
- **Proceso**: Parse PDF/TXT → chunk → embedding por chunk
- **Ejemplo**: Politicas de garantia, manuales, procesos

### 5. Website (semi-automatico)
- **Trigger**: Ingestion manual (URL) o scrape programado
- **Proceso**: Scrape → texto limpio → chunk → embedding

### 6. FAQ (manual + auto-generado)
- **Manual**: Admin agrega Q&A desde dashboard
- **Auto**: Sistema detecta preguntas frecuentes en conversaciones → sugiere al admin

### 7. Conversaciones (automatico)
- **Trigger**: Analisis periodico (cron semanal)
- **Proceso**: IA extrae preguntas frecuentes → crea FAQ entries
- **Validacion**: `auto_generated=true`, admin revisa/edita

## Pipeline de Ingestion

```
Fuente → Parse → Chunk (si >1000 tokens) → Embed → Store en pgvector
                                              |
                                              v
                                    Embedding API
                                    (voyage-3 o text-embedding-3-small)
```

## Busqueda Semantica (RAG)

```python
async def search_knowledge(company_id, query, top_k=5):
    query_embedding = await embed_text(query)
    results = await db.execute(
        select(KnowledgeItem)
        .where(KnowledgeItem.company_id == company_id)
        .where(KnowledgeItem.is_active == True)
        .order_by(KnowledgeItem.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return results.scalars().all()
```

## Flujo Instagram → KB → Respuesta

```
1. Empresa publica en Instagram:
   "Nueva cabana Tiny House! 35m2, precio especial $25,000"

2. Meta webhook → Tabot captura → KnowledgeItem:
   source: "instagram"
   content: "Nueva cabana Tiny House! 35m2..."
   media_urls: ["foto1.jpg", "foto2.jpg"]

3. Se genera embedding → se guarda en KB

4. Lead escribe por WhatsApp:
   "Vi en Instagram que tienen una cabana nueva, cuanto sale?"

5. Agente busca en KB → encuentra post IG
   → responde con info real + fotos
```

## Metricas del KB

| Metrica | Que mide |
|---------|----------|
| Items por fuente | Balance de contenido |
| Items sin match | Contenido que nunca se usa |
| Preguntas sin respuesta | Gaps en el KB |
| Hit rate por fuente | Fuentes mas utiles |
| Freshness | Antiguedad del contenido |
