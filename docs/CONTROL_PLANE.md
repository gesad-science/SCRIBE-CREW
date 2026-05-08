# Control Plane (A2A discovery, registry, and routing)

This document describes the **Control Plane** (service `control_plane` in `docker-compose.yaml`). It is responsible for:

- discovering alive A2A agents (via `agent-card.json`)
- maintaining an in-memory registry
- providing a simple HTTP API to list and call agents by name
- forwarding messages to A2A agents using JSON-RPC (`message/send`)

## Why A2A + Control Plane matters (decoupling)

The combination of **A2A agents** and the **Control Plane** makes the system **language- and framework-agnostic**:

- an agent can be implemented in **any language** (Python, Node, Go, Rust, Java, etc.)
- it can use **any tech stack** (FastAPI, Express, Spring, gRPC gateway, serverless, etc.)
- as long as it exposes the **A2A HTTP contract** (Agent Card + JSON-RPC `message/send`)

Because the Core Agent calls agents **by name** through the Control Plane, the agent implementation is **fully decoupled** from the orchestration code.

## Where it lives

- Code:
  - `src/control_plane/main.py` (FastAPI HTTP API)
  - `src/control_plane/control_plane.py` (discovery/registry/call logic)
- Container: `scribe-control-plane`
- Port: `7000` (inside the Docker Compose network)

## Control Plane HTTP API

File: `src/control_plane/main.py`.

### `GET /agents`

Returns a list of “alive” agents with metadata extracted from the Agent Card:

- `name`
- `description`
- `skills`
- `url`

### `POST /call`

Body:

```json
{
  "agent_name": "string",
  "input_data": "dict or string"
}
```

Behavior:

- finds the agent in the registry (with fuzzy match)
- sends `input_data` as text to the A2A agent via JSON-RPC
- returns `{"status":"ok","result":"..."}` (or `status=error`)

### `POST /refresh`

Forces a re-scan across the port range and replaces the current registry.

## Discovery: how the registry is built

File: `src/control_plane/control_plane.py`.

### Strategy

- scans a port range (default `9000..9999`)
- for each port, tries:
  - `GET http://<host>:<port>/.well-known/agent-card.json` with a short timeout (`0.5s`)
- when status is 200:
  - reads `card.name`, `card.description`, `card.skills`
  - sanitizes the name into a registry key (lowercase + `_`)
  - stores:
    - `url`: `http://<host>:<port>`
    - `card`: full agent card JSON
    - `port`: discovered port

### Host used in Docker Compose

In `src/control_plane/main.py`, the Control Plane is created as:

- `cp = ControlPlane(host="scribe-api")`

This means discovery and routing assume A2A agents are reachable via the Compose DNS name `scribe-api` (the `api` container).

If you run an agent outside the `api` container (or outside Compose entirely), the Control Plane must be able to reach it via `host:port` and the discovery host configuration must reflect that.

### Startup delay

In `ControlPlane.__init__` there is:

- `time.sleep(165)`

Practical goal:

- wait for `scribe-api` to bring up `supervisord` and expose A2A agents before scanning ports

This affects “time until ready” depending on environment speed.

## Routing: how a call is executed

### Fuzzy match on agent name

Method `_find_best_agent`:

- returns exact match when available
- otherwise uses `difflib.get_close_matches(..., cutoff=0.5)` to pick the closest name

This reduces friction, but can route to an unintended agent if names are ambiguous.

### JSON-RPC payload (A2A)

Method `call_agent` builds:

- `method`: `"message/send"`
- `params.message.role`: `"user"`
- `params.message.parts[0].kind`: `"text"`
- `params.message.parts[0].text`: input (string)
- `params.message.messageId`: UUID

And performs:

- `POST <agent_url>` with timeout `1200s`

On response:

- if `result.message.parts[0].text` is present, that is returned as `result`
- otherwise, the whole `result` object is returned

## How the Core Agent uses the Control Plane

File: `src/agents/core_agent/tools.py`.

- `get_agents()` → `GET http://scribe-control-plane:7000/agents`
- `get_agent_names()` turns the list into `["name1","name2",...]`
- `call_agent(agent_name, input_data)` → `POST http://scribe-control-plane:7000/call`

In other words:

- the Core Agent does **not** need to know A2A ports/URLs
- it works with names, and the Control Plane provides service discovery and routing

## Related docs

- Main pipeline: `docs/PIPELINE_PRINCIPAL.md`
- A2A agents: `docs/AGENTES_A2A.md`
- Core Agent: `docs/CORE_AGENT.md`
