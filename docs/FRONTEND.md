# Frontend (chat UI) and API integration

This document describes the **Frontend** (`front/`): main routes, chat components, and how it integrates with the SCRIBE API.

## Stack and runtime

- Stack: **Vite + React + TypeScript + Tailwind + shadcn-ui**
- Dev server (container `scribe-front`):
  - `Dockerfile-front` runs: `npm run dev -- --host`
  - `vite.config.ts` sets port `8080` by default
- Docker Compose ports: `8080:8080` (and also `5173:5173`, although Vite is configured for `8080`)

## Routes

File: `front/src/App.tsx`.

- `/`: landing page (`front/src/pages/Index.tsx`)
- `/chat`: main chat (`front/src/pages/Chat.tsx`)

## Chat flow (main path)

File: `front/src/pages/Chat.tsx`.

Local state:

- `messages`: message history (`user` / `assistant`)
- `isLoading`: request loading state

Send behavior:

- `handleSend(message, pdf?)`
  - adds the user message to the timeline
  - calls:
    - `executeSimple(message)` when there is **no** PDF
    - `executeWithPdf(message, pdf)` when a PDF is attached
  - renders the response as:
    - string (if already a string)
    - pretty-printed JSON (`JSON.stringify(result, null, 2)`) otherwise
  - on error, shows a toast “Request error”

Note:

- The code imports `executeSimple`/`executeWithPdf` from `@/lib/api`, but that file is not present in the repository state. For documentation purposes, the expected backend contract is:
  - `executeSimple`: `POST /execute`
  - `executeWithPdf`: `POST /execute-with-pdf` (multipart)

## PDF upload in the chat

File: `front/src/components/ChatInput.tsx`.

Behavior:

- Allows sending text, PDF, or both.
- Enter sends; Shift+Enter adds a new line.
- When a PDF is selected, it shows an attachment “chip” with the filename and a remove button.

## Message rendering and BibTeX cards

File: `front/src/components/ChatMessage.tsx`.

Features:

- Renders text via `react-markdown`.
- Converts URLs into Markdown links (domain shown as label).
- Detects BibTeX blocks inside assistant responses (heuristic: starts with `@...{` and ends at balanced braces).
- When BibTeX is found:
  - shows a card with extracted fields (title/author/year/journal)
  - allows expanding to view full BibTeX
  - allows copying BibTeX to clipboard

## API integration (expected contract)

Backend API (container `scribe-api`) exposes on `:8000`:

- `POST /execute` with JSON body `{ "message": "..." }`
- `POST /execute-with-pdf` with multipart form:
  - `user_input` (text)
  - `pdf` (file)

The frontend should point to the correct host/port (in Compose dev, typically `http://localhost:8000` from the browser).

## Related docs

- Main pipeline: `docs/PIPELINE_PRINCIPAL.md`
- Core Agent: `docs/CORE_AGENT.md`
