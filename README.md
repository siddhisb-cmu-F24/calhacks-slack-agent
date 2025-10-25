# Slack Q&A Agent

Minimal FastAPI service that stores Slack Q&A memories in Supabase (pgvector), searches for relevant answers, and posts replies back to Slack threads. Designed to be orchestrated by Postman Flows.

## Features
- `/memory/upsert` – embed a question, persist QA memory + vector to Supabase.
- `/memory/search` – embed new query and run pgvector similarity search via RPC.
- `/slack/reply` – format and post answers/follow-ups to Slack threads.
- Health endpoint for monitoring plus JSON problem responses.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in secrets
```

Enable pgvector and create the knowledge table + indexes:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE public.kb (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  channel TEXT,
  q_text TEXT NOT NULL,
  a_text TEXT NOT NULL,
  source_url TEXT,
  ts TIMESTAMPTZ DEFAULT NOW(),
  embedding VECTOR(1536) NOT NULL
);
CREATE INDEX kb_embedding_idx ON public.kb USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX kb_channel_ts_idx ON public.kb(channel, ts DESC);
```

Create an RPC wrapper called `match_memories` that executes the cosine-distance SQL shown in the spec so PostgREST can order the matches. Point `SUPABASE_SEARCH_FUNCTION` to that function name if you choose something else.

Launch the API locally:
```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --reload
```

## Environment Variables
See `.env.example` for the full list. Critical values:
- `SLACK_BOT_TOKEN` – bot user token used for replies
- `SUPABASE_SERVICE_ROLE_KEY` – service key for inserts/RPC (keep server-side)
- `EMBEDDING_API_URL` / `EMBEDDING_API_KEY` – embedding provider endpoint
- `EMBEDDING_DIM` – vector length (defaults to 1536)

## API Examples
```bash
curl -X POST http://localhost:8080/memory/upsert \
  -H 'content-type: application/json' \
  -d '{"channel":"C1","q_text":"How request VPN?","a_text":"Use form...","source_url":"https://confluence/vpn"}'

curl -X POST http://localhost:8080/memory/search \
  -H 'content-type: application/json' \
  -d '{"channel":"C1","query":"vpn access","k":3}'

curl -X POST http://localhost:8080/slack/reply \
  -H 'content-type: application/json' \
  -d '{"channel":"C1","thread_ts":"1729.1","answer":"Here is how...","references":[{"title":"VPN SOP","url":"https://..."}],"mode":"answer","confidence":0.9}'
```

Responses include cosine distances (lower = closer). If you prefer similarity scores, normalize in the Postman Flow.

## Development Notes
- Uses shared `httpx.AsyncClient` and Supabase client singletons for efficiency.
- Embeddings provider must return `{ "embedding": [float, ...] }` with the configured dimension.
- Slack replies are prefixed with `[Auto-Reply]`, include up to two sources, and append a clarifying question when in follow-up mode.
- Tests run via `pytest -q` and rely on `respx` to mock external HTTP calls.
- Avoid logging or echoing secrets; loguru is configured at import time.
