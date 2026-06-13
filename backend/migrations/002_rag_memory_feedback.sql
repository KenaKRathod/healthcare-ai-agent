-- AuraHealth AI: Chroma-backed RAG metadata, conversation health context, feedback query/response

ALTER TABLE IF EXISTS chat_conversations
    ADD COLUMN IF NOT EXISTS health_context_json TEXT;

ALTER TABLE IF EXISTS chat_feedback
    ADD COLUMN IF NOT EXISTS query TEXT,
    ADD COLUMN IF NOT EXISTS response TEXT;
