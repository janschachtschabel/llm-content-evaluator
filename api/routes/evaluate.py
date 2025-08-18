"""Evaluation endpoint for text assessment."""

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from datetime import datetime
from typing import Dict, Any

from models.schemas import EvaluationRequest, EvaluationResponse, EvaluationResult
from core.evaluation import EvaluationEngine
from core.config import settings

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


def get_evaluation_engine() -> EvaluationEngine:
    """Get evaluation engine instance."""
    return EvaluationEngine()


def get_openai_client() -> AsyncOpenAI:
    """Get OpenAI client."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


@router.post("/", response_model=EvaluationResponse,
         summary="Evaluate Text Content")
async def evaluate_text(request: EvaluationRequest) -> EvaluationResponse:
    """Evaluate text content against quality and compliance schemes.
    
    This endpoint evaluates educational content, articles, or other text materials
    against various quality dimensions and legal compliance requirements.
    
    **Available Scheme Types:**
    
    - **Quality Dimensions**: neutralitaet_new, sachrichtigkeit_old, didaktik_methodik_new, etc.
    - **Legal Gates**: jugendschutz_gate, strafrecht_gate, persoenlichkeitsrechte_gate
    - **Derived Evaluations**: rechtliche_compliance, overall_quality
    
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
        # Initialize engine and client directly (no dependency injection for Swagger compatibility)
        engine = EvaluationEngine()
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Validate schemes exist
        available_schemes = {s["id"] for s in engine.get_schemes()}
        invalid_schemes = set(request.schemes) - available_schemes
        if invalid_schemes:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown schemes: {list(invalid_schemes)}"
            )
        
        # Perform evaluation
        start_time = datetime.now()
        evaluation_data = await engine.evaluate_text(
            text=request.text,
            scheme_ids=request.schemes,
            llm_client=openai_client
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
                reasoning=result.get("reasoning") if request.include_reasoning else None,
                criteria=result.get("criteria") if request.include_reasoning else None,
                scale_info=result.get("scale_info"),
                na_reason=result.get("na_reason")
            )
            for result in evaluation_data["results"]
        ]
        
        # Build metadata and provenance
        metadata = {
            "processing_time_ms": int((end_time - start_time).total_seconds() * 1000),
            "model_used": settings.openai_model,
            "include_reasoning": request.include_reasoning
        }
        
        provenance = {
            "timestamp": start_time.isoformat(),
            "api_version": "0.1.0",
            "text_length": len(request.text),
            "schemes_count": len(request.schemes)
        }
        
        return EvaluationResponse(
            results=results,
            gates_passed=evaluation_data.get("gates_passed", True),
            metadata=metadata,
            provenance=provenance
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
