-- Enable pgvector extension for semantic search (embeddings).
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
