# A2A agents (Docker + supervisord) and capabilities

This document describes the **A2A (Agent-to-Agent) services** running under **supervisord** inside the `scribe-api` container, and the **capabilities of each agent** (what it does and when to use it).

## What A2A means in this project

Each A2A service under `src/agents/a2a/*`:

- exposes an HTTP endpoint that accepts **JSON-RPC** calls (`message/send`)
- publishes an **Agent Card** at `/.well-known/agent-card.json` (used by Control Plane discovery)
- wraps a CrewAI “domain” agent (e.g. `src/agents/reference_agent.py`)

In practice:

- the **Control Plane** discovers and calls A2A agents
- the **Core Agent** talks to the Control Plane (it does not call A2A agents directly)

## How they start (supervisord)

File: `supervisord.conf`.

Inside the `scribe-api` container, supervisor starts 5 A2A processes (Uvicorn + Starlette A2A):

- **BibTeX Agent** (A2A): `src/agents/a2a/a2a_bibtex.py` → port **9994**
- **Reference Finder Agent** (A2A): `src/agents/a2a/a2a_reference_finder.py` → port **9995**
- **RAG Agent** (A2A): `src/agents/a2a/a2a_rag.py` → port **9996**
- **Download Agent** (A2A): `src/agents/a2a/a2a_download.py` → port **9997**
- **Validator Agent** (A2A): `src/agents/a2a/a2a_validator.py` → port **9998**

Note:

- There is also a runner at `src/agents/a2a/run_agents.py`, but it calls `uvicorn.run(...)` sequentially (blocking) and **is not the main production mechanism** in Docker Compose. The main path is `supervisord`.

## A2A contract (discovery + call)

### Discovery (Agent Card)

Each A2A app creates an `AgentCard` (name, description, skills, interfaces), and the A2A server publishes:

- `GET /.well-known/agent-card.json`

The Control Plane uses this to:

- discover active agents (by scanning ports)
- list available skills/capabilities

### Call (JSON-RPC)

The Control Plane calls the agent base endpoint (e.g. `http://scribe-api:9998`) with a JSON-RPC payload:

- `method`: `"message/send"`
- `params.message.parts[0].text`: the input text (string)

Each A2A executor:

- extracts text from the first `part`
- creates a CrewAI `Task` using that input
- runs a `Crew(...).kickoff()`
- emits the result using `new_agent_text_message(...)`

## Capabilities by agent

### 1) Reference Finder Agent

- **A2A wrapper**: `src/agents/a2a/a2a_reference_finder.py`
- **Domain agent**: `src/agents/reference_agent.py`
- **Goal**: take a reference string (citation/bibliography/partial title) and return paper **metadata** (title, authors, year, URL, DOI/arXiv, sometimes BibTeX).
- **Main tools**:
  - `extract_identifiers_from_reference` (DOI/arXiv regex)
  - `guess_title_tool` (title heuristic)
  - `search_paper_by_title` and `search_by_topic` (Semantic Scholar)
- **Output**: JSON-as-text with `status=found|not_found` and `paper` (or `papers[]` for broad topics).
- **When to use**:
  - the user provides an incomplete reference
  - you need DOI/arXiv/URL to feed Download/BibTeX/Validator

### 2) BibTeX Generator Agent

- **A2A wrapper**: `src/agents/a2a/a2a_bibtex.py`
- **Domain agent**: `src/agents/bibtex_agent.py`
- **Goal**: produce a **valid BibTeX** entry from DOI/arXiv/metadata.
- **Main tools**:
  - `fetch_bibtex_from_doi`
  - `fetch_bibtex_from_arxiv`
  - `create_bibtex_manually` (fallback)
  - `validate_bibtex`
- **Output**: JSON-as-text with `bibtex`, `source` (`doi|arxiv|manual|provided`), and validation status.
- **When to use**:
  - you already have DOI/arXiv/metadata and want a citation export

### 3) Paper Downloader Agent

- **A2A wrapper**: `src/agents/a2a/a2a_download.py`
- **Domain agent**: `src/agents/download_agent.py`
- **Goal**: locate and **download the paper PDF** (so memory can be populated and RAG can answer questions grounded in the paper).
- **Main tools**:
  - `query_crossref_by_doi`
  - `query_unpaywall` (open access)
  - `query_arxiv` (build PDF URL)
  - `download_pdf`
- **Output**: JSON-as-text with `status` (`downloaded|not_available|failed`) and `file_path`.
- **When to use**:
  - before RAG, when the answer requires reading the paper content

### 4) Hierarchical RAG Agent

- **A2A wrapper**: `src/agents/a2a/a2a_rag.py`
- **Domain agent**: `src/agents/rag_agent.py`
- **Goal**: answer questions using **hierarchical memory** with strict grounding (no invented facts).
- **Memories**:
  - `rag_private_memory` (private cache)
  - `system_memory` (PDF-indexed chunks)
- **Main tool**:
  - `smart_retrieve_with_delimiter(query)`
    - checks private first; if missing, checks system and caches into private
- **Output**: JSON-as-text with `status=answered|not_found`, `answer`, and `sources_used[]`.
- **When to use**:
  - questions about the content of a specific paper/PDF
  - after indexing the PDF (via `save_pdf_to_system_memory`) and/or downloading it

### 5) Reference Validator Agent

- **A2A wrapper**: `src/agents/a2a/a2a_validator.py`
- **Domain agent**: `src/agents/validator_agent.py`
- **Goal**: validate **quality and consistency** between metadata and BibTeX.
- **Main tools**:
  - `check_metadata_completeness`
  - `check_bibtex_validity`
  - `cross_check_metadata_bibtex`
- **Output**: JSON-as-text with `validation_status` (`valid|invalid|warning`), issues, warnings, and recommendations.
- **When to use**:
  - before persisting/using generated references
  - for QA gates in the pipeline

## Operational notes

- **Ports**: the Control Plane scans `9000–9999` by default. Since agents run on `9994–9998`, they are discoverable.
- **Agent naming**: the Control Plane sanitizes names (lowercase + `_`) and also does **fuzzy matching** on calls (`difflib.get_close_matches`).
- **Timeout**: routing uses a large timeout (`1200s`) for long tasks (download, RAG).

## Where this fits in the pipeline

- Main pipeline: `docs/PIPELINE_PRINCIPAL.md`
- Control Plane: `docs/CONTROL_PLANE.md`
- Core Agent: `docs/CORE_AGENT.md`
