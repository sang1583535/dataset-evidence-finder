# NLP/CL Dataset Evidence Finder

Find NLP/Computational Linguistics dataset candidates and supporting evidence sentences from arXiv papers. Searches Hugging Face, European Language Grid, OpenML, and DataCite, then matches datasets against paper abstracts and full text.

## Running with Docker

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (Streamlit) | http://localhost:8501 |
| Backend API docs | http://localhost:8000/docs |
| GROBID | http://localhost:8070 |

```bash
# Stop all services
docker compose down
```

> GROBID can take up to 60 seconds to start. The backend waits for it to be healthy before launching.

## PDF Extraction

GROBID is used by default for structured, section-aware full-text extraction from arXiv PDFs. If GROBID is unavailable or returns no content for a paper, the backend automatically falls back to PyMuPDF. This is handled entirely in the backend — the frontend has no extraction toggle.

## Running Locally (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

When running locally, GROBID is optional. If it is not running at `http://localhost:8070`, the backend falls back to PyMuPDF automatically.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROBID_URL` | `http://localhost:8070` | GROBID service URL |
| `BACKEND_API_URL` | `http://localhost:8000/api` | Backend URL used by the frontend |
| `MAX_ALIAS_QUERIES` | `5` | Max alias-based arXiv queries per search |

Copy `.env.example` to `.env` and adjust as needed for local overrides.

## GitHub Actions

This repository includes two GitHub Actions workflows:

- CI: installs backend/frontend dependencies and runs basic checks.
- Docker Build: verifies that backend and frontend Docker images can build successfully.

The full application is intended to be deployed on Railway or another container platform because it requires running backend, frontend, and GROBID services.
