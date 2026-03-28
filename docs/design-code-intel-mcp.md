# Diseno Completo: Code Intelligence MCP Server

> Servidor MCP unificado que combina extraccion de simbolos + grafos de dependencias + salud del codigo + seleccion inteligente de contexto.
> Documento de research + arquitectura. SIN codigo aun.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura](#arquitectura)
3. [Tools MCP a Exponer](#tools-mcp-a-exponer)
4. [Plan de Implementacion](#plan-de-implementacion)
5. [Flujos de Uso Diario](#flujos-de-uso-diario)
6. [Comparacion con Alternativas](#comparacion-con-alternativas)
7. [Fuentes de Investigacion](#fuentes-de-investigacion)

---

## Resumen Ejecutivo

### Que es

Un servidor MCP (Model Context Protocol) escrito en Python que se conecta a Claude Code via stdio y le da **vision estructural** del codebase. En vez de que Claude haga 15 llamadas a Grep/Glob para entender como funciona auth, hace UNA llamada a `get_symbols` o `find_references` y obtiene exactamente lo que necesita.

### Por que construirlo

Claude Code hoy tiene Grep (busqueda textual) y Glob (busqueda por nombre de archivo). Esto es como buscar en un libro escaneando pagina por pagina. Un servidor de code intelligence es como tener el **indice, el glosario, y las referencias cruzadas** del libro listos para consultar.

### El stack

- **Parser**: tree-sitter (via `tree-sitter` + `tree-sitter-python` + `tree-sitter-typescript`)
- **Grafo**: NetworkX (para PageRank sobre referencias)
- **MCP SDK**: `mcp[cli]` (FastMCP oficial, decorador `@mcp.tool()`)
- **Transporte**: stdio (el estandar para Claude Code)
- **Cache**: En memoria con invalidacion por mtime de archivos

---

## Arquitectura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code                          │
│                                                         │
│  "quiero entender como funciona auth"                   │
│       │                                                 │
│       ▼                                                 │
│  Llama tool MCP: get_smart_context(query="auth flow")   │
└───────┬─────────────────────────────────────────────────┘
        │ stdio (JSON-RPC)
        ▼
┌─────────────────────────────────────────────────────────┐
│              Code Intelligence MCP Server               │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Indexer     │  │  Analyzer    │  │  Ranker      │  │
│  │              │  │              │  │              │  │
│  │ tree-sitter  │  │ complexity   │  │ PageRank     │  │
│  │ parser       │  │ metrics      │  │ (NetworkX)   │  │
│  │              │  │ dep graph    │  │              │  │
│  │ symbols      │  │ imports      │  │ smart ctx    │  │
│  │ cache        │  │ references   │  │ selection    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └────────────┬────┘                 │           │
│                      ▼                      │           │
│              ┌──────────────┐               │           │
│              │  SymbolStore  │◄──────────────┘           │
│              │              │                           │
│              │  - symbols[] │  (en memoria, por sesion) │
│              │  - refs[]    │                           │
│              │  - graph     │                           │
│              │  - mtime{}   │                           │
│              └──────────────┘                           │
│                      ▲                                  │
│                      │ lee archivos                     │
│                      ▼                                  │
│              ┌──────────────┐                           │
│              │  Filesystem   │                           │
│              │  (cwd o path) │                           │
│              └──────────────┘                           │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
1. Claude Code inicia el server MCP (stdio)
2. El server NO indexa nada al arrancar (lazy)
3. Claude llama una tool (ej: get_symbols)
4. El server:
   a. Verifica cache (mtime de archivos)
   b. Si cache miss: parsea con tree-sitter
   c. Extrae simbolos (funciones, clases, imports)
   d. Construye/actualiza el grafo de referencias
   e. Retorna resultado formateado
5. Para smart_context:
   a. Construye grafo completo si no existe
   b. Ejecuta PageRank con personalizacion
   c. Selecciona top-N simbolos/archivos
   d. Retorna mapa de contexto optimizado
```

### Integracion con Claude Code

El server se registra en `.mcp.json` del proyecto:

```json
{
  "mcpServers": {
    "code-intel": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/code-intel-mcp", "python", "-m", "code_intel_mcp"],
      "env": {
        "CODE_INTEL_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

Alternativa mas simple (si se instala globalmente):

```json
{
  "mcpServers": {
    "code-intel": {
      "type": "stdio",
      "command": "code-intel-mcp",
      "args": ["--root", "."]
    }
  }
}
```

---

## Tools MCP a Exponer

### Tool 1: `index_project`

**Proposito**: Indexar (o re-indexar) el proyecto completo. Construye el store de simbolos y el grafo de dependencias.

```python
@mcp.tool()
async def index_project(
    root_path: str = ".",
    languages: list[str] | None = None,
    exclude_patterns: list[str] | None = None
) -> str:
    """Indexa el proyecto completo: parsea archivos con tree-sitter,
    extrae simbolos (funciones, clases, imports), y construye el grafo
    de dependencias. Ejecutar esto primero para habilitar las demas tools.

    Args:
        root_path: Directorio raiz del proyecto (default: directorio actual)
        languages: Lenguajes a indexar (default: auto-detect). Opciones: python, typescript, javascript
        exclude_patterns: Patrones glob a excluir (default: node_modules, .venv, __pycache__, .git)
    """
```

**Retorno ejemplo**:
```
Proyecto indexado exitosamente:
- Archivos parseados: 81 (55 Python, 16 TypeScript, 10 Svelte)
- Simbolos extraidos: 487 (312 funciones, 89 clases, 86 imports)
- Grafo de dependencias: 81 nodos, 234 aristas
- Tiempo: 1.2s
- Archivos ignorados: 3712 (node_modules, .venv)
```

---

### Tool 2: `get_symbols`

**Proposito**: Listar todos los simbolos (funciones, clases, metodos, variables de modulo) de un archivo o directorio.

```python
@mcp.tool()
async def get_symbols(
    path: str,
    kind: str | None = None,
    recursive: bool = False
) -> str:
    """Extrae los simbolos definidos en un archivo o directorio.
    Usa tree-sitter para parseo preciso (no regex).

    Args:
        path: Archivo o directorio a analizar
        kind: Filtrar por tipo: "function", "class", "method", "import", "variable" (default: todos)
        recursive: Si path es directorio, incluir subdirectorios (default: false)
    """
```

**Retorno ejemplo** (para `backend/app/services/ai_agent.py`):
```
## backend/app/services/ai_agent.py (247 lineas)

### Imports (8)
- fastapi (line 1)
- sqlalchemy.ext.asyncio.AsyncSession (line 2)
- app.models.company.Company (line 4)
- app.services.kb_manager.KBManager (line 5)
- app.services.ai_tools.TOOLS_OPENAI, execute_tool (line 6)
- groq.AsyncGroq (line 8)
- anthropic.AsyncAnthropic (line 9)
- app.config.settings (line 10)

### Clases (1)
- AIAgent (line 15-247)
  - __init__(self, db: AsyncSession, company: Company) (line 16)
  - _build_system_prompt(self) -> str (line 34)
  - _get_rag_context(self, query: str) -> str (line 78)
  - generate_response(self, message: str, history: list) -> str (line 112)
  - _call_groq(self, messages: list) -> str (line 156)
  - _call_anthropic(self, messages: list) -> str (line 189)
  - _handle_tool_calls(self, tool_calls: list) -> list (line 218)
```

---

### Tool 3: `find_references`

**Proposito**: Encontrar todas las referencias a un simbolo en el codebase (quien llama a esta funcion, quien usa esta clase).

```python
@mcp.tool()
async def find_references(
    symbol_name: str,
    kind: str | None = None,
    scope: str | None = None
) -> str:
    """Encuentra todas las referencias a un simbolo en el codebase.
    Mas preciso que grep porque entiende la estructura del codigo.

    Args:
        symbol_name: Nombre del simbolo a buscar (ej: "generate_response", "AIAgent", "KBManager")
        kind: Filtrar por tipo de referencia: "call", "import", "instantiation", "inheritance" (default: todos)
        scope: Limitar busqueda a un directorio (ej: "backend/app/api")
    """
```

**Retorno ejemplo** (para `find_references("KBManager")`):
```
## Referencias a "KBManager" (7 encontradas)

### Imports (4)
- backend/app/services/ai_agent.py:5 — from app.services.kb_manager import KBManager
- backend/app/api/settings_api.py:12 — from app.services.kb_manager import KBManager
- backend/app/tasks/kb_maintenance.py:8 — from app.services.kb_manager import KBManager
- backend/app/api/onboarding.py:15 — from app.services.kb_manager import KBManager

### Instanciaciones (3)
- backend/app/services/ai_agent.py:82 — kb = KBManager(self.db, self.company)
- backend/app/api/settings_api.py:45 — manager = KBManager(db, company)
- backend/app/api/onboarding.py:67 — kb = KBManager(db, new_company)

### Grafo de dependencias:
  kb_manager.py ← ai_agent.py ← message_handler.py ← webhooks/whatsapp.py
                ← settings_api.py
                ← kb_maintenance.py (task)
                ← onboarding.py
```

---

### Tool 4: `get_dependencies`

**Proposito**: Mostrar el arbol de dependencias de un archivo (que importa, y que lo importa a el).

```python
@mcp.tool()
async def get_dependencies(
    path: str,
    direction: str = "both",
    depth: int = 2
) -> str:
    """Muestra el arbol de dependencias de un archivo: sus imports (upstream)
    y quien lo importa (downstream).

    Args:
        path: Archivo a analizar
        direction: "imports" (que usa), "importers" (quien lo usa), "both" (default)
        depth: Profundidad del arbol (default: 2, max: 5)
    """
```

**Retorno ejemplo** (para `backend/app/services/message_handler.py`):
```
## Dependencias de message_handler.py

### Imports (upstream) — que usa este archivo:
message_handler.py
├── ai_agent.py
│   ├── kb_manager.py
│   │   └── models/knowledge.py
│   ├── ai_tools.py
│   └── config.py
├── whatsapp_client.py
│   └── config.py
├── lead_scorer.py
│   └── models/lead.py
├── response_validator.py
│   └── models/product.py
└── models/conversation.py

### Importers (downstream) — quien usa este archivo:
message_handler.py
├── api/webhooks/whatsapp.py
└── api/webhooks/instagram.py

### Estadisticas:
- Upstream: 12 archivos (profundidad max: 3)
- Downstream: 2 archivos
- Acoplamiento: ALTO (12 dependencias directas)
```

---

### Tool 5: `get_smart_context`

**Proposito**: EL TOOL ESTRELLA. Dado un query o tarea, selecciona automaticamente los archivos y simbolos mas relevantes usando PageRank sobre el grafo de referencias.

```python
@mcp.tool()
async def get_smart_context(
    query: str,
    focus_files: list[str] | None = None,
    max_tokens: int = 4000,
    include_signatures: bool = True
) -> str:
    """Seleccion inteligente de contexto. Dado un query o descripcion de tarea,
    identifica los archivos y simbolos mas relevantes del codebase usando
    PageRank sobre el grafo de dependencias. Retorna un mapa compacto y
    optimizado para el token budget.

    Usa esto ANTES de empezar cualquier tarea para entender que archivos
    y funciones estan involucrados.

    Args:
        query: Descripcion de lo que quieres hacer o entender (ej: "como funciona la autenticacion")
        focus_files: Archivos que ya sabes que son relevantes (mejora la precision del ranking)
        max_tokens: Presupuesto maximo de tokens para el contexto (default: 4000)
        include_signatures: Incluir firmas de funciones/clases (default: true)
    """
```

**Retorno ejemplo** (para `get_smart_context("como funciona la autenticacion JWT")`):
```
## Contexto Inteligente: "autenticacion JWT"

### Archivos Relevantes (ranked por PageRank):

#### 1. backend/app/api/auth.py (score: 0.142) ★ CORE
  - register(data: UserCreate, db: AsyncSession) -> UserResponse
  - login(data: LoginRequest, db: AsyncSession) -> TokenResponse
  - refresh_token(token: str, db: AsyncSession) -> TokenResponse
  - get_me(company_id: int = Depends(get_current_company_id)) -> UserResponse

#### 2. backend/app/api/deps.py (score: 0.118) ★ CORE
  - get_current_company_id(token: str = Depends(oauth2_scheme)) -> int
  - require_admin(company_id: int = Depends(get_current_company_id)) -> int
  Importado por: 11 archivos (todos los routers de API)

#### 3. backend/app/models/user.py (score: 0.089)
  - class User(Base):
      id, email, hashed_password, company_id, role, is_active

#### 4. backend/app/config.py (score: 0.067)
  - SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

#### 5. backend/app/schemas/lead.py (score: 0.034)
  - class UserCreate, LoginRequest, TokenResponse

### Archivos Secundarios (contexto util):
- backend/app/api/webhooks/whatsapp.py — usa HMAC, no JWT
- backend/app/api/conversations.py — SSE con company_id en URL (sin JWT)

### Flujo detectado:
  login() → JWT(company_id) → get_current_company_id() → every API endpoint

### Tokens usados: 1,847 / 4,000
```

---

### Tool 6: `analyze_health`

**Proposito**: Metricas de salud del codigo: complejidad, longitud de funciones, archivos acoplados, code smells.

```python
@mcp.tool()
async def analyze_health(
    path: str = ".",
    metric: str | None = None
) -> str:
    """Analiza la salud del codigo: complejidad ciclomatica, longitud de funciones,
    acoplamiento entre modulos, y detecta code smells comunes.

    Args:
        path: Archivo o directorio a analizar (default: proyecto completo)
        metric: Metrica especifica: "complexity", "coupling", "size", "all" (default: "all")
    """
```

**Retorno ejemplo** (para `analyze_health("backend/app/services")`):
```
## Salud del Codigo: backend/app/services/

### Resumen General
| Metrica              | Valor  | Status |
|----------------------|--------|--------|
| Archivos             | 9      | -      |
| Total lineas         | 1,247  | OK     |
| Complejidad promedio | 4.2    | OK     |
| Funcion mas larga    | 67 ln  | WARN   |
| Acoplamiento max     | 12     | WARN   |

### Complejidad por Archivo (McCabe)
| Archivo               | CC Promedio | CC Max | Funcion mas compleja        |
|-----------------------|-------------|--------|-----------------------------|
| ai_agent.py           | 6.3         | 12     | generate_response (12)      |
| message_handler.py    | 5.8         | 9      | handle_incoming_message (9) |
| response_validator.py | 4.5         | 7      | validate_prices (7)         |
| kb_manager.py         | 3.2         | 5      | sync_from_catalog (5)       |
| lead_scorer.py        | 2.8         | 4      | calculate_score (4)         |
| ai_tools.py           | 2.1         | 3      | execute_tool (3)            |
| whatsapp_client.py    | 1.9         | 3      | send_message (3)            |
| instagram_client.py   | 1.7         | 2      | send_dm (2)                 |
| follow_up_engine.py   | 1.5         | 2      | execute_pending (2)         |

### Code Smells Detectados
- ⚠ ai_agent.py:generate_response — 67 lineas (max recomendado: 50)
- ⚠ message_handler.py — 12 imports directos (alto acoplamiento)
- ⚠ ai_agent.py — CC=12 en generate_response (considerar extraer metodos)

### Recomendaciones
1. Extraer _handle_groq_response() y _handle_anthropic_response() de generate_response()
2. message_handler.py: considerar un patron mediador para reducir acoplamiento
```

---

### Tool 7: `find_api_endpoints`

**Proposito**: Encontrar todos los endpoints API definidos en el proyecto (FastAPI routes, Express routes, etc.).

```python
@mcp.tool()
async def find_api_endpoints(
    path: str = ".",
    method: str | None = None
) -> str:
    """Encuentra todos los endpoints HTTP/API definidos en el proyecto.
    Detecta decoradores de FastAPI (@router.get, @app.post, etc.),
    Express (app.get, router.post), y SvelteKit (+server.ts).

    Args:
        path: Directorio a buscar (default: proyecto completo)
        method: Filtrar por metodo HTTP: "GET", "POST", "PUT", "DELETE" (default: todos)
    """
```

**Retorno ejemplo**:
```
## API Endpoints (42 encontrados)

### backend/app/api/auth.py (4 endpoints)
  POST   /auth/register          → register()
  POST   /auth/login             → login()
  POST   /auth/refresh           → refresh_token()
  GET    /auth/me                → get_me()

### backend/app/api/leads.py (6 endpoints)
  GET    /leads/                 → list_leads()
  GET    /leads/{lead_id}        → get_lead()
  POST   /leads/                 → create_lead()
  PUT    /leads/{lead_id}        → update_lead()
  PUT    /leads/{lead_id}/stage  → update_stage()
  POST   /leads/{lead_id}/handoff → handoff_to_human()

### backend/app/api/conversations.py (4 endpoints)
  GET    /conversations/         → list_conversations()
  GET    /conversations/{id}/messages → get_messages()
  POST   /conversations/{id}/send    → send_message()
  GET    /conversations/stream/{company_id} → sse_stream()

### backend/app/api/catalog.py (4 endpoints)
  GET    /catalog/               → list_products()
  POST   /catalog/               → create_product()
  PUT    /catalog/{id}           → update_product()
  DELETE /catalog/{id}           → delete_product()

[... mas endpoints ...]

### Resumen por Metodo
  GET: 18 | POST: 14 | PUT: 6 | DELETE: 4

### Endpoints sin Auth (verificar seguridad)
  POST /webhooks/whatsapp  — usa HMAC
  POST /webhooks/instagram — usa HMAC
  GET  /health             — publico (intencionado)
  GET  /conversations/stream/{company_id} — SSE, company_id en URL
```

---

### Tool 8: `search_by_pattern`

**Proposito**: Busqueda semantica por patrones de codigo (no texto). Ejemplo: "funciones async que reciben db: AsyncSession", "clases que heredan de Base".

```python
@mcp.tool()
async def search_by_pattern(
    pattern: str,
    language: str | None = None,
    scope: str | None = None
) -> str:
    """Busca patrones estructurales en el codigo usando tree-sitter queries.
    A diferencia de grep, esto entiende la estructura del AST.

    Patrones soportados (lenguaje natural que se convierte a tree-sitter query):
    - "funciones async" → async function_definition
    - "clases que heredan de X" → class con base class
    - "funciones con decorador @router.get" → decorated functions
    - "try/except sin manejo especifico" → bare except
    - "funciones con mas de 3 parametros" → function con 4+ params

    Args:
        pattern: Descripcion del patron a buscar (lenguaje natural)
        language: Lenguaje objetivo (default: auto-detect)
        scope: Directorio donde buscar (default: proyecto completo)
    """
```

**Retorno ejemplo** (para `search_by_pattern("funciones async que reciben db: AsyncSession")`):
```
## Patron: funciones async con parametro db: AsyncSession (23 encontradas)

### backend/app/api/auth.py
  - async def register(data: UserCreate, db: AsyncSession = Depends(get_db))  [line 24]
  - async def login(data: LoginRequest, db: AsyncSession = Depends(get_db))   [line 45]

### backend/app/api/leads.py
  - async def list_leads(db: AsyncSession = Depends(get_db), ...)              [line 18]
  - async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db))       [line 35]
  [... 4 mas ...]

### backend/app/services/ai_agent.py
  - async def generate_response(self, ...) — usa self.db (AsyncSession)        [line 112]

[... etc ...]
```

---

## Plan de Implementacion

### Paquetes a Instalar

```toml
# pyproject.toml
[project]
name = "code-intel-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.2.0",           # SDK MCP oficial (incluye FastMCP)
    "tree-sitter>=0.23.0",        # Parser core
    "tree-sitter-python>=0.23.0", # Gramatica Python
    "tree-sitter-typescript>=0.23.0", # Gramatica TypeScript
    "tree-sitter-javascript>=0.23.0", # Gramatica JavaScript
    "networkx>=3.2",              # PageRank y grafos
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

# Punto de entrada CLI
[project.scripts]
code-intel-mcp = "code_intel_mcp.__main__:main"
```

**Nota sobre gramaticas tree-sitter**: Los paquetes `tree-sitter-python`, `tree-sitter-typescript`, etc. vienen con la gramatica pre-compilada como binary wheel. No hay que compilar nada manualmente. Son ~2MB cada uno.

### Estructura de Archivos

```
code-intel-mcp/
├── pyproject.toml
├── README.md
├── src/
│   └── code_intel_mcp/
│       ├── __init__.py
│       ├── __main__.py              # Entry point: inicializa FastMCP y corre
│       ├── server.py                # FastMCP server + tool definitions
│       ├── indexer.py               # Parseo tree-sitter, extraccion de simbolos
│       ├── symbol_store.py          # Store en memoria: simbolos, refs, cache
│       ├── graph.py                 # Construccion del grafo NetworkX + PageRank
│       ├── health.py                # Metricas de complejidad y code smells
│       ├── queries/                 # Tree-sitter queries por lenguaje
│       │   ├── python_tags.scm      # Queries para Python
│       │   ├── typescript_tags.scm  # Queries para TypeScript
│       │   └── javascript_tags.scm  # Queries para JavaScript
│       └── utils.py                 # Helpers: file discovery, language detection
└── tests/
    ├── test_indexer.py
    ├── test_graph.py
    ├── test_health.py
    ├── test_server.py               # Tests de integracion MCP
    └── fixtures/                    # Archivos de prueba
        ├── sample_python.py
        └── sample_typescript.ts
```

### Como Construirlo Paso a Paso

#### Fase 1: Servidor MCP minimo + indexacion basica (1-2 dias)

1. Crear el proyecto con `uv init code-intel-mcp`
2. Implementar `server.py` con FastMCP:
   ```python
   from mcp.server.fastmcp import FastMCP
   mcp = FastMCP("code-intel")
   ```
3. Implementar `indexer.py`:
   - Funcion `parse_file(path) -> list[Symbol]`
   - Usa `tree-sitter` con query para extraer function_definition, class_definition, import_statement
   - Retorna lista de `Symbol(name, kind, line, end_line, signature, file_path)`
4. Implementar `symbol_store.py`:
   - Dict de `{file_path: [Symbol, ...]}` con mtime para invalidacion
   - Metodos: `index_file()`, `index_directory()`, `get_symbols()`, `is_stale()`
5. Exponer tools: `index_project`, `get_symbols`
6. Probar: `echo '{"method":"tools/list"}' | uv run code-intel-mcp`

#### Fase 2: Referencias y grafo de dependencias (1-2 dias)

1. Extender `indexer.py` para capturar **referencias** (no solo definiciones):
   - Identifier nodes que no son parte de una definicion = referencia
   - Import statements = referencia a modulo externo
2. Implementar `graph.py`:
   - Construir `nx.MultiDiGraph` donde nodos = archivos, aristas = "archivo A referencia simbolo definido en archivo B"
   - Weight = numero de referencias entre A y B
3. Exponer tools: `find_references`, `get_dependencies`

#### Fase 3: Smart context con PageRank (1 dia)

1. Implementar ranking en `graph.py`:
   - Personalizacion: archivos mencionados en `focus_files` reciben peso 100x
   - Match de keywords del query contra nombres de simbolos para boost adicional
   - `nx.pagerank(graph, personalization=weights)`
2. Post-procesamiento:
   - Ordenar simbolos por score
   - Incluir firmas hasta llenar `max_tokens`
   - Formato de salida compacto y legible
3. Exponer tool: `get_smart_context`

#### Fase 4: Salud del codigo y endpoints (1 dia)

1. Implementar `health.py`:
   - Complejidad ciclomatica: contar `if`, `elif`, `for`, `while`, `except`, `and`, `or` en el AST
   - Longitud de funciones: `end_line - start_line`
   - Acoplamiento: contar imports unicos por archivo
2. Deteccion de API endpoints:
   - Python/FastAPI: buscar decoradores `@router.get/post/put/delete/patch`
   - TypeScript/Express: buscar `app.get()`, `router.post()`
   - SvelteKit: buscar `+server.ts` con export GET/POST
3. Exponer tools: `analyze_health`, `find_api_endpoints`

#### Fase 5: Busqueda por patrones + polish (1 dia)

1. Implementar `search_by_pattern`:
   - Mapeo de patrones comunes en lenguaje natural a tree-sitter queries
   - Catalog de ~20 patrones pre-definidos
   - Fallback a busqueda textual si no matchea ningun patron
2. Optimizacion de performance:
   - Cache agresivo con invalidacion por mtime
   - Indexacion incremental (solo archivos modificados)
3. Manejo de errores robusto (archivos binarios, encoding, etc.)

**Tiempo total estimado: 5-7 dias**

### Como Testearlo

```bash
# 1. Tests unitarios
cd code-intel-mcp
uv run pytest tests/ -v

# 2. Test manual del server MCP
uv run code-intel-mcp --root /path/to/tabot

# 3. Registrar en proyecto y probar con Claude Code
# Agregar a .mcp.json del proyecto target
# Reiniciar Claude Code
# Usar: "lista los simbolos de backend/app/services/ai_agent.py"

# 4. Test de integracion con mcp CLI
mcp dev src/code_intel_mcp/server.py
```

---

## Flujos de Uso Diario

### Escenario 1: "Quiero entender como funciona auth"

**Sin Code Intelligence (hoy):**
```
Claude: Voy a buscar archivos relacionados con auth...
→ Glob("**/auth*") → 3 archivos
→ Read(auth.py) → 200 lineas
→ Grep("get_current_company_id") → 14 resultados
→ Read(deps.py) → 80 lineas
→ Grep("JWT") → 8 resultados
→ Read(config.py) → buscando SECRET_KEY
→ Read(user.py) → modelo de usuario
Total: 7+ tool calls, ~800 tokens de overhead por call
```

**Con Code Intelligence:**
```
Claude: Voy a obtener el contexto inteligente para auth...
→ get_smart_context(query="autenticacion JWT", max_tokens=4000)
  ← Retorna: auth.py (firmas), deps.py (firmas), user.py (modelo),
     config.py (JWT settings), flujo detectado, archivos secundarios
Total: 1 tool call, respuesta completa y organizada
```

**Ahorro: 6 tool calls menos, contexto mejor organizado, Claude entiende la estructura antes de tocar codigo.**

### Escenario 2: "Quiero refactorizar el KB Manager"

```
Desarrollador: "Necesito refactorizar kb_manager.py, esta muy acoplado"

Claude:
→ get_smart_context(query="kb_manager refactoring", focus_files=["backend/app/services/kb_manager.py"])
  ← Ve: 4 archivos lo importan, 3 lo instancian, grafo de dependencias completo

→ analyze_health(path="backend/app/services/kb_manager.py")
  ← Ve: CC promedio 3.2, funcion mas larga 45 lineas, 5 imports

→ find_references(symbol_name="KBManager")
  ← Ve exactamente DONDE se usa, con que metodos, en que contexto

→ get_dependencies(path="backend/app/services/kb_manager.py")
  ← Ve arbol upstream (que usa) y downstream (quien lo usa)

Claude ahora sabe EXACTAMENTE:
- Que archivos tocar
- Que metodos son publicos vs privados en la practica
- El impacto del refactoring (que puede romper)
- Sugerencias basadas en metricas de salud
```

### Escenario 3: "Quiero encontrar todos los API endpoints"

```
Desarrollador: "Lista todos los endpoints de la API con sus metodos"

Claude:
→ find_api_endpoints()
  ← Lista completa: 42 endpoints, agrupados por router, con metodo HTTP,
     path, funcion handler, y flags de seguridad (auth/no-auth)

Sin code-intel tendria que:
→ Glob("**/api/**/*.py") → 13 archivos
→ Read cada uno buscando decoradores @router
→ 13 tool calls minimo + parsing mental
```

### Escenario 4: "Hay algun code smell que deberia arreglar?"

```
Desarrollador: "Analiza la calidad del codigo del backend"

Claude:
→ analyze_health(path="backend/app")
  ← Tabla de complejidad por archivo, funciones largas, acoplamiento alto,
     recomendaciones concretas

→ search_by_pattern("try/except sin manejo especifico")
  ← Bare excepts encontrados

→ search_by_pattern("funciones con mas de 5 parametros")
  ← Funciones con demasiados parametros (candidatas a refactoring)
```

---

## Comparacion con Alternativas

### vs Grep/Glob Nativos de Claude Code

| Aspecto | Grep/Glob | Code Intelligence MCP |
|---------|-----------|----------------------|
| Busqueda | Textual (regex) | Estructural (AST) |
| Contexto | Lineas individuales | Simbolos completos con firmas |
| Dependencias | No tiene | Grafo completo con PageRank |
| Relevancia | Manual (Claude decide) | Automatica (PageRank rankea) |
| Tool calls | 5-15 por tarea | 1-3 por tarea |
| Falsos positivos | Muchos (comentarios, strings) | Minimos (entiende AST) |
| Endpoints API | Grep por "@router" | Deteccion precisa + metadata |
| Code health | No tiene | Complejidad, acoplamiento, smells |

**Ejemplo concreto**: Buscar "KBManager" con Grep retorna 23 resultados incluyendo comentarios, strings, y el propio archivo. `find_references("KBManager")` retorna exactamente 7 referencias reales, clasificadas por tipo (import, instanciacion, herencia).

### vs mcp-server-tree-sitter (wrale)

| Aspecto | wrale/mcp-server-tree-sitter | Nuestro Code Intel |
|---------|------------------------------|-------------------|
| Tools | 22 tools (muchos) | 8 tools (focused) |
| PageRank | No tiene | Si — smart context selection |
| Code health | Basico (analyze_complexity) | Completo (CC, acoplamiento, smells) |
| API endpoints | No detecta | Deteccion automatica |
| Complejidad config | YAML config, cache settings | Zero config |
| Smart context | No tiene | Tool estrella |
| Enfoque | General (cualquier lenguaje) | Optimizado para Python+TS |

**Ventaja clave nuestra**: `get_smart_context` no existe en ningun MCP server actual. Es la combinacion de tree-sitter + PageRank (estilo Aider) lo que hace la diferencia.

### vs Srclight

| Aspecto | Srclight | Nuestro Code Intel |
|---------|----------|-------------------|
| Tools | 29 tools | 8 tools |
| Indexing | SQLite + FTS5 + embeddings | En memoria (mas simple) |
| Scale | Multi-repo, miles de archivos | Single-repo, ~100-500 archivos |
| Setup | Complejo (GPU opcional) | Zero config, un comando |
| Dependencias | Pesadas (embeddings, SQLite) | Ligeras (~5 paquetes) |
| Mantenimiento | Alto | Bajo |

**Srclight gana para**: repos masivos (>10K archivos), busqueda semantica, equipos grandes.
**Nosotros ganamos para**: proyectos personales/medianos, setup instantaneo, zero config.

### Que da Code Intel que Claude Code NO tiene nativamente

1. **Grafo de dependencias**: Claude hoy no sabe "quien importa a quien" sin leer cada archivo.
2. **PageRank sobre codigo**: Seleccion automatica de los archivos mas relevantes para una tarea.
3. **Metricas de salud**: Complejidad, acoplamiento, code smells — sin instalar ruff/pylint.
4. **Deteccion de endpoints**: Saber todos los endpoints sin leer cada router.
5. **Busqueda estructural**: "funciones async con mas de 3 parametros" no es posible con Grep.
6. **Reduccion de tool calls**: De 7-15 calls a 1-3 por tarea tipica.

### Consideraciones de Performance

| Operacion | Tiempo Esperado | Notas |
|-----------|----------------|-------|
| Index 80 archivos | ~1-2s | tree-sitter parsea ~10K lineas en <100ms |
| get_symbols (1 archivo) | <50ms | Cache hit: <1ms |
| find_references | <100ms | Scan del store en memoria |
| get_smart_context | ~200-500ms | Incluye PageRank computation |
| analyze_health | ~100-300ms | Recorrido del AST |
| Re-index incremental | <100ms | Solo archivos con mtime cambiado |

**Memoria**: El store en memoria para un proyecto de 80 archivos usa ~5-10MB. Para 500 archivos, ~30-50MB. Aceptable para un proceso MCP que vive durante la sesion de Claude Code.

**Startup**: El server arranca en <1s (no indexa al arrancar, es lazy). La primera llamada a una tool que requiera el indice lo construye on-demand.

---

## Fuentes de Investigacion

### MCP Protocol y SDK
- [Build an MCP Server - Documentacion Oficial](https://modelcontextprotocol.io/docs/develop/build-server)
- [Python SDK - GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [mcp en PyPI](https://pypi.org/project/mcp/)
- [FastMCP - gofastmcp.com](https://gofastmcp.com/tutorials/create-mcp-server)
- [Claude Code MCP Docs](https://code.claude.com/docs/en/mcp)
- [MCP Tool Schema Best Practices](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

### MCP Servers de Code Intelligence Existentes
- [wrale/mcp-server-tree-sitter](https://github.com/wrale/mcp-server-tree-sitter) — 22 tools, el mas completo para tree-sitter
- [srclight/srclight](https://github.com/srclight/srclight) — 29 tools, FTS5 + embeddings + call graphs
- [nendotools/tree-sitter-mcp](https://github.com/nendotools/tree-sitter-mcp) — CLI + MCP, structural data
- [johnhuang316/code-index-mcp](https://github.com/johnhuang316/code-index-mcp) — 7 lenguajes core + fallback
- [flytohub/flyto-indexer](https://github.com/flytohub/flyto-indexer) — Impact analysis + semantic search
- [jgravelle/jcodemunch-mcp](https://github.com/jgravelle/jcodemunch-mcp) — Token-efficient AST exploration
- [pdavis68/RepoMapper](https://github.com/pdavis68/repomapper) — Port de Aider's repo-map a MCP

### tree-sitter
- [py-tree-sitter - GitHub](https://github.com/tree-sitter/py-tree-sitter)
- [py-tree-sitter docs](https://tree-sitter.github.io/py-tree-sitter/)
- [tree-sitter-languages PyPI](https://pypi.org/project/tree-sitter-languages/)
- [Simon Willison - Using tree-sitter with Python](https://til.simonwillison.net/python/tree-sitter)
- [Tree-sitter Code Navigation](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html)

### Aider Repo Map (PageRank sobre codigo)
- [Repository Map - Aider docs](https://aider.chat/docs/repomap.html)
- [Building a better repo map with tree-sitter - Blog](https://aider.chat/2023/10/22/repomap.html)
- [aider/repomap.py - Source code](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)
- [Repository Mapping System - DeepWiki](https://deepwiki.com/Aider-AI/aider/4.1-repository-mapping)

### Code Health y Metricas
- [Radon - Python code metrics](https://radon.readthedocs.io/en/latest/intro.html)
- [Code Metrics - Full Stack Python](https://www.fullstackpython.com/code-metrics.html)
