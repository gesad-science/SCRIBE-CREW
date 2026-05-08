# Main pipeline (end-to-end view)

This document describes **only the main SCRIBE pipeline**: how the **Frontend** talks to the **API** (`main.py`), how the **Core Agent** orchestrates **plan → governance → execution**, and how it integrates with **A2A agents** through the **Control Plane**, all running with **Docker Compose** and **supervisord**.

## What “main pipeline” means

End-to-end happy path:

1. The user interacts with the **Frontend** (chat, optionally attaching a PDF).
2. The Frontend calls the **API** (container `scribe-api`) at:
   - `POST /execute` (text)
   - `POST /execute-with-pdf` (text + PDF file)
3. The API delegates to the **Core Agent** (`src/agents/core_agent/core_agent.py`) via `CoreAgent.orchestrate()`.
4. The Core Agent runs a fixed chain of tasks (CrewAI, `Process.sequential`):
   - **Context understanding**
   - **Pre-plan pipeline** (plan reuse and/or PDF persistence)
   - **Plan** (build a JSON execution plan)
   - **Governance validation** (approve/reject the plan)
   - **Execution** (call A2A agents via the Control Plane)
   - **Post-execution formatting**
5. During execution, the Core Agent calls the **Control Plane** (`scribe-control-plane`) to:
   - discover which A2A agents are alive (`GET /agents`)
   - call a specific agent (`POST /call`)
6. The Control Plane forwards the call to the A2A agent using **JSON-RPC** with `method=message/send`.
7. Each A2A agent runs a CrewAI `Crew` with its “domain” agent (e.g. `reference_agent`, `bibtex_agent`, etc.) and returns a text response.

## Components and responsibilities (high level)

- **Frontend** (`front/`): chat UI (text + PDF upload) and response rendering (includes simple BibTeX parsing).
- **Main API** (`main.py`): product HTTP endpoints and `CoreAgent` initialization.
- **Core Agent** (`src/agents/core_agent/core_agent.py`): orchestration pipeline (planning + governance + execution).
- **Control Plane** (`src/control_plane/*`): discovery/registry + routing calls to A2A agents.
- **A2A agents** (`src/agents/a2a/*`): A2A adapters (JSON-RPC + agent-card) wrapping CrewAI domain agents.
- **Infra**: `docker-compose.yaml` (service topology) + `supervisord.conf` (runs API + A2A agents in the same `api` container) + `qdrant` (vector memory) + `ollama` (embeddings/models).

## Docker Compose orchestration

File: `docker-compose.yaml`.

Services relevant to the main pipeline:

- **`api`** (container `scribe-api`)
  - Build: `Dockerfile`
  - Port: `8000:8000`
  - Volumes:
    - `./src:/app/src`
    - `./pdfs:/app/pdfs`
    - `./plans:/app/plans`
  - Depends on: `qdrant`, `ollama`
  - Note: runs `supervisord` and starts **the API** plus **all A2A agents** in the same runtime.

- **`control_plane`** (container `scribe-control-plane`)
  - Build: `Dockerfile.controlplane`
  - Exposes `7000` inside the Compose network (not published to the host in the current compose file)
  - Depends on: `qdrant`, `ollama`, `api`

- **`qdrant`** (container `scribe-qdrant`)
  - Port: `6333:6333`
  - Persistence: `qdrant_storage`

- **`ollama`** (container `scribe-ollama`)
  - Build: `Dockerfile-ollama`
  - Pulls `nomic-embed-text` on startup
  - Persistence: `ollama_models`

- **`front`** (container `scribe-front`)
  - Build: `Dockerfile-front`
  - Ports: `8080:8080` (Vite is configured for `8080`; `5173:5173` is also mapped)

## supervisord: which processes start

File: `supervisord.conf`.

The `api` container starts multiple processes:

- `program:main-api`: `python main.py` (FastAPI at `:8000`)
- A2A agents (each is a Uvicorn Starlette A2A server):
  - **BibTeX**: `:9994`
  - **Reference Finder**: `:9995`
  - **RAG**: `:9996`
  - **Download**: `:9997`
  - **Validator**: `:9998`

These ports are exposed by the container (see `Dockerfile`), and the Control Plane discovers them via `/.well-known/agent-card.json`.

## Product HTTP contracts

File: `main.py`.

- `POST /execute`
  - Body: `{ "message": "..." }`
  - Runs the Core Agent pipeline and returns the CrewAI `result.raw` (text).

- `POST /execute-with-pdf`
  - multipart form:
    - `user_input` (text)
    - `pdf` (file)
  - Saves the PDF into `pdfs/<filename>`
  - Appends `ARTICLE PATH: <path>` to the prompt (so the Core can trigger PDF indexing)

## How the Core Agent chains phases

File: `src/agents/core_agent/core_agent.py`.

The `CoreAgent` creates a single CrewAI `Agent` with orchestration tools and runs a sequential `Crew` with 5 tasks:

- **Context understanding**: enriches intent using the last 5 messages.
- **Pre-plan pipeline**:
  - detects file paths in the request and calls `save_pdf_to_system_memory` (Qdrant indexing).
  - attempts plan reuse via `get_similar_plans`.
- **Plan task**:
  - builds a strict JSON plan (`plan_json.plan[]` schema).
  - validates with `delegate_to_governance`.
  - persists with `save_plan` (creates `plans/plan_<timestamp>.pln`).
- **Execution task**:
  - lists agents via `get_agent_names` (through the Control Plane).
  - executes each step by calling `call_agent(agent_name, input_data)`.
- **Post execution task**: formats the final answer (may include a Markdown table).

## Control Plane: discovery and routing

Files: `src/control_plane/main.py` and `src/control_plane/control_plane.py`.

Control Plane endpoints:

- `GET /agents`: list alive A2A agents (name, description, skills, url)
- `POST /call`: route a request to a named A2A agent (with fuzzy match)
- `POST /refresh`: force a registry re-scan

Discovery:

- the `ControlPlane` scans a port range (default `9000–9999`) for:
  - `http://<host>:<port>/.well-known/agent-card.json`
- when found, it sanitizes the agent name and registers url/port/card.

Routing:

- converts `input_data` to text (dict → JSON string).
- builds a JSON-RPC `message/send` payload and POSTs to the agent URL.
- extracts `result.message.parts[0].text` when available.

## How “memory” enters the flow

Key points:

- **PDF indexing**: `save_pdf_to_system_memory(pdf_path)` extracts text, chunks, and stores it in Qdrant `system_memory`.
- **RAG**: the RAG agent queries private memory first (`rag_private_memory`); if missing, it reads from `system_memory` and caches into the private collection.

## Ports and important names (summary)

- **Main API**: `scribe-api:8000`
- **Control Plane**: `scribe-control-plane:7000`
- **A2A agents** (inside `scribe-api`):
  - `:9994` validator
  - `:9995` bibtex
  - `:9996` download
  - `:9997` rag
  - `:9998` reference_finder
- **Qdrant**: `:6333`
- **Ollama**: `:11434`
- **Frontend**: `:8080` (Vite)

## Next docs

- Core Agent: `docs/CORE_AGENT.md`
- A2A agents: `docs/AGENTES_A2A.md`
- Control Plane: `docs/CONTROL_PLANE.md`
- Frontend: `docs/FRONTEND.md`
