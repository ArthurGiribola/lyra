# Lyra — CLAUDE.md

## O que é este projeto

Lyra é uma plataforma que recebe um link do Spotify, resolve os metadados da música e retorna a letra formatada. A V1 entrega isso como API + interface web. O foco é simplicidade operacional: um fluxo end-to-end funcionando com qualidade antes de qualquer expansão.

## Stack

### Backend (API)

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Framework | FastAPI |
| Banco | Supabase / PostgreSQL |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Validação | Pydantic v2 |
| HTTP client | httpx (async) |
| Provider de letra | Genius (`lyricsgenius`) |
| Auth Spotify | OAuth 2.0 Client Credentials (server-side) |
| Testes | pytest + httpx AsyncClient |
| Container | Docker + docker-compose |

### Frontend (Web)

| Camada | Tecnologia |
|---|---|
| Framework | Next.js 15 (App Router) |
| Linguagem | TypeScript strict |
| Estilo | Tailwind CSS |
| Componentes | Shadcn/UI |

### Futuro (IA)

Python já é a linguagem do backend, o que elimina fricção para integrar:
- Embeddings de letras (sentence-transformers ou OpenAI)
- Recomendação por similaridade (pgvector)
- Tradução automática
- Análise semântica de letras

---

## Estrutura de diretórios (planejada)

```
lyra/
  apps/
    api/                        ← FastAPI
      main.py                   # bootstrap FastAPI + lifespan
      routers/
        health.py               # GET /health
        lyrics.py               # POST /lyrics
      services/
        spotify.py              # resolve track via link
        lyrics.py               # orquestra busca de letra
      providers/
        genius.py               # Genius API
      db/
        models.py               # SQLAlchemy models
        session.py              # engine + AsyncSession
      schemas/
        lyrics.py               # Pydantic request/response
      config.py                 # Settings via pydantic-settings
    web/                        ← Next.js 15
      app/
        page.tsx
        layout.tsx
      components/
      lib/
  migrations/                   # Alembic
    versions/
    env.py
  docs/
    lyra-auditoria-cto-v1.md
  tests/
    test_health.py
    test_lyrics.py
  docker-compose.yml
  pyproject.toml
  .env.example
  CLAUDE.md
```

> `apps/web` e `apps/api` ainda não foram criados. A estrutura acima é o plano para o Sprint 0.

---

## Variáveis de ambiente obrigatórias

```
# Banco
DATABASE_URL=postgresql+asyncpg://...

# Spotify
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=

# Lyrics provider
GENIUS_API_KEY=

# App
ENVIRONMENT=development
PORT=8000
```

---

## Comandos principais (backend)

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Instalar dependências
pip install -e ".[dev]"

# Subir infraestrutura local
docker-compose up -d

# Rodar migrations
alembic upgrade head

# Dev com hot-reload
uvicorn apps.api.main:app --reload --port 8000

# Testes
pytest

# Testes com cobertura
pytest --cov=apps/api
```

## Comandos principais (frontend)

```bash
cd apps/web
npm install
npm run dev     # http://localhost:3000
npm run build
npm run lint
```

---

## Endpoints V1

### `GET /health`

Retorna status da API e do banco. Sem autenticação.

**Response 200:**
```json
{
  "status": "ok",
  "database": "ok",
  "version": "1.0.0"
}
```

### `POST /lyrics`

Recebe link do Spotify, resolve a música e retorna a letra.

**Request:**
```json
{ "url": "https://open.spotify.com/track/..." }
```

**Response 200:**
```json
{
  "track": {
    "id": "spotify:track:...",
    "title": "Nome da Música",
    "artist": "Nome do Artista",
    "album": "Nome do Álbum",
    "duration_ms": 210000,
    "spotify_url": "https://open.spotify.com/track/..."
  },
  "lyrics": {
    "text": "Verso 1\n...\nCoro\n...",
    "provider": "genius",
    "language": "pt"
  }
}
```

**Response 404:** música encontrada mas letra não disponível  
**Response 422:** URL inválida ou não é do Spotify  
**Response 502:** falha no provider de letra

---

## Banco de dados (V1)

Duas tabelas:

```sql
tracks (
  id           TEXT PRIMARY KEY,  -- spotify:track:{id}
  title        TEXT NOT NULL,
  artist       TEXT NOT NULL,
  album        TEXT,
  duration_ms  INTEGER,
  created_at   TIMESTAMPTZ DEFAULT now()
)

lyrics (
  id           SERIAL PRIMARY KEY,
  track_id     TEXT REFERENCES tracks(id),
  text         TEXT NOT NULL,
  provider     TEXT NOT NULL,   -- 'genius'
  language     TEXT,
  fetched_at   TIMESTAMPTZ DEFAULT now()
)
```

Sem pgvector na V1. Busca vetorial fica reservada para o módulo Universe/Search Engine em versão futura.

---

## Fluxo principal

```
POST /lyrics
  └── Pydantic valida body
  └── regex extrai track ID do link Spotify
  └── checa Postgres (letra já salva?)
      ├── HIT → retorna
      └── MISS
          └── Spotify API → metadados da track
              (token em memória, renovado via lifespan se expirado)
          └── Genius API → letra pelo título + artista
          └── INSERT tracks + INSERT lyrics
          └── retorna
```

O token Spotify é mantido em memória no processo FastAPI (variável de módulo com timestamp de expiração). Sem Redis na V1.

---

## Regras de desenvolvimento

- Pydantic v2 em todos os schemas de entrada e saída. Nunca `dict` cru.
- SQLAlchemy async em todas as queries. Nunca operações síncronas em rotas.
- Erros externos (Spotify, Genius) nunca chegam crus ao cliente: envolva em exceções de domínio com HTTPException apropriado.
- Testes de integração usam banco PostgreSQL real via docker-compose. Sem mocks de infraestrutura de dados.
- Type hints obrigatórios em todas as funções. Sem `Any` sem comentário justificando.
- Commits em inglês, mensagem no imperativo.
- Nenhum endpoint admin na V1.

---

## O que não está na V1

- `apps/web` e `apps/api` (ainda não criados — Sprint 0 os inicializa)
- YouTube Music, Apple Music, Deezer (futuro)
- pgvector / busca semântica (futuro — módulo Universe)
- Endpoints admin, takedown, métricas agregadas (futuro)
- Autenticação de usuário final (futuro)
- Rate limiting por usuário (futuro)
- Redis / cache distribuído (futuro, se a latência do Postgres se tornar problema)
