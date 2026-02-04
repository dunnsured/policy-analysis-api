"""
Direct analysis endpoints for testing without webhooks
"""

import logging
import uuid
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import settings
from services.orchestrator import run_policy_analysis, analysis_status_store

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Direct analysis request"""
    client_name: str
    client_industry: str = "Other/General"
    policy_type: str = "cyber"
    renewal: bool = False


class AnalysisStatusResponse(BaseModel):
    """Status of an analysis job"""
    analysis_id: str
    status: str
    progress: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict] = None


@router.post("/upload")
async def analyze_uploaded_policy(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Policy PDF file"),
    client_name: str = Form(..., description="Client company name"),
    client_industry: str = Form("Other/General", description="Client industry"),
    policy_type: str = Form("cyber", description="Policy type"),
    renewal: bool = Form(False, description="Is this a renewal?"),
):
    """
    Upload a policy PDF directly for analysis (without webhook integration).

    This is useful for:
    - Testing the analysis workflow
    - One-off analysis without SaaS integration
    - Demo purposes

    The analysis runs asynchronously. Use GET /analysis/{analysis_id}/status
    to check progress and retrieve results.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Generate analysis ID
    analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"

    # Save uploaded file temporarily
    temp_path = os.path.join(settings.TEMP_DIR, f"{analysis_id}_{file.filename}")
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(f"📤 Direct upload received: {file.filename}")
    logger.info(f"   Client: {client_name}")
    logger.info(f"   Industry: {client_industry}")
    logger.info(f"   Analysis ID: {analysis_id}")

    # Create payload similar to webhook
    payload = {
        "event_type": "policy.uploaded",
        "policy_id": f"direct_{analysis_id}",
        "client_id": f"direct_{client_name.lower().replace(' ', '_')}",
        "client_name": client_name,
        "client_industry": client_industry,
        "file_url": None,  # Local file, no URL
        "file_name": file.filename,
        "file_size": len(content),
        "policy_type": policy_type,
        "renewal": renewal,
        "callback_url": None,
        "_local_file_path": temp_path,  # Internal: path to saved file
    }

    # Queue analysis
    background_tasks.add_task(
        run_policy_analysis,
        analysis_id=analysis_id,
        payload=payload,
    )

    return {
        "success": True,
        "analysis_id": analysis_id,
        "message": "Analysis started. Use GET /analysis/{analysis_id}/status to check progress.",
        "status_url": f"/analysis/{analysis_id}/status",
    }


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """
    Get the current status of an analysis job.

    Returns the analysis progress and results when complete.
    """
    if analysis_id not in analysis_status_store:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatusResponse(**analysis_status_store[analysis_id])


@router.get("/{analysis_id}/report")
async def download_report(analysis_id: str):
    """
    Download the generated PDF report for a completed analysis.
    """
    if analysis_id not in analysis_status_store:
        raise HTTPException(status_code=404, detail="Analysis not found")

    status = analysis_status_store[analysis_id]
    if status.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Current status: {status.get('status')}"
        )

    report_path = status.get("result", {}).get("report_path")
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=os.path.basename(report_path),
    )


@router.get("/")
async def list_analyses():
    """
    List all analysis jobs (for debugging/demo purposes).
    """
    return {
        "analyses": [
            {
                "analysis_id": aid,
                "status": data.get("status"),
                "client_name": data.get("result", {}).get("client_name", "Unknown"),
                "started_at": data.get("started_at"),
            }
            for aid, data in analysis_status_store.items()
        ]
    }
