from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import datetime

from storage.db_client import db_client
from analytics.incidents import incident_clusterer
from reports.brief_pdf import generate_incident_pdf

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("")
def get_incidents():
    """Dynamically cluster high-threat posts into incidents."""
    posts = db_client.get_posts(limit=1000)["items"]
    incidents = incident_clusterer.build_incidents(posts)
    return incidents

@router.post("/generate")
def generate_report(payload: Dict[str, Any]):
    posts = db_client.get_posts()["items"]
    incidents = incident_clusterer.build_incidents(posts)
    return {
        "status": "success",
        "report_id": f"rep_{int(datetime.datetime.utcnow().timestamp())}",
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "summary": "SentinelAI Threat & Incident Report",
        "total_posts_analyzed": len(posts),
        "total_incidents": len(incidents),
        "incidents": incidents
    }

@router.get("/{incident_id}/pdf")
def download_incident_pdf(incident_id: str):
    """Generates and downloads a PDF brief for a specific incident."""
    # Ensure incidents are up to date
    posts = db_client.get_posts(limit=1000)["items"]
    incident_clusterer.build_incidents(posts)
    
    incident = incident_clusterer.incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Get evidence posts
    evidence_ids = incident.get("evidence_posts", [])
    evidence_posts = [db_client.posts[pid] for pid in evidence_ids if pid in db_client.posts]
    
    pdf_buffer = generate_incident_pdf(incident, evidence_posts)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={incident_id}_brief.pdf"}
    )
