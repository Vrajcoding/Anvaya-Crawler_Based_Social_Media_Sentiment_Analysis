from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from storage.db_client import db

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("")
def get_alerts(status: Optional[str] = Query("all")):
    return db.get_alerts(status=status)

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    alert = db.update_alert_status(alert_id, "acknowledged")
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    alert = db.update_alert_status(alert_id, "resolved")
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
