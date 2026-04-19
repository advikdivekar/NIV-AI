"""Firestore integration — save/load reports. Graceful if Firebase not configured."""
from __future__ import annotations
import logging, os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)
_db = None
_initialized = False


def _init():
    global _db, _initialized
    if _initialized:
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")
        if project_id and private_key and client_email:
            cred_dict = {"type": "service_account", "project_id": project_id,
                         "private_key": private_key.replace("\\n", "\n"),
                         "client_email": client_email, "token_uri": "https://oauth2.googleapis.com/token"}
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Certificate(cred_dict))
            _db = firestore.client()
            logger.info("Firestore connected")
        else:
            logger.warning("Firebase credentials not set — reports will not persist")
    except Exception as e:
        logger.warning("Firestore init failed: %s", e)
    _initialized = True


async def save_report(user_id: str, report: dict, raw_input: dict) -> Optional[str]:
    _init()
    if _db is None:
        return None
    try:
        doc = {"user_id": user_id, "verdict": report.get("verdict"), "confidence_score": report.get("confidence_score"),
               "verdict_reason": report.get("verdict_reason"), "property_location": raw_input.get("property", {}).get("location_area", ""),
               "property_price": raw_input.get("property", {}).get("property_price", 0),
               "report": report, "input": raw_input, "created_at": datetime.now(timezone.utc).isoformat()}
        ref = _db.collection("reports").document()
        ref.set(doc)
        return ref.id
    except Exception as e:
        logger.error("Save report failed: %s", e)
        return None


async def get_report(report_id: str) -> Optional[dict]:
    _init()
    if _db is None:
        return None
    try:
        doc = _db.collection("reports").document(report_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None
    except Exception as e:
        logger.error("Get report failed: %s", e)
        return None


async def list_reports(user_id: str, limit: int = 20) -> list:
    _init()
    if _db is None:
        return []
    try:
        docs = (_db.collection("reports").where("user_id", "==", user_id)
                .order_by("created_at", direction="DESCENDING").limit(limit).stream())
        return [{"id": d.id, "verdict": d.to_dict().get("verdict"), "property_location": d.to_dict().get("property_location"),
                 "created_at": d.to_dict().get("created_at")} for d in docs]
    except Exception as e:
        logger.error("List reports failed: %s", e)
        return []
