# MindPalace

A personal RAG-powered AI agent that indexes and searches across your digital life — emails, notes, bookmarks, documents, and photos — using semantic search and LLM-based conversational retrieval.

## Features

- **Conversational RAG** — Ask natural-language questions over your personal data with streaming responses via WebSocket
- **Semantic Search** — Vector similarity search powered by sentence-transformers and ChromaDB
- **Multi-source Ingestion** — Ingest content from Gmail, Google Keep, Chrome Bookmarks, Google Drive, Google Photos, and local files via a REST API
- **Multi-tenant** — All data is scoped per user; supports multiple accounts
- **Authentication** — Username/password with HMAC-signed tokens, API keys for external integrations, and WebAuthn/passkey support for biometric login
- **PWA Frontend** — React + TypeScript SPA with offline-capable service worker, dark theme, and mobile-friendly layout
- **Streaming Chat** — Real-time token-by-token response streaming with thinking/reasoning display
- **Chat History** — Persistent chat sessions stored in PostgreSQL

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| LLM | LiteLLM (default: gpt-4o-mini) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB |
| Database | PostgreSQL |
| Frontend | React 19, TypeScript, Vite |
| Deployment | Docker Compose |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key (or any LiteLLM-compatible provider)

### Run with Docker Compose

```bash
# Clone the repo
git clone <repo-url> && cd mindpalace

# Create .env file
cat > .env <<EOF
AUTH_SECRET=your-secret-key
LLM__API_KEY=your-openai-api-key
EOF

# Start all services
docker compose up --build
```

The app will be available at `http://localhost:8080`.

### Local Development

**Backend:**

```bash
# Install Python dependencies
pip install -e .

# Start PostgreSQL and ChromaDB
docker compose up postgres chromadb -d

# Set environment variables
export DATABASE__URL=postgresql://mindpalace:mindpalace@localhost:5432/mindpalace
export VECTOR_STORE__HOST=localhost
export AUTH_SECRET=dev-secret

# Run the API server
uvicorn mindpalace.api.main:app --host 0.0.0.0 --port 8080 --reload
```

**Frontend:**

```bash
cd web
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/ws` to `localhost:8080`.

## Configuration

Settings are loaded from environment variables using the `__` delimiter for nested values:

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_SECRET` | HMAC signing key for auth tokens | *required* |
| `DATABASE__URL` | PostgreSQL connection string | `postgresql://...localhost.../mindpalace` |
| `VECTOR_STORE__HOST` | ChromaDB host | `localhost` |
| `VECTOR_STORE__PORT` | ChromaDB port | `8000` |
| `LLM__API_KEY` | LLM provider API key | — |
| `LLM__MODEL` | LLM model name | `gpt-4o-mini` |
| `LLM__BASE_URL` | Custom LLM endpoint | — |
| `EMBEDDING__MODEL` | Embedding model | `all-MiniLM-L6-v2` |
| `RAG__TOP_K` | Number of chunks to retrieve | `10` |
| `RAG__CHUNK_SIZE` | Chunk size in tokens | `512` |
| `WEBAUTHN_RP_ID` | WebAuthn relying party ID | `localhost` |
| `WEBAUTHN_ORIGIN` | WebAuthn origin URL | `http://localhost:8080` |

## API Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/register` | POST | — | Create account |
| `/api/auth/login` | POST | — | Login with password |
| `/api/auth/webauthn/*` | POST/GET | — / Token | Passkey registration and login |
| `/api/chat` | POST | Token | Non-streaming chat |
| `/api/search` | POST | Token | Semantic search |
| `/api/stats` | GET | Token | Collection stats |
| `/api/chats` | GET/POST | Token | List/create chat sessions |
| `/api/chats/{id}` | GET/PATCH/DELETE | Token | Manage a session |
| `/api/ingest/documents` | POST/DELETE | API Key | Ingest or delete documents |
| `/ws/chat` | WebSocket | Token | Streaming chat |
| `/api/health` | GET | — | Health check |

## Project Structure

```
mindpalace/
├── agent/          # RAG engine (retrieve + ask)
├── api/            # FastAPI app, WebSocket, routes
│   └── routes/     # auth, chat, history, ingest
├── llm/            # LiteLLM wrapper
├── pipeline/       # Chunking and embedding
├── store/          # ChromaDB client
├── config.py       # Pydantic settings
├── db.py           # SQLAlchemy models and session
└── models.py       # Document and Chunk dataclasses
web/                # React frontend (Vite + TypeScript)
scripts/            # Utility scripts
docs/               # Architecture and design docs
```

See [docs/DESIGN.md](docs/DESIGN.md) for detailed architecture documentation.