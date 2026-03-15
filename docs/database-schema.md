# Schema de Base de Datos

## Diagrama de Relaciones

```
companies ─┬── house_models (catalogo generico: products)
            ├── leads ─┬── conversations ── messages
            │          ├── lead_stage_history
            │          ├── follow_ups
            │          └── visits
            ├── knowledge_items
            ├── follow_up_sequences
            ├── users
            └── daily_metrics
```

## Tablas

### companies (tenant principal)
```sql
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    business_type   VARCHAR(100),          -- "construccion", "restaurante", "clinica", etc.
    description     TEXT,                  -- descripcion del negocio (para system prompt)
    -- WhatsApp config
    whatsapp_phone  VARCHAR(20),
    waba_id         VARCHAR(50),           -- WhatsApp Business Account ID
    phone_number_id VARCHAR(50),           -- Meta phone number ID
    whatsapp_token  TEXT,                  -- Meta access token (encriptado)
    -- Instagram config
    ig_account_id   VARCHAR(50),
    ig_page_id      VARCHAR(50),
    ig_token        TEXT,                  -- (encriptado)
    -- AI config
    ai_personality  TEXT,                  -- "amigable y profesional", "formal", etc.
    ai_language     VARCHAR(50) DEFAULT 'es-UY', -- idioma del bot
    ai_sales_goal   TEXT,                  -- "guiar hacia una visita"
    ai_custom_rules TEXT,                  -- reglas adicionales
    ai_model        VARCHAR(50) DEFAULT 'claude-sonnet-4-20250514',
    -- Business config
    timezone        VARCHAR(50) DEFAULT 'America/Montevideo',
    business_hours  JSONB,                 -- {"mon": {"start": "08:00", "end": "18:00"}, ...}
    currency        VARCHAR(3) DEFAULT 'USD',
    -- Meta
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### products (catalogo generico — no solo casas)
```sql
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(100) NOT NULL,
    category        VARCHAR(100),          -- libre por empresa
    description     TEXT,
    short_desc      VARCHAR(500),          -- para respuestas rapidas en WhatsApp
    price           DECIMAL(12,2),
    price_currency  VARCHAR(3) DEFAULT 'USD',
    price_notes     TEXT,                  -- "No incluye envio", etc.
    unit            VARCHAR(50),           -- "unidad", "m2", "hora", "sesion"
    -- Specs flexibles (schema-less para cualquier dominio)
    specs           JSONB DEFAULT '{}',    -- {"dormitorios": 3, "area_m2": 80, "material": "pino"}
    features        JSONB DEFAULT '[]',    -- ["WiFi", "Estacionamiento", "Garantia 5 anios"]
    -- Media
    image_urls      JSONB DEFAULT '[]',
    video_url       TEXT,
    document_url    TEXT,                  -- brochure, ficha tecnica
    -- Estado
    is_active       BOOLEAN DEFAULT true,
    in_stock        BOOLEAN DEFAULT true,
    display_order   INT DEFAULT 0,
    -- Vector para busqueda semantica
    embedding       vector(1536),
    -- Meta
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(company_id, slug)
);

CREATE INDEX idx_products_company ON products(company_id) WHERE is_active = true;
CREATE INDEX idx_products_embedding ON products USING hnsw (embedding vector_cosine_ops);
```

### product_options (opcionales / variantes)
```sql
CREATE TABLE product_options (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID REFERENCES products(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    price           DECIMAL(10,2),
    description     TEXT,
    is_default      BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### leads (contactos / prospectos)
```sql
CREATE TABLE leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    -- Canal IDs
    whatsapp_id     VARCHAR(50),
    whatsapp_phone  VARCHAR(20),
    instagram_id    VARCHAR(50),
    instagram_username VARCHAR(100),
    -- Datos de contacto
    name            VARCHAR(200),
    email           VARCHAR(200),
    phone           VARCHAR(20),
    city            VARCHAR(100),
    region          VARCHAR(100),
    -- Scoring y pipeline
    score           INT DEFAULT 0,         -- 0-100
    stage           VARCHAR(30) DEFAULT 'new',
        -- new → interested → qualified → negotiating → visiting → closing → won | lost
    priority        VARCHAR(10) DEFAULT 'medium', -- low, medium, high, urgent
    -- Interes
    budget_range    VARCHAR(50),
    interested_products JSONB DEFAULT '[]', -- [product_id, ...]
    timeline        VARCHAR(50),           -- "inmediato", "1_mes", "3_meses", "explorando"
    needs_summary   TEXT,                  -- resumen IA de lo que busca
    -- Origen
    source_channel  VARCHAR(20),           -- "whatsapp", "instagram_dm", "instagram_comment", "web"
    source_campaign VARCHAR(100),
    source_url      TEXT,                  -- URL del post/ad de donde vino
    referred_by     UUID REFERENCES leads(id),
    -- Asignacion
    assigned_to     UUID,                  -- REFERENCES users(id)
    -- Estado
    tags            JSONB DEFAULT '[]',
    notes           TEXT,
    custom_fields   JSONB DEFAULT '{}',    -- campos libres por empresa
    last_message_at TIMESTAMPTZ,
    last_response_at TIMESTAMPTZ,
    -- Meta
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(company_id, whatsapp_id),
    UNIQUE(company_id, instagram_id)
);

CREATE INDEX idx_leads_company_stage ON leads(company_id, stage);
CREATE INDEX idx_leads_company_score ON leads(company_id, score DESC);
CREATE INDEX idx_leads_last_message ON leads(company_id, last_message_at DESC);
```

### lead_stage_history
```sql
CREATE TABLE lead_stage_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id     UUID REFERENCES leads(id) ON DELETE CASCADE,
    from_stage  VARCHAR(30),
    to_stage    VARCHAR(30) NOT NULL,
    changed_by  VARCHAR(50),             -- "ai", "user:{uuid}", "system", "follow_up"
    reason      TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

### conversations
```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID REFERENCES leads(id) ON DELETE CASCADE,
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    channel         VARCHAR(20) NOT NULL,   -- "whatsapp", "instagram_dm", "instagram_comment", "web"
    channel_conv_id VARCHAR(100),
    status          VARCHAR(20) DEFAULT 'active', -- active, paused, closed, handed_off
    handed_to       UUID,                   -- user_id si fue escalado
    ai_enabled      BOOLEAN DEFAULT true,
    summary         TEXT,                   -- resumen IA de la conversacion
    topic           VARCHAR(100),           -- topico detectado
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conversations_lead ON conversations(lead_id, created_at DESC);
CREATE INDEX idx_conversations_company ON conversations(company_id, status);
```

### messages
```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    -- Direccion
    direction       VARCHAR(10) NOT NULL,   -- "inbound", "outbound"
    sender_type     VARCHAR(10) NOT NULL,   -- "lead", "ai", "human"
    sender_id       VARCHAR(100),
    -- Contenido
    msg_type        VARCHAR(20) NOT NULL,   -- "text", "image", "audio", "video", "document", "location", "template", "interactive"
    content         TEXT,
    media_url       TEXT,
    media_mime      VARCHAR(50),
    -- Canal
    channel_msg_id  VARCHAR(100),           -- wamid o ig message id
    channel_status  VARCHAR(20),            -- "sent", "delivered", "read", "failed"
    -- IA metadata
    ai_model        VARCHAR(50),
    ai_tokens_in    INT,
    ai_tokens_out   INT,
    ai_cost_usd     DECIMAL(8,6),
    ai_tools_used   JSONB,                  -- ["buscar_producto", "consultar_precio"]
    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT now(),
    channel_ts      TIMESTAMPTZ
);

CREATE INDEX idx_messages_conv ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_channel ON messages(channel_msg_id);
```

### knowledge_items (knowledge base per company)
```sql
CREATE TABLE knowledge_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    -- Fuente
    source          VARCHAR(20) NOT NULL,   -- "catalog", "document", "instagram", "website", "faq", "conversation", "manual"
    source_url      TEXT,                   -- URL original (post IG, pagina web, etc.)
    source_id       VARCHAR(100),           -- ID externo (post ID, etc.)
    -- Contenido
    title           VARCHAR(500),
    content         TEXT NOT NULL,
    media_urls      JSONB DEFAULT '[]',
    -- Vector
    embedding       vector(1536),
    -- Estado
    is_active       BOOLEAN DEFAULT true,
    auto_generated  BOOLEAN DEFAULT false,  -- generado de conversaciones vs manual
    -- Meta
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_kb_company ON knowledge_items(company_id) WHERE is_active = true;
CREATE INDEX idx_kb_embedding ON knowledge_items USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_kb_source ON knowledge_items(company_id, source);
```

### follow_ups
```sql
CREATE TABLE follow_ups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID REFERENCES leads(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    -- Config
    type            VARCHAR(30) NOT NULL,   -- "reminder", "offer", "check_in", "visit_confirm", "reactivation"
    template_name   VARCHAR(100),           -- nombre del template WhatsApp
    template_params JSONB,
    message_text    TEXT,
    -- Schedule
    scheduled_at    TIMESTAMPTZ NOT NULL,
    executed_at     TIMESTAMPTZ,
    status          VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed, cancelled, skipped
    skip_reason     TEXT,
    -- Secuencia
    sequence_id     UUID,
    sequence_step   INT,
    max_attempts    INT DEFAULT 3,
    attempt         INT DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_followups_pending ON follow_ups(scheduled_at) WHERE status = 'pending';
```

### follow_up_sequences
```sql
CREATE TABLE follow_up_sequences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    trigger_stage   VARCHAR(30),            -- en que etapa del lead se activa
    steps           JSONB NOT NULL,         -- [{"delay_hours": 2, "type": "reminder", "template": "..."}, ...]
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### visits
```sql
CREATE TABLE visits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID REFERENCES leads(id) ON DELETE CASCADE,
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    assigned_to     UUID,                   -- vendedor
    visit_type      VARCHAR(30),            -- "showroom", "domicilio", "virtual", "sucursal"
    scheduled_date  DATE,
    scheduled_time  TIME,
    duration_min    INT DEFAULT 60,
    location        TEXT,
    location_lat    DECIMAL(10,7),
    location_lng    DECIMAL(10,7),
    status          VARCHAR(20) DEFAULT 'scheduled', -- scheduled, confirmed, completed, no_show, cancelled
    notes           TEXT,
    feedback        TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### users (equipo de ventas + admin)
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    email           VARCHAR(200) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    role            VARCHAR(20) DEFAULT 'seller', -- super_admin, admin, manager, seller
    password_hash   TEXT NOT NULL,
    phone           VARCHAR(20),
    whatsapp_phone  VARCHAR(20),            -- para recibir alertas por WhatsApp
    is_active       BOOLEAN DEFAULT true,
    notification_prefs JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(company_id, email)
);
```

### daily_metrics (analytics desnormalizados)
```sql
CREATE TABLE daily_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    metric_date     DATE NOT NULL,
    channel         VARCHAR(20),
    -- Volumenes
    messages_in     INT DEFAULT 0,
    messages_out    INT DEFAULT 0,
    new_leads       INT DEFAULT 0,
    conversations_started INT DEFAULT 0,
    -- Performance
    avg_response_sec INT,
    ai_handled_pct  DECIMAL(5,2),
    handoff_count   INT DEFAULT 0,
    -- Conversion
    leads_qualified INT DEFAULT 0,
    visits_scheduled INT DEFAULT 0,
    visits_completed INT DEFAULT 0,
    deals_won       INT DEFAULT 0,
    revenue         DECIMAL(12,2) DEFAULT 0,
    -- Costos
    ai_cost_usd     DECIMAL(8,4) DEFAULT 0,
    meta_cost_usd   DECIMAL(8,4) DEFAULT 0,
    -- Productos populares
    top_products    JSONB,
    UNIQUE(company_id, metric_date, channel)
);
```
