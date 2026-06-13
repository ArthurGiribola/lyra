# Lyra — Auditoria CTO V1

**Data:** 2026-06-11  
**Autor:** ArthurGiribola  
**Status:** Aprovado para Sprint 0

---

## Sumário executivo

Lyra é uma plataforma que resolve músicas a partir de links do Spotify e retorna letras formatadas. A decisão central de escopo da V1 é fazer uma coisa com qualidade: dado um link do Spotify, retorne a letra. Tudo o que estiver fora disso é trabalho futuro.

Este documento registra as decisões arquiteturais, o escopo fechado da V1, o que deliberadamente ficou de fora e o raciocínio por trás de cada escolha.

---

## 1. Escopo da V1

### Incluído

| Funcionalidade | Detalhes |
|---|---|
| Input | Link do Spotify apenas (`open.spotify.com/track/...`) |
| Resolução de metadados | Spotify API (Client Credentials) |
| Busca de letra | LRCLib API (pública, sem chave) |
| Persistência | Supabase/PostgreSQL para tracks e lyrics |
| Token Spotify | Cache em memória no processo FastAPI |
| Endpoint principal | `POST /lyrics` |
| Health check | `GET /health` |
| Interface web | Next.js 15 consumindo a API |

### Excluído deliberadamente da V1

| Item | Justificativa |
|---|---|
| YouTube Music, Apple Music, Deezer | Cada plataforma tem API, parsing e casos-limite diferentes. Adicionar antes de validar o fluxo Spotify gera complexidade sem aprendizado proporcional. |
| pgvector / busca vetorial | Depende de volume de dados e caso de uso (Universe/Search) que ainda não foram validados. Custo de operação é real; benefício na V1 é zero. |
| Endpoints admin (takedown, métricas, painel) | Operação desnecessária até ter usuários reais. Health check é suficiente. |
| Autenticação de usuário | O produto V1 não tem sessão de usuário. A única auth necessária é server-side com Spotify. |
| Redis / cache distribuído | Sem Redis na V1. Token Spotify fica em memória. Letras já buscadas ficam no Postgres. Latência adicional é aceitável até o produto ser validado. |
| Rate limiting por usuário | Sem usuários identificados, rate limiting por IP pode ser feito na borda (proxy/Supabase). |

---

## 2. Decisões arquiteturais

### 2.1 Por que FastAPI e não Flask ou Django?

FastAPI tem validação de request/response nativa via Pydantic v2, suporte async de primeira classe (necessário para I/O com Spotify e Genius em paralelo no futuro), geração automática de OpenAPI/docs e tipagem Python que o IDE já entende. Flask exigiria montar validação manualmente; Django traz ORM e auth que não são necessários na V1 e adiciona peso de configuração. FastAPI é a escolha com melhor DX e performance para APIs assíncronas novas.

### 2.2 Por que SQLAlchemy + Alembic e não outro ORM?

SQLAlchemy é o ORM mais maduro do ecossistema Python, com suporte async robusto na v2 (`AsyncSession`), migrations via Alembic sem surpresas e queries SQL legíveis quando necessário. Alternativas como Tortoise ORM ou SQLModel são mais jovens e têm histórico de breaking changes. Para um projeto que vai crescer para features de IA (embeddings, pgvector), SQLAlchemy é o que tem melhor suporte da comunidade.

### 2.3 Por que Supabase e não Postgres puro?

Supabase é Postgres gerenciado com autenticação, Row Level Security e REST automático prontos para quando forem necessários. Localmente, docker-compose usa Postgres puro — o `DATABASE_URL` aponta para Supabase em produção, para localhost em dev. A decisão não prende a nenhuma abstração proprietária: é Postgres por baixo e pode ser migrado a qualquer momento.

### 2.4 Por que sem Redis na V1?

Redis resolve dois problemas: cache de token e cache de letras. Na V1, o token Spotify fica em memória no processo FastAPI (uma variável de módulo com timestamp de expiração), que é suficiente para uma instância. Letras já buscadas ficam no Postgres — uma query por `track_id` com índice primário tem latência de 5-20ms, aceitável até o produto ter usuários reais. Adicionar Redis agora seria infraestrutura sem demanda comprovada. A decisão de adicionar Redis fica aberta para V1.1 se a latência do Postgres se provar um problema.

### 2.5 Por que Client Credentials e não Authorization Code?

Na V1 o Lyra não age em nome de usuário. A API só precisa de metadados públicos da track (título, artista, álbum). Client Credentials é mais simples, não expira por inatividade do usuário e não requer fluxo de redirect. Authorization Code só fará sentido quando/se houver features personalizadas por conta (playlists, histórico do usuário).

### 2.6 Por que LRCLib como provider de letra?

LRCLib é uma API pública de letras sincronizadas, sem necessidade de chave de API ou cadastro. A integração é um único `GET /api/get?track_name=...&artist_name=...` que retorna JSON com o campo `plainLyrics`. Vantagens para a V1: zero configuração operacional, sem rate limit documentado, resposta limpa e previsível. Adicionalmente, o formato LRC (letras sincronizadas por timestamp) está disponível no mesmo endpoint e pode ser aproveitado em versões futuras para exibição karaokê. Se a cobertura do LRCLib se provar insuficiente para certos gêneros ou regiões, Genius ou Musixmatch podem ser adicionados como fallback na V1.1.

### 2.7 Por que não pgvector na V1?

pgvector resolve busca semântica. Busca semântica pressupõe um corpus indexado e um caso de uso de busca por similaridade. Na V1 o fluxo é determinístico: link → letra. Não há "buscar músicas parecidas" nem "encontrar letra por trecho". Adicionar pgvector agora significa pagar custo de operação, indexação e memória sem nenhum endpoint que use o índice. A decisão é: mencionar como opção futura para o módulo Universe, não implementar.

### 2.8 Por que Next.js 15 + Shadcn/UI?

Next.js 15 com App Router é a escolha padrão para aplicações React modernas com SSR. Tailwind + Shadcn/UI entregam componentes acessíveis e consistentes sem CSS customizado na V1. A combinação permite construir a interface de exibição de letra rapidamente. TypeScript strict no frontend mantém a paridade de rigor com o backend Python (Pydantic).

---

## 3. Modelo de dados

```
tracks
  id           TEXT PK      -- spotify:track:{spotifyId}
  title        TEXT NN
  artist       TEXT NN
  album        TEXT
  duration_ms  INTEGER
  created_at   TIMESTAMPTZ

lyrics
  id           SERIAL PK
  track_id     TEXT FK → tracks.id
  text         TEXT NN
  provider     TEXT NN      -- 'genius'
  language     TEXT
  fetched_at   TIMESTAMPTZ
```

**Por que `spotify:track:{id}` como PK e não UUID?**  
O ID do Spotify é estável, globalmente único e já é a chave natural do domínio. Usar UUID seria adicionar uma chave artificial sem ganho. Queries ficam legíveis. Sem necessidade de join extra para encontrar uma track pelo ID Spotify.

**Por que não tabela de sessão ou usuário na V1?**  
Sem autenticação de usuário, não há sessão. O Supabase provisiona Auth quando necessário — não antes.

---

## 4. Fluxo de uma requisição

```
Cliente → POST /lyrics { url: "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC" }

1. Pydantic valida o body (url é string, formato Spotify)
2. Regex extrai o track ID: "4uLU6hMCjMI75M1A2tKUQC"
3. Checa Postgres: SELECT * FROM lyrics WHERE track_id = 'spotify:track:...'
   → HIT: retorna imediatamente
   → MISS:
4. Spotify API: GET /tracks/{id}
   (token em memória; se expirado, renova via Client Credentials antes de prosseguir)
   → Extrai: title, artist, album, duration_ms
5. LRCLib API: GET /api/get?track_name={title}&artist_name={artist}
   → sucesso: letra encontrada em plainLyrics
   → falha: retorna 404 com error="lyrics_not_found"
6. INSERT tracks + INSERT lyrics no Postgres
7. Retorna resposta formatada
```

**Tratamento de erro:**
- URL não é do Spotify → 422 com mensagem clara
- Track não existe no Spotify → 404
- Letra não encontrada → 404 `{ "error": "lyrics_not_found" }`
- Falha no provider (5xx) → 502
- Erro interno → 500 (sem stack trace exposto ao cliente)

---

## 5. Sprint 0 — Entregável mínimo funcionando

**Objetivo:** ter `POST /lyrics` e `GET /health` funcionando end-to-end localmente, com interface web consumindo a API.

### Tarefas — Backend

- [ ] Inicializar `apps/api`: `pyproject.toml`, FastAPI, dependências
- [ ] `docker-compose.yml` com Postgres 16
- [ ] `config.py` com `pydantic-settings` validando todas as env vars na inicialização
- [ ] SQLAlchemy async: engine, `AsyncSession`, models `Track` e `Lyric`
- [ ] Migration inicial via Alembic
- [ ] `GET /health` retornando status do banco
- [ ] Serviço Spotify: Client Credentials com cache de token em memória (lifespan)
- [ ] Serviço Spotify: `resolve_track(url: str) → TrackMetadata`
- [x] Provider LRCLib: `get_lyrics(title: str, artist: str) → str`
- [ ] `POST /lyrics` orquestrando o fluxo completo
- [ ] Testes de integração: health, lyrics com track real, lyrics sem letra disponível
- [ ] `.env.example` documentado

### Tarefas — Frontend

- [ ] Inicializar `apps/web`: Next.js 15, TypeScript, Tailwind, Shadcn/UI
- [ ] Campo de input para URL do Spotify
- [ ] Chamada `POST /lyrics` e exibição da letra formatada
- [ ] Tratamento de erros (404, 422, 502) com mensagem amigável

### Critério de aceite do Sprint 0

```bash
curl -X POST http://localhost:8000/lyrics \
  -H "Content-Type: application/json" \
  -d '{"url":"https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"}'
```

Retorna 200 com letra formatada. Segunda chamada com a mesma URL retorna do Postgres (sem chamada ao LRCLib). Interface web exibe a letra com título e artista.

---

## 6. Observabilidade V1

Sem painel admin. O suficiente para operar:

- **Logs estruturados** (JSON) em stdout via `logging` + `python-json-logger`
- **`GET /health`** com status detalhado do banco
- **Alertas**: configurar via plataforma de deploy (Railway/Render/Fly) sobre health check failing

Prometheus, Grafana e painel admin ficam para quando houver razão operacional real.

---

## 7. Roadmap pós-V1

As decisões abaixo foram postergadas com critério.

### V1.1 — Estabilização
- Redis para cache de letras (se latência do Postgres for problema)
- Fallback de provider de letra (Musixmatch como segunda opção)
- Retry com backoff exponencial no Genius
- Rate limiting por IP

### V1.2 — Outros providers de entrada
- YouTube Music
- Apple Music
- Deezer

### V2 — Universe / Search Engine
- pgvector para busca semântica de letras
- Embeddings gerados no insert (sentence-transformers ou OpenAI)
- Endpoint `GET /search?q=trecho+da+letra`
- Endpoint `GET /similar?track_id=...`
- Tradução automática de letras

### Futuro — Admin & Compliance
- Endpoints de takedown (DMCA)
- Painel de métricas de uso
- Autenticação de usuário (Supabase Auth)

---

## 8. Riscos conhecidos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| LRCLib não encontra letra por título/artista ambíguo ou catálogo regional limitado | Média | Normalizar título antes da busca; adicionar Genius ou Musixmatch como fallback na V1.1 |
| Spotify depreca endpoint de track | Baixa | Endpoint `/tracks/{id}` é estável desde 2014 |
| Letra protegida por copyright não disponível via API | Alta para catálogo regional | 404 explícito, sem tentar scraping |
| Token Spotify perdido no restart do processo | Baixa | Renovação automática na próxima requisição; sem impacto no dado, apenas latência extra uma vez |
| Supabase connection pool esgotado sob carga | Baixa na V1 | SQLAlchemy AsyncSession com pool configurado; alert no health check |

---

*Documento gerado em 2026-06-11. Próxima revisão: ao fechar Sprint 0.*
