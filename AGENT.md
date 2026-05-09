# AGENT.md

Guidance for coding agents working in this repository.

## Project Overview
- Purpose: Multi-tenant RAG chatbot system with a FastAPI backend and a pre-built embeddable chat widget (UMD, Shadow DOM).
- Key parts:
  - `backend/`: API, ingestion, chat services, vector DB (ChromaDB).
  - `widget/`: Pre-built UMD bundles served by nginx.

## Repo Map
- `backend/main.py`: CLI entry point.
- `backend/api/main.py`: FastAPI app.
- `backend/api/routes/ingest.py`: POST /ingest.
- `backend/api/routes/chat.py`: POST /chat.
- `backend/services/`: scraper, indexer, chatbot logic.
- `widget/*.umd.js`: Pre-built widget bundles.

## Setup
### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python -m api.main
```
- API docs: `http://localhost:8000/docs`

### Widget
The widget is shipped as pre-built UMD bundles in `widget/` and served via the `widget` container.

## Common Commands
- Backend (CLI): `python backend/main.py`
- Backend (API): `python -m api.main`

## Environment Variables
### Backend (`backend/.env`)
- `API_KEY`: API auth key (required).
- `GOOGLE_API_KEY`: Gemini API key (required).
- `ALLOWED_ORIGINS`: Comma-separated CORS origins.

## Behavior & Conventions
- Keep multi-tenant isolation by always passing `client_id` in ingest/chat flows.
- Preserve Shadow DOM isolation in widget styles.
- Prefer existing API models and request shapes in `backend/api/models/schemas.py`.
- Avoid committing secrets; `.env` files are local-only.

## Testing & Verification
- No formal test suite; verify manually:
  - Start backend.
  - Ingest a site via `http://localhost:8000/docs`.
  - Chat via widget to confirm responses.

## Documentation References
- `README.md`: product overview.
- `PROJECT_SUMMARY.md`: end-to-end workflow and commands.
- `backend/API_DOCUMENTATION.md`: API details.
