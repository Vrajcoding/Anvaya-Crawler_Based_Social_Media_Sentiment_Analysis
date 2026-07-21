from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from storage.db_client import db

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

@router.get("")
def get_watchlist():
    return db.get_watchlist()

@router.post("")
def add_watchlist_item(payload: Dict[str, Any]):
    val = payload.get("value")
    item_type = payload.get("type")
    if not val or not item_type:
        raise HTTPException(status_code=400, detail="Missing type or value")
    return db.add_watchlist_item(payload)

@router.delete("/{item_id}")
def delete_watchlist_item(item_id: str):
    success = db.delete_watchlist_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"status": "success", "id": item_id}
