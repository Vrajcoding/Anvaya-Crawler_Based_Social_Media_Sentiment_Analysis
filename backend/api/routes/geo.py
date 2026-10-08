"""
api/routes/geo.py
Geo/Map API endpoints: district stats for heat-map and risk index.
"""

from fastapi import APIRouter, Query
from ingest.geo_tagger import geo_tagger
from analytics.risk_index import risk_index
from storage.db_client import db

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/districts")
def get_district_stats(limit: int = Query(200)):
    """Return per-district post stats for map heat-map rendering."""
    posts = db.get_posts(limit=limit)["items"]
    return {
        "districts": geo_tagger.get_district_stats(posts),
    }


@router.get("/risk-index")
def get_risk_index():
    """Return the Escalation Risk Index for all Gujarat districts."""
    posts = db.get_posts(limit=500)["items"]
    risk_index.update(posts)
    return {
        "risk_index": risk_index.get_index(),
        "updated_at": getattr(risk_index, "_last_updated", None),
    }


@router.get("/risk-index/{district}")
def get_district_risk(district: str):
    """Return ERI for a single district."""
    entry = risk_index.get_district_eri(district)
    if not entry:
        return {"district": district, "eri": 0, "trend": "stable", "components": {}}
    return entry
