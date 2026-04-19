"""Reports endpoints — save, retrieve, list analysis reports."""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from backend.firebase.firestore import get_report, list_reports, save_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.post("/reports")
async def create_report(body: dict, x_user_id: Optional[str] = Header(None)):
    user_id = x_user_id or "anonymous"
    report_data = body.get("report")
    if not report_data:
        raise HTTPException(status_code=422, detail="Missing report in body")
    doc_id = await save_report(user_id, report_data, body.get("input", {}))
    return {"id": doc_id, "saved": doc_id is not None}


@router.get("/reports")
async def get_reports(x_user_id: Optional[str] = Header(None), limit: int = 20):
    user_id = x_user_id or "anonymous"
    return {"reports": await list_reports(user_id, limit=min(limit, 50))}


@router.get("/reports/{report_id}")
async def get_single_report(report_id: str):
    report = await get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
