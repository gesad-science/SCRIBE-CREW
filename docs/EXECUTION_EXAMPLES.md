# Execution examples (high-level logs)

This document is meant to collect **high-level execution logs** for the main SCRIBE pipeline.

Goals:

- make it easy to understand “what happened” across Core → Control Plane → A2A agents
- provide copy/pasteable traces for debugging and demos
- document common flows (metadata + BibTeX, PDF download + indexing + RAG)

## Conventions

- Redact sensitive data (API keys, personal data).
- Prefer **high-level** logs (what step ran, which agent was called, and summary of outputs).
- Include timestamps when available.

## Example 1: metadata → BibTeX → validation

Input (Frontend / `POST /execute`):

```
Find metadata and BibTeX for: Attention is All You Need
```

High-level trace:

```
[API] /execute
[CORE] context_understanding
[CORE] pre_plan (plan reuse: Not found)
[CORE] plan_task (governance: approved)
[CORE] execution_task
  [CP] GET /agents -> 5 agents alive
  [CP] POST /call -> reference_finder_agent
  [A2A] reference_finder -> found metadata (title/authors/year/doi)
  [CP] POST /call -> bibtex_generator_agent
  [A2A] bibtex -> fetched BibTeX via DOI, validated OK
  [CP] POST /call -> reference_validator_agent
  [A2A] validator -> valid (no critical issues)
[CORE] post_execution -> formatted answer
```

## Example 2: PDF download → system memory indexing → RAG QA

Input (Frontend / `POST /execute-with-pdf`):

```
Summarize the methodology section and list main contributions.
```

High-level trace:

```
[API] /execute-with-pdf (saved: pdfs/<file>.pdf)
[CORE] context_understanding
[CORE] pre_plan
  [CORE] detected ARTICLE PATH -> save_pdf_to_system_memory -> indexed chunks
[CORE] plan_task (governance: approved)
[CORE] execution_task
  [CP] POST /call -> hierarchical_rag_agent
  [A2A] rag -> answered with citations from retrieved chunks
[CORE] post_execution -> formatted answer
```
