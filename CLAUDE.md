# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A read-only integration that pulls data from **Acumatica ERP** (build
`24.106.0018`, i.e. 2024 R1) via its REST API and presents it on a dashboard.
Current views: **open PO lines**, **purchase receipts**, and **inventory
transaction history**. Despite the original README wording ("deploy a model"),
there is no ML model here — the "API" is a thin FastAPI layer in front of
Acumatica.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Acumatica instance + credentials

# Run (serves API + dashboard on one port)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The dashboard is at `/`; JSON is under `/api/*`. There is **no test suite, linter,
or CI configured yet** — add them here when introduced (and document how to run a
single test once a framework exists).

## Architecture

Single FastAPI process serves both the JSON API and the static dashboard, so
there is no separate frontend build or dev server.

- `backend/config.py` — `Settings` dataclass loaded from env (`.env` in dev).
  Derives the three Acumatica base URLs: contract `entity_url`, `auth_url`, and
  `odata_url`. `ACUMATICA_ENDPOINT_VERSION` defaults to `24.200.001` (the 2024 R1
  Default endpoint).
- `backend/acumatica.py` — `AcumaticaClient`, a shared async `httpx` client.
  Uses **cookie/session auth**: lazily POSTs to `/entity/auth/login`, reuses the
  session cookie, transparently re-logs-in once on a 401, and logs out on
  shutdown to release the license seat. `get_entity()` hits the contract REST
  endpoint; `get_generic_inquiry()` hits OData and unwraps the `value` array.
- `backend/main.py` — FastAPI app. Owns the client lifecycle via `lifespan`
  (created at startup on `app.state.acumatica`, logged out at shutdown). Each
  `/api/*` route shapes raw Acumatica records into flat JSON; `_field()` unwraps
  Acumatica's `{"value": ...}` field envelopes. The static frontend is mounted at
  `/` **last** so it doesn't shadow `/api/*`.
- `frontend/` — static `index.html` + `styles.css` + `app.js`. `app.js` fetches
  one `/api/*` view and renders rows as a table, deriving columns from the row
  keys (so it adapts to whatever shape the backend returns). Tabs switch views;
  optional 30s auto-refresh provides the "real-time" behaviour.

Data flow: `app.js` → `/api/<view>` → `AcumaticaClient` → Acumatica REST/OData.

## Acumatica specifics (important)

- Target build is `24.106.0018` (2024 R1). Keep REST usage compatible with that
  version; the Default endpoint version is `24.200.001` unless the instance says
  otherwise (**System > Integration > Web Service Endpoints**).
- **Open PO lines** come from the `PurchaseOrder` entity filtered to
  `Status eq 'Open'` with `$expand=Details`; lines are flattened with parent PO
  context. **Purchase receipts** come from the `PurchaseReceipt` entity.
- **Inventory history is NOT a standard Default-endpoint entity.** It is read
  from a **Generic Inquiry** exposed via OData, named by
  `ACUMATICA_INVENTORY_HISTORY_GI`. If inventory history is empty/erroring, the
  GI almost certainly needs to be created/exposed in Acumatica first (base it on
  the Inventory Transaction History inquiry, IN405000).
- Entity and field names in `main.py` assume the **stock** Default endpoint.
  Customized tenants may rename or add fields — adjust `$select`/`$expand`/
  filters to match the actual instance rather than assuming the defaults hold.

## Conventions

- All Acumatica access is **read-only** today (GET only). Adding writes (POST/PUT)
  changes the risk profile — confirm intent before introducing them.
- Secrets live only in `.env` (gitignored); never hardcode the instance URL or
  credentials. `.env.example` is the documented contract for required vars.
- **Org standard for Excel exports:** if any feature exports data to Excel,
  calculated fields must be written as live Excel formulas (not pre-computed
  static values). No Excel export exists yet — honour this when one is added.

## Git workflow

- Default branch: `main`.
- Open a pull request only when explicitly requested.
