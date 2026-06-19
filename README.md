# API-and-Dashboard

Pull data from **Acumatica ERP** (build 24.106.0018 / 2024 R1) via its REST API
and view it on a real-time dashboard. Current views: **open PO lines**,
**purchase receipts**, and **inventory transaction history**.

## Stack

- **Backend:** Python + FastAPI. Calls Acumatica's contract-based REST API
  (cookie/session auth) and exposes simplified JSON at `/api/*`.
- **Frontend:** static HTML/CSS/JS dashboard served by FastAPI (no Node build).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your Acumatica instance + credentials
```

## Run

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 for the dashboard. JSON endpoints live under `/api/`
(e.g. `/api/open-po-lines`, `/api/purchase-receipts`, `/api/inventory-history`,
`/api/health`).

## Acumatica notes

- The default REST endpoint version for 2024 R1 is `24.200.001`. Confirm yours
  under **System > Integration > Web Service Endpoints** and set
  `ACUMATICA_ENDPOINT_VERSION` accordingly.
- Open PO lines and purchase receipts use the standard `PurchaseOrder` and
  `PurchaseReceipt` entities of the Default endpoint.
- **Inventory history has no standard REST entity** — it is read from a
  **Generic Inquiry** exposed via OData. Create/expose a GI (e.g. based on the
  Inventory Transaction History inquiry, IN405000) and set
  `ACUMATICA_INVENTORY_HISTORY_GI` to its name.
