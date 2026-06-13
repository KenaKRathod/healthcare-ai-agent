-- AuraHealth AI: conversation memory, feedback, and medical RAG tables
-- Legacy PostgreSQL reference script. The app uses SQLAlchemy create_all with SQLite by default.

CREATE TABLE IF NOT EXISTS medical_knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR NOT NULL UNIQUE,
    created_at VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_medical_knowledge_chunks_source ON medical_knowledge_chunks (source);

CREATE TABLE IF NOT EXISTS chat_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    patient_name VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    created_at VARCHAR NOT NULL,
    updated_at VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chat_conversations_user_id ON chat_conversations (user_id);
CREATE INDEX IF NOT EXISTS ix_chat_conversations_patient_name ON chat_conversations (patient_name);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR,
    selected_tool VARCHAR,
    metadata_json TEXT,
    created_at VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chat_messages_conversation_id ON chat_messages (conversation_id);

CREATE TABLE IF NOT EXISTS chat_feedback (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chat_feedback_message_id ON chat_feedback (message_id);
CREATE INDEX IF NOT EXISTS ix_chat_feedback_user_id ON chat_feedback (user_id);
