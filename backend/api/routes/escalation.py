from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/escalation", tags=["escalation"])

@router.get("/templates")
def get_escalation_templates(platform: str, post_id: str, author: str, url: str) -> Dict[str, Any]:
    """
    Feature 4.7: Pre-filled legal/takedown escalation templates.
    Generates ready-to-send emails/requests for Nodal officers.
    """
    platform = platform.lower()
    
    # Generic template
    template = (
        f"To the Grievance Officer, {platform.capitalize()},\n\n"
        f"Under Section 69A of the IT Act 2000, we request the immediate removal of the following content:\n"
        f"URL: {url}\n"
        f"Author: @{author}\n"
        f"Post ID: {post_id}\n\n"
        f"This content violates public order and constitutes an incitement to violence. "
        f"Please acknowledge receipt and confirm action taken within 24 hours.\n\n"
        f"Regards,\n"
        f"Cyber Cell, Gujarat Police"
    )
    
    # Platform specific nuances could be added here
    email_target = "grievance-india@twitter.com" if platform == "x" else "grievance@meta.com"

    return {
        "platform": platform,
        "email_target": email_target,
        "subject": f"URGENT: Content Takedown Request - Section 69A (ID: {post_id})",
        "body": template
    }
