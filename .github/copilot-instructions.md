# Copilot Onboarding Instructions for DeerFlow

Use this file as the default operating guide for this repository. Follow it first, and only search the codebase when this file is incomplete or incorrect.

## 1) Repository Summary

DeerFlow is currently a backend-focused repository (project was trimmed).

- Backend: Python 3.12, LangGraph agent runtime + FastAPI gateway.
- Skills: local skills directory at repo root.
- Root currently keeps minimal files: `README.md`, `config.yaml`, `backend/`, `skills/`, `.github/`.

## 2) Runtime and Toolchain Requirements

- Python `>=3.12`
- `uv`

Run commands from `backend/` unless explicitly stated otherwise.

## 3) Build/Test/Lint/Run - Current Command Sequences

### A. Install dependencies

From `backend/`:

```bash
uv sync --group dev
```

### B. Backend validation

From `backend/`:

```bash
uv run ruff check .
uv run pytest
```

### C. Start services (manual)

From `backend/`, use separate terminals.

Gateway startup:

```bash
PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001
```

Agent startup:

```bash
uv run langgraph dev --no-browser --no-reload --n-jobs-per-worker 10
```

Behavior:

- Gateway listens on `8001`.
- LangGraph dev server runs without browser auto-open and without reload.

## 4) Command Order That Minimizes Failures

For local code changes, use this order:

1. `cd backend && uv sync --group dev`
2. `cd backend && uv run ruff check .`
3. `cd backend && uv run pytest`
4. Start runtime services only when needed:
   - `cd backend && PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001`
   - `cd backend && uv run langgraph dev --no-browser --no-reload --n-jobs-per-worker 10`

## 5) Project Layout and Architecture (High-Value Paths)

Root-level:

- `README.md`
- `config.yaml`
- `.github/copilot-instructions.md`
- `backend/`
- `skills/`

Backend core:

- `backend/app/gateway/` - FastAPI gateway app and routers
- `backend/packages/harness/deerflow/agents/` - lead agent, middlewares, memory
- `backend/packages/harness/deerflow/sandbox/` - sandbox provider + tools
- `backend/packages/harness/deerflow/subagents/` - subagent registry/execution
- `backend/packages/harness/deerflow/mcp/` - MCP integration
- `backend/langgraph.json` - LangGraph graph entrypoint
- `backend/pyproject.toml` - backend dependencies
- `backend/ruff.toml` - lint policy

## 6) Pre-Checkin / Validation Expectations

Before submitting backend changes, run at minimum:

- `cd backend && uv run ruff check .`
- `cd backend && uv run pytest`

If touching runtime boot paths (`backend/app/gateway/*`, `backend/langgraph.json`, agent factories), also verify both startup commands run successfully.

## 7) Non-Obvious Dependencies and Gotchas

- Gateway startup requires `PYTHONPATH=.` from `backend/`.
- LangGraph dev is expected to run with `--no-browser --no-reload --n-jobs-per-worker 10` in this trimmed setup.
- This repository no longer assumes root `Makefile`, frontend, docker dev stack, or nginx unified endpoint.

## 8) Root Inventory (quick reference)

Important root entries:

- `.github/`
- `backend/`
- `skills/`
- `README.md`
- `config.yaml`

## 9) Instruction Priority

Trust this onboarding guide first.

Only do broad repo searches when:

- you need implementation details not listed here,
- startup/lint/test commands in this file fail,
- or repository structure has changed again.