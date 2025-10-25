from __future__ import annotations

import os

pytest_plugins = ["respx"]

_env_defaults = {
    "SLACK_BOT_TOKEN": "xoxb-test",
    "SLACK_POST_AS_USER": "false",
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
    "SUPABASE_ANON_KEY": "anon-key",
    "SUPABASE_SCHEMA": "public",
    "SUPABASE_TABLE": "kb",
    "SUPABASE_SEARCH_FUNCTION": "match_memories",
    "EMBEDDING_API_URL": "https://embeddings.test/vector",
    "EMBEDDING_API_KEY": "emb-key",
    "EMBEDDING_DIM": "8",
    "LOG_LEVEL": "INFO",
}

for key, value in _env_defaults.items():
    os.environ.setdefault(key, value)
