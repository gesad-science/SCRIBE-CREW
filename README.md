# SCRIBE (alternate / monolithic variant)

> **Important notice**: this repository is **an alternative SCRIBE variant**.  
> The **mainline version** lives on the **`main`** branch.  
> This variant is **more monolithic** and **does not include A2A**.

## Overview

**SCRIBE** is a system to **automate research workflows and academic reference handling** using a multi-agent architecture (coordinated by a core orchestrator), including:

- A **Python API** (FastAPI) to run executions and receive requests
- A **Web UI** (Vite + React + TypeScript + shadcn/ui) for browser interaction
- **RAG / vector storage** via **Qdrant** (optional, depending on configuration)
- Support for **remote LLMs** (via `litellm`) and/or **Ollama** (when enabled)

## Components

- **Backend (API)**: `main.py` + `src/`
  - `POST /execute` receives a message and triggers an execution.
  - `POST /execute-with-pdf` receives `user_input` + a `pdf` upload and runs the execution including the file path in the prompt.
- **Frontend (UI)**: `front/`
- **Vector DB / storage**: Qdrant (via `docker-compose.yaml`)
- **Local models**: Ollama (via `docker-compose.yaml`, when enabled/configured)

## Requirements

- **Python 3.11+**
- **Node.js 18+** (for the UI)
- (Optional) **Docker + Docker Compose** (to run the full stack with Qdrant/Ollama/UI)

## Configuration

### Environment variables

This project uses `.env`. The backend reads:

- **`API_KEY`**: your provider/LLM key (mapped internally to `OPENAI_API_KEY` at runtime)

Example (create a `.env` file at the repo root):

```env
API_KEY=your_key_here
```

### Runtime config

`config.yaml` controls settings such as:

- `USE_OLLAMA` (enable/disable Ollama usage)
- `MODEL`
- `TIMEOUT`, `TEMPERATURE`, `MAX_RETRIES`, `MAX_ITERATIONS`
- `QDRANT` and `OLLAMA` hosts

## Running the project

### Option A) Docker Compose (recommended)

From the repository root:

```bash
docker compose up --build
```

Default services:

- **API**: `http://localhost:8000`
- **Qdrant**: `http://localhost:6333`
- **UI**: `http://localhost:5173` (or `http://localhost:8080`, depending on the container)

### Option B) Local run (no Docker)

#### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

API at `http://localhost:8000`.

#### Frontend

```bash
cd front
npm install
npm run dev
```

UI at `http://localhost:5173`.

## Using the API

### Execute a request

```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{"message":"Describe the goal and generate a plan to review my paper references."}'
```

### Execute with a PDF (upload)

```bash
curl -X POST "http://localhost:8000/execute-with-pdf" \
  -F "user_input=Extract the references and generate a BibTeX." \
  -F "pdf=@./pdfs/your_file.pdf"
```

## Repository structure

- `main.py`: FastAPI app (endpoints and bootstrap)
- `src/`: agents, entities and utilities
- `front/`: React UI (Vite + TS + shadcn/ui)
- `tests/`: tests and execution helpers
- `pdfs/`: uploaded/stored PDFs
- `plans/`: plan outputs (depending on configuration)
- `docker-compose.yaml`: stack (API + Qdrant + Ollama + UI)

## Tests

Frontend:

```bash
cd front
npm test
```

(If there are backend tests, they live under `tests/` and may depend on external services depending on the workflow.)

## License

See `LICENSE`.

