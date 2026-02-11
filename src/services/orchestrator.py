"""
Analysis Orchestrator
Coordinates the policy analysis workflow from end to end
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp

from config import settings
from services.pdf_extractor import extractor
from services.claude_analyzer import analyzer
from services.report_generator import generator
from services.supabase_client import supabase_service

logger = logging.getLogger(__name__)

# In-memory status store (use Redis/DB in production)
analysis_status_store: Dict[str, Dict[str, Any]] = {}


async def run_policy_analysis(analysis_id: str, payload: Dict[str, Any]):
    """
    Main orchestration function for policy analysis.

    Coordinates:
    1. PDF download/extraction
    2. Claude-powered analysis
    3. Report generation
    4. Callback delivery (if URL provided)

    Args:
        analysis_id: Unique identifier for this analysis
        payload: Webhook payload or direct upload data
    """
    logger.info(f"🚀 Starting analysis workflow: {analysis_id}")

    # Initialize status
    analysis_status_store[analysis_id] = {
        "analysis_id": analysis_id,
        "status": "started",
        "progress": "Initializing...",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
        "result": None,
    }

    try:
        # Extract metadata from payload
        client_name = payload.get("client_name", "Unknown Client")
        client_industry = payload.get("client_industry", "Other/General")
        policy_type = payload.get("policy_type", "cyber")
        is_renewal = payload.get("renewal", False)
        callback_url = payload.get("callback_url")

        # STEP 1: Get the PDF content
        _update_status(analysis_id, "extracting", "Extracting text from PDF...")

        local_path = payload.get("_local_file_path")
        file_url = payload.get("file_url")

        if local_path:
            # Direct upload - file already saved locally
            extraction = await extractor.extract_from_file(local_path)
        elif file_url:
            # Webhook - download from presigned URL
            extraction = await extractor.extract_from_url(str(file_url))
        else:
            raise ValueError("No file path or URL provided")

        if not extraction.success:
            raise Exception(f"PDF extraction failed: {extraction.error}")

        logger.info(f"   Extracted {len(extraction.text)} chars from {extraction.page_count} pages")

        # STEP 2: Analyze with Claude
        _update_status(analysis_id, "analyzing", "Analyzing policy with Claude...")

        analysis_result = await analyzer.analyze_policy(
            policy_text=extraction.text,
            client_name=client_name,
            client_industry=client_industry,
            policy_type=policy_type,
            is_renewal=is_renewal,
        )

        if not analysis_result.success:
            raise Exception(f"Claude analysis failed: {analysis_result.error}")

        analysis_data = analysis_result.analysis_data
        logger.info(f"   Analysis complete, tokens used: {analysis_result.tokens_used}")

        # STEP 3: Generate PDF report
        _update_status(analysis_id, "generating", "Generating PDF report...")

        report_result = await generator.generate_report(
            analysis_data=analysis_data,
            output_dir=settings.REPORTS_DIR,
        )

        if not report_result.success:
            logger.warning(f"   Report generation failed: {report_result.error}")
            report_path = None
        else:
            report_path = report_result.report_path
            logger.info(f"   Report generated: {report_path}")

        # Build result summary
        exec_summary = analysis_data.get("executive_summary", {})
        key_metrics = exec_summary.get("key_metrics", {})

        result = {
            "analysis_id": analysis_id,
            "policy_id": payload.get("policy_id"),
            "client_id": payload.get("client_id"),
            "client_name": client_name,
            "status": "completed",
            "overall_score": key_metrics.get("overall_maturity_score"),
            "recommendation": exec_summary.get("recommendation"),
            "report_path": report_path,
            "analysis_data": analysis_data,
            "completed_at": datetime.utcnow().isoformat(),
            "processing_time_seconds": _calculate_duration(analysis_id),
        }

                # STEP 5: Store results in Supabase
                policy_id = payload.get("policy_id")
                if policy_id:
                                await supabase_service.store_analysis_result(
                                                    policy_id=policy_id,
                                                    analysis_id=analysis_id,
                                                    analysis_data=result,
                                                    status="completed"
                                                )

        # Update status to complete
        analysis_status_store[analysis_id].update({
            "status": "completed",
            "progress": "Analysis complete",
            "completed_at": result["completed_at"],
            "result": result,
        })

        logger.info(f"✅ Analysis complete: {analysis_id}")
        logger.info(f"   Score: {result['overall_score']}")
        logger.info(f"   Recommendation: {result['recommendation']}")

        # STEP 4: Send callback (if configured)
        if callback_url:
            await _send_callback(callback_url, result)

    except Exception as e:
        logger.error(f"❌ Analysis failed: {analysis_id} - {str(e)}")

        # Update status to failed
        analysis_status_store[analysis_id].update({
            "status": "failed",
            "progress": "Analysis failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        })

        # Send failure callback if configured
        callback_url = payload.get("callback_url")
        if callback_url:
            await _send_callback(callback_url, {
                "analysis_id": analysis_id,
                "policy_id": payload.get("policy_id"),
                "client_id": payload.get("client_id"),
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.utcnow().isoformat(),
            })


def _update_status(analysis_id: str, status: str, progress: str):
    """Update the status of an analysis"""
    if analysis_id in analysis_status_store:
        analysis_status_store[analysis_id].update({
            "status": status,
            "progress": progress,
        })
    logger.info(f"   [{analysis_id}] {progress}")


def _calculate_duration(analysis_id: str) -> float:
    """Calculate processing duration in seconds"""
    if analysis_id not in analysis_status_store:
        return 0

    started = analysis_status_store[analysis_id].get("started_at")
    if not started:
        return 0

    start_dt = datetime.fromisoformat(started)
    duration = (datetime.utcnow() - start_dt).total_seconds()
    return round(duration, 2)


async def _send_callback(callback_url: str, result: Dict[str, Any]):
    """Send analysis results to callback URL"""
    logger.info(f"📤 Sending callback to {callback_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                callback_url,
                json=result,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=settings.CALLBACK_TIMEOUT),
            ) as response:
                if response.status == 200:
                    logger.info(f"   Callback sent successfully")
                else:
                    logger.warning(f"   Callback returned status {response.status}")

    except Exception as e:
        logger.error(f"   Callback failed: {str(e)}")
