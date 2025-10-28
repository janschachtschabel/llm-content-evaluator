"""Evaluation endpoint for text assessment."""

from fastapi import APIRouter, Body, Depends, HTTPException
from openai import AsyncOpenAI
from datetime import datetime
from typing import Dict, Any
from loguru import logger
import traceback

from models.schemas import EvaluationRequest, EvaluationResponse, EvaluationResult
from core.dependencies import get_engine_instance
from core.config import settings

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


def get_openai_client() -> AsyncOpenAI:
    """Get OpenAI client."""
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


@router.post("/", response_model=EvaluationResponse,
         summary="Evaluate Text Content")
async def evaluate_text(payload: EvaluationRequest = Body(...)) -> EvaluationResponse:
    """Evaluate text content against quality and compliance schemes.
    
    This endpoint evaluates educational content, articles, or other text materials
    against various quality dimensions and legal compliance requirements.
    
    **Available Scheme Types:**
    
    - **Quality Dimensions**: neutralitaet_new, sachrichtigkeit_old, didaktik_methodik_new, etc.
    - **Legal Gates**: jugendschutz_gate, strafrecht_gate, persoenlichkeitsrechte_gate
    - **Derived Evaluations**: rechtliche_compliance, overall_quality

    **Request Parameters:**

    - ``text`` *(string, required)*: Vollständiger Inhalt (10–50.000 Zeichen), der bewertet werden soll.
    - ``schemes`` *(array[str], required)*: Liste der zu prüfenden Schemas (max. 10).
    - ``include_reasoning`` *(bool, optional, default ``true``)*: Steuert, ob ausführliche Begründungen
      und Kriterien-Breakdowns zurückgegeben werden.
    - ``context_type`` (``"content"`` | ``"platform"`` | ``"both"``): Steuert, welche Gate-Regeln
      angewendet werden. ``content`` blendet Plattform-spezifische Regeln aus, ``platform`` berücksichtigt
      nur Plattform-Metadaten, ``both`` führt eine vollständige Prüfung durch.
    
    **Usage Examples:**
    
    1. **Single Quality Check:**
       ```json
       {
         "text": "Educational content about German history...",
         "schemes": ["neutralitaet_new"],
         "include_reasoning": true
       }
       ```
    
    2. **Comprehensive Quality Assessment:**
       ```json
       {
         "text": "Learning material for students...",
         "schemes": ["neutralitaet_new", "sachrichtigkeit_old", "didaktik_methodik_new"],
         "include_reasoning": true
       }
       ```
    
    3. **Legal Compliance Check:**
       ```json
       {
         "text": "Content for publication...",
         "schemes": ["rechtliche_compliance"],
         "include_reasoning": true
       }
       ```
    
    **Response Structure:**
    
    - Each scheme returns a score, label, and detailed reasoning
    - Checklist schemes show individual criteria breakdown
    - Derived schemes include intermediate results from dependencies
    - Binary gates indicate pass/fail for legal compliance
    
    **Score Ranges:**
    
    - Quality scales: 0.0 (poor) to 5.0 (excellent)
    - Binary gates: 0 (fail) or 1 (pass)
    - Derived compliance: 0 (non-compliant) or 1 (compliant)
    """
    try:
        # Use singleton engine instance (initialized at app startup)
        engine = get_engine_instance()
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        # Validate schemes exist
        available_schemes = {s["id"] for s in engine.get_schemes()}
        invalid_schemes = set(payload.schemes) - available_schemes
        if invalid_schemes:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown schemes: {list(invalid_schemes)}"
            )
        
        # Perform evaluation
        start_time = datetime.now()
        evaluation_data = await engine.evaluate_text(
            text=payload.text,
            scheme_ids=payload.schemes,
            llm_client=openai_client,
            model=settings.openai_model,
            context_type=payload.context_type
        )
        end_time = datetime.now()
        
        # Convert to response format
        results = [
            EvaluationResult(
                scheme_id=result["scheme_id"],
                dimension=result["dimension"],
                value=result.get("value"),
                label=result.get("label"),
                confidence=result.get("confidence"),
                reasoning=result.get("reasoning") if payload.include_reasoning else None,
                criteria=result.get("criteria") if payload.include_reasoning else None,
                scale_info=result.get("scale_info"),
                na_reason=result.get("na_reason")
            )
            for result in evaluation_data["results"]
        ]
        
        # Build metadata and provenance
        metadata = {
            "processing_time_ms": int((end_time - start_time).total_seconds() * 1000),
            "model_used": settings.openai_model,
            "include_reasoning": payload.include_reasoning
        }
        
        provenance = {
            "timestamp": start_time.isoformat(),
            "api_version": "0.1.0",
            "text_length": len(payload.text),
            "schemes_count": len(payload.schemes)
        }
        
        return EvaluationResponse(
            results=results,
            gates_passed=evaluation_data.get("gates_passed", True),
            overall_score=evaluation_data.get("overall_score"),
            overall_label=evaluation_data.get("overall_label"),
            metadata=metadata,
            provenance=provenance
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for invalid schemes)
        raise
    except Exception as e:
        # Log detailed error internally
        logger.error(f"Evaluation failed with exception: {str(e)}")
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        
        # Return generic error to client (avoid info leakage)
        raise HTTPException(
            status_code=500, 
            detail="Evaluation failed due to an internal error. Please check your request or contact support."
        )
