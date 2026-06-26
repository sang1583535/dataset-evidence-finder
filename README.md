# Dataset Evidence Finder

Dataset Evidence Finder is a research support tool that helps researchers discover
dataset candidates and supporting evidence for a given research topic, with a focus
on **NLP / Computational Linguistics**. It combines dataset source search, academic
paper search, and section-aware evidence extraction into a single web application.

## What It Does

- Helps researchers discover datasets related to a research topic.
- Searches dataset sources (Hugging Face, European Language Grid, OpenML, DataCite)
  and academic papers (arXiv).
- Extracts evidence sentences from papers showing where datasets are mentioned or used.
- Presents dataset candidates, paper candidates, and extracted evidence in a web interface.

The system is intended to support discovery and manual verification, not to act as a
fully automatic ground-truth detector of dataset usage.

## Features

- **Topic-based dataset search** from a single research query.
- **Dataset candidate collection** from Hugging Face Datasets, European Language Grid,
  OpenML, and DataCite.
- **arXiv paper search** for related academic papers.
- **GROBID-based structured PDF extraction** for section titles and full text.
- **PyMuPDF fallback** when GROBID is unavailable or fails to parse a PDF.
- **Section-aware evidence extraction** targeting relevant sections such as
  *Dataset*, *Data*, *Experiments*, *Evaluation*, and *Results*.
- **Evidence sentence extraction** with source information and section titles.
- **Basic dataset-paper matching** to link dataset candidates with paper evidence.
- **Optional caching** of source searches and GROBID sections to speed up repeated queries.

## Pipeline

```text
User query
  → Dataset source search (Hugging Face, ELG, OpenML, DataCite)
  → arXiv paper search
  → GROBID PDF parsing (PyMuPDF fallback)
  → Evidence sentence extraction
  → Dataset-paper matching
  → Streamlit result display
```

A slightly more detailed view of the flow:

1. User enters a research topic.
2. Backend searches dataset sources for candidate datasets.
3. Backend searches arXiv for related papers.
4. GROBID extracts structured text and section titles from PDFs
   (PyMuPDF is used as a fallback when GROBID fails).
5. Evidence sentences are extracted from relevant sections.
6. Candidate datasets and paper evidence are displayed in the frontend.

## Project Structure

```text
dataset-evidence-finder/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── api/             # API routes
│   │   ├── core/            # Configuration and settings
│   │   ├── models/          # Pydantic schemas / data models
│   │   ├── services/        # Source search, GROBID, evidence extraction, matching
│   │   └── utils/           # Helper utilities (text processing, etc.)
│   ├── cache/               # Cached source searches and GROBID sections
│   ├── tests/               # Backend test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py               # Streamlit entry point
│   ├── components/          # UI components
│   ├── api_client.py        # Backend API client
│   ├── requirements.txt
│   └── Dockerfile
├── scripts/                 # Helper run scripts
├── docker-compose.yml
├── docker-compose.dev.yml
├── LICENSE
└── README.md
```

## Setup and Run

### Option 1: Run with Docker (recommended)

Docker Compose starts the **frontend**, **backend**, and **GROBID** services together.

```bash
docker compose up --build
```

Once the containers are running, the services are available at:

- Frontend: [http://localhost:8501](http://localhost:8501/)
- Backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- GROBID service: [http://localhost:8070](http://localhost:8070/)

To stop and remove the containers:

```bash
docker compose down
```

> GROBID can take up to 60 seconds to start. The backend waits for it to be healthy
> before launching.

### Option 2: Run Locally with Conda

Create and activate an environment:

```bash
conda create -n dataset-evidence-finder python=3.11
conda activate dataset-evidence-finder
```

Start the backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start the frontend (in a separate terminal):

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

If you need full-text structured extraction, GROBID should be running separately.
The project uses the same image defined in `docker-compose.yml`:

```bash
docker run --rm -p 8070:8070 grobid/grobid:0.9.0-crf
```

When running locally, GROBID is optional. If it is not reachable, the backend
automatically falls back to PyMuPDF.

## Configuration

The application reads a few environment variables:

- `GROBID_URL` — URL of the GROBID service used for structured PDF extraction.
- `BACKEND_API_URL` — URL the frontend uses to reach the backend API.

Example values:

```bash
GROBID_URL=http://grobid:8070
BACKEND_API_URL=http://backend:8000/api
```

When running via Docker Compose, these values are already set for you. For local
runs, the defaults point to `http://localhost:8070` (GROBID) and
`http://localhost:8000/api` (backend). You can copy `.env.example` to `.env` and
adjust values as needed.

## How to Run Tests

Backend tests can be run from the `backend` directory:

```bash
cd backend
pytest -q
```

For more detailed output:

```bash
pytest -v
```

A quick syntax check of the frontend entry point can be run from the `frontend`
directory:

```bash
cd frontend
python -m py_compile app.py
```

You can also run the backend tests inside the running Docker containers. With the
services started via `docker compose up`, run the tests in the backend container:

```bash
docker compose exec backend pytest -q
```

To run the tests in a one-off container without starting the full stack:

```bash
docker compose run --rm backend pytest -q
```

The repository may also include GitHub Actions workflows that automatically run
basic backend and frontend checks on push or pull request.

## Possible Limitations

- Dataset names extracted from papers may be noisy.
- Some papers may not have accessible or parseable PDFs.
- GROBID extraction can be slower than raw text extraction.
- Matching dataset names to paper evidence is approximate and may require manual verification.
- Coverage depends on the availability and quality of external sources such as
  arXiv, Hugging Face, OpenML, ELG, and DataCite.
- The system is intended as a discovery and evidence-support tool, not a fully
  automatic ground-truth dataset usage detector.
- The current implementation focuses on a selected set of sources to keep the
  system manageable. Other relevant sources, including Kaggle, Zenodo, OpenAlex,
  re3data, LDC, and ELRA, are acknowledged as important dataset discovery or
  catalogue resources, but are left for future integration.

## Acknowledgements

We thank **Prof. Kan Min-Yen** for providing valuable feedback and guidance during
the development of this project. We also acknowledge **arXiv**, **Hugging Face**,
**OpenML**, **European Language Grid**, and **DataCite** as important resources for
dataset and paper discovery. Structured PDF extraction is powered by
[**GROBID**](https://github.com/kermitt2/grobid). Parts of the software development
process were supported by **GitHub Copilot**.

## License

This project is licensed under the terms described in the [LICENSE](LICENSE) file
(MIT License).
