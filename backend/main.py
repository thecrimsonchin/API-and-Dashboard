"""FastAPI app: exposes Acumatica data as JSON and serves the dashboard.

Endpoints
  GET /                      -> dashboard (static frontend)
  GET /api/health            -> liveness + which Acumatica instance is configured
  GET /api/open-po-lines     -> open purchase order lines
  GET /api/purchase-receipts -> recent purchase receipts
  GET /api/inventory-history -> inventory transaction history (via Generic Inquiry)

NOTE: Acumatica entity/field names below reflect the standard Default endpoint
for 2024 R1. Customized instances may rename or add fields; adjust the
$select / $expand / filters here to match your tenant.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .acumatica import AcumaticaClient, AcumaticaError
from .config import get_settings

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.acumatica = AcumaticaClient(settings)
    try:
        yield
    finally:
        await app.state.acumatica.logout()


app = FastAPI(title="Acumatica API & Dashboard", lifespan=lifespan)


def _field(record: dict[str, Any], name: str) -> Any:
    """Unwrap an Acumatica contract field: {"value": ...} -> ...."""
    val = record.get(name)
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


@app.exception_handler(AcumaticaError)
async def _acumatica_error_handler(_request, exc: AcumaticaError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.get("/api/health")
async def health() -> dict[str, Any]:
    s = app.state.settings
    return {
        "status": "ok",
        "instance": s.base_url,
        "endpoint_version": s.endpoint_version,
        "tenant": s.tenant,
    }


@app.get("/api/open-po-lines")
async def open_po_lines(top: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    """Open purchase orders, flattened to their open lines.

    Filters POs to Status = 'Open' and expands Details. Lines are returned
    with the parent PO context so the dashboard can show order + line together.
    """
    client: AcumaticaClient = app.state.acumatica
    data = await client.get_entity(
        "PurchaseOrder",
        params={
            "$filter": "Status eq 'Open'",
            "$expand": "Details",
            "$top": top,
        },
    )
    rows: list[dict[str, Any]] = []
    for po in data:
        order_nbr = _field(po, "OrderNbr")
        vendor = _field(po, "VendorID")
        po_date = _field(po, "Date")
        for line in po.get("Details", []) or []:
            rows.append(
                {
                    "orderNbr": order_nbr,
                    "vendorID": vendor,
                    "date": po_date,
                    "lineNbr": _field(line, "LineNbr"),
                    "inventoryID": _field(line, "InventoryID"),
                    "description": _field(line, "LineDescription"),
                    "orderQty": _field(line, "OrderQty"),
                    "openQty": _field(line, "OpenQty"),
                    "uom": _field(line, "UOM"),
                    "unitCost": _field(line, "UnitCost"),
                }
            )
    return rows


@app.get("/api/purchase-receipts")
async def purchase_receipts(top: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    """Recent purchase receipts (header level)."""
    client: AcumaticaClient = app.state.acumatica
    data = await client.get_entity(
        "PurchaseReceipt",
        params={
            "$select": "ReceiptNbr,Type,Date,VendorID,Status,ControlQty,Hold",
            "$top": top,
            "$orderby": "Date desc",
        },
    )
    return [
        {
            "receiptNbr": _field(r, "ReceiptNbr"),
            "type": _field(r, "Type"),
            "date": _field(r, "Date"),
            "vendorID": _field(r, "VendorID"),
            "status": _field(r, "Status"),
            "controlQty": _field(r, "ControlQty"),
        }
        for r in data
    ]


@app.get("/api/inventory-history")
async def inventory_history(top: int = Query(200, ge=1, le=2000)) -> list[dict[str, Any]]:
    """Inventory transaction history, read from a Generic Inquiry (OData).

    There is no standard Default-endpoint entity for inventory history, so this
    reads the GI named by ACUMATICA_INVENTORY_HISTORY_GI. Column names depend on
    how that GI is defined; the dashboard renders whatever columns come back.
    """
    client: AcumaticaClient = app.state.acumatica
    gi = app.state.settings.inventory_history_gi
    if not gi:
        raise HTTPException(
            status_code=400,
            detail="ACUMATICA_INVENTORY_HISTORY_GI is not configured.",
        )
    rows = await client.get_generic_inquiry(gi, params={"$top": top})
    return rows


# Serve the dashboard at "/" (mounted last so it doesn't shadow /api/*).
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
