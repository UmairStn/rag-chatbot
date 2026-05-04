# AGENT.md

Guidance for coding agents working in this repository.

## Project Overview
- Purpose: Multi-tenant RAG chatbot system with a FastAPI backend and a React + TypeScript frontend.
- Key parts:
  - `backend/`: API, ingestion, chat services, vector DB (ChromaDB).
  - `frontend/`: Admin dashboard + embeddable chat widget (UMD, Shadow DOM).

## Repo Map
- `backend/main.py`: CLI entry point.
- `backend/api/main.py`: FastAPI app.
- `backend/api/routes/ingest.py`: POST /ingest.
- `backend/api/routes/chat.py`: POST /chat.
- `backend/services/`: scraper, indexer, chatbot logic.
- `frontend/src/pages/AdminDashboard.tsx`: Admin UI.
- `frontend/src/components/ChatWidget.tsx`: Chat widget UI.
- `frontend/src/widget/embed.tsx`: UMD widget entry.

## Setup
### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python -m api.main
```
- API docs: `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
- Admin dashboard: `http://localhost:3000`

## Common Commands
- Backend (CLI): `python backend/main.py`
- Backend (API): `python -m api.main`
- Frontend dev: `npm run dev` (in `frontend/`)
- Build dashboard: `npm run build` (in `frontend/`)
- Build widget: `npm run build:widget` (in `frontend/`)
- Preview build: `npm run preview` (in `frontend/`)

## Environment Variables
### Backend (`backend/.env`)
- `API_KEY`: API auth key (required).
- `GOOGLE_API_KEY`: Gemini API key (required).
- `ALLOWED_ORIGINS`: Comma-separated CORS origins.

### Frontend (`frontend/.env`)
- `VITE_API_URL`: Backend API base URL.
- `VITE_API_KEY`: API key for local dev.

## Behavior & Conventions
- Keep multi-tenant isolation by always passing `client_id` in ingest/chat flows.
- Preserve Shadow DOM isolation in widget styles.
- Prefer existing API models and request shapes in `backend/api/models/schemas.py`.
- Avoid committing secrets; `.env` files are local-only.

## Testing & Verification
- No formal test suite; verify manually:
  - Start backend and frontend.
  - Ingest a site via Admin Dashboard.
  - Chat via dashboard or widget to confirm responses.

## Documentation References
- `README.md`: product overview.
- `PROJECT_SUMMARY.md`: end-to-end workflow and commands.
- `backend/API_DOCUMENTATION.md`: API details.
- `frontend/SETUP.md`: frontend setup/deploy.
- `frontend/WIDGET_INTEGRATION.md`: widget install steps.
