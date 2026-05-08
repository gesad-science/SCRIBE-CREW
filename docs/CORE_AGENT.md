# Core Agent (orchestrator) and responsibilities

This document describes the **Core Agent** (`src/agents/core_agent/core_agent.py`): the orchestrator that builds a plan, validates it through governance, executes it by calling A2A agents via the Control Plane, and formats the final answer.

## Core Agent role

The Core Agent is the “brain” of the system. It:

- **does not perform domain work** (e.g. searching papers, generating BibTeX) directly
- creates a **structured execution plan**
- requires **governance validation** before executing any step
- executes the plan by calling external agents (A2A) via `call_agent`

## Main structure

File: `src/agents/core_agent/core_agent.py`.

Class: `CoreAgent`.

Key points:

- loads configuration via `SystemConfig()`
- keeps a small conversation window (`deque(maxlen=5)`)
- instantiates a CrewAI `Agent` (`self.core_orchestrator_agent`)
- builds a sequential `Crew` with 5 fixed tasks

## Core Agent tools (what it can do)

File: `src/agents/core_agent/tools.py`.

Most important tools used by the Core Agent:

- **Planning and governance**
  - `get_agents`: list alive agents (via Control Plane)
  - `delegate_to_governance` / `delegate_to_governance_plan`: validate the plan (Gov Agent)
  - `save_plan`: persist the approved plan into `plans/`
  - `get_similar_plans`: attempt to reuse validated plans (Execution Memory)

- **Execution (external calls)**
  - `get_agent_names`: return available A2A agent names
  - `call_agent`: `POST http://scribe-control-plane:7000/call`

- **Memory**
  - `save_pdf_to_system_memory`: index a PDF into Qdrant (`system_memory`)

There are also “direct delegates” (running CrewAI locally without A2A), such as:

- `delegate_to_reference_finder`
- `delegate_to_bibtex_generator`
- `delegate_to_validator`
- `delegate_to_download_agent`
- `delegate_to_rag_agent`

In the **main Docker Compose pipeline**, the expected path for distributed execution is **Control Plane + A2A** via `call_agent`.

## The 5 pipeline phases (sequential tasks)

The Core Agent runs `Crew(..., process=Process.sequential)` with:

### 1) Context understanding

Goal:

- treat the current request as part of a conversation
- prioritize the last 5 messages (`recent_context`)

Output:

- an “enriched” user request for downstream steps

### 2) Pre-plan pipeline

Goals:

- **detect file paths** in the input (e.g. `ARTICLE PATH: pdfs/...`) and call `save_pdf_to_system_memory` when present
- attempt **plan reuse** via `get_similar_plans`

Important note:

- this task’s contract returns something only if a reusable plan is found; otherwise the system continues to generate a new plan.

### 3) Plan task (plan creation)

Goal:

- build a strict JSON plan that follows this schema:

```json
{
  "plan_json": {
    "plan": [
      {
        "agent": "the agent responsible",
        "action": "the action that must be done",
        "input": "the input that the responsible agent needs to perform the action"
      }
    ]
  }
}
```

Key rules:

- only include “available” agents (obtained via `get_agents`)
- **validate** with governance (`delegate_to_governance`) and iterate until approved
- only after approval, persist with `save_plan`

### 4) Execution task (plan execution)

Goal:

- fetch available names via `get_agent_names`
- execute each step by calling `call_agent(agent_name, input_data)` **in order**
- collect outputs (including errors) and use them in the final response

In Docker Compose, `call_agent` uses the Control Plane endpoint:

- `POST http://scribe-control-plane:7000/call`

### 5) Post-execution task (formatting)

Goal:

- return a clear final answer based only on executed outputs
- optionally generate a Markdown table when comparison/summary fits

## Core Agent input and output

Input:

- `CoreAgent.orchestrate(user_input: str)`

Output:

- CrewAI kickoff result object
- the API (`tests/run_execution.py`) returns `result.raw`

## Where the Core Agent is called (product API)

File: `main.py`.

- `POST /execute` → `run_execution(core, req.message)` → `core.orchestrate(...)`
- `POST /execute-with-pdf` saves the PDF and appends `ARTICLE PATH: <path>` to the input

## Structural dependencies

- **Control Plane** must be reachable at `http://scribe-control-plane:7000`
- **A2A agents** must be reachable from the Control Plane at `http://scribe-api:<port>`
- **Qdrant** must be reachable (memory / RAG / PDF indexing)
- **Ollama** must be reachable (embeddings/models, per `SystemConfig`)

## Related docs

- Main pipeline: `docs/PIPELINE_PRINCIPAL.md`
- Control Plane: `docs/CONTROL_PLANE.md`
- A2A agents: `docs/AGENTES_A2A.md`
