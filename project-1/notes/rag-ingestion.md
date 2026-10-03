# RAG Ingestion - Design Note

## Purpose
Load FAQ into Supabase with embeddings for retrieval.

## Pipeline
1. Read file from disk (/data mount)
2. Extract text
3. Chunk into 500-char segments
4. Embed via OpenRouter (text-embedding-3-small)
5. Insert into documents table

## Chunking
- Fixed size: 500 chars
- Sanitize newlines to spaces (prevents JSON errors)
- Track chunk_index

## Embedding
- Model: openai/text-embedding-3-small (1536 dims)
- Called via OpenRouter

## Storage
- Supabase documents table
- Columns: content, embedding (vector), source, chunk_index

## Failure Handling
- Empty chunks skipped
- Invalid JSON -> workflow error

## Alternatives Considered
- Semantic chunking -> too slow for prototype
- Larger chunks -> exceeds embedding window
