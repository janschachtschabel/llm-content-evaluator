"""Schemes endpoint for listing available evaluation schemes."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from core.evaluation import EvaluationEngine
from models.schemas import SchemesResponse
import traceback

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("/", response_model=SchemesResponse,
         summary="List Available Schemes")
async def list_schemes():
    """List all available evaluation schemes with detailed information.
    
    Returns comprehensive information about all loaded evaluation schemes including:
    - Scheme metadata (ID, name, description, version)
    - Quality dimensions and scale types
    - Available score ranges and labels
    - Dependencies for derived schemes
    
    **Scheme Categories:**
    
    - **Quality Dimensions**: Evaluate content quality aspects
      - `neutralitaet_new`: Political neutrality assessment (checklist)
      - `neutralitaet_old`: Political neutrality assessment (ordinal)
      - `sachrichtigkeit_new`: Factual accuracy evaluation (checklist)
      - `sachrichtigkeit_old`: Factual accuracy evaluation (ordinal)
      - `didaktik_methodik_new`: Pedagogical quality analysis (checklist)
      - `didaktik_methodik_old`: Pedagogical quality analysis (ordinal)
      - `aktualitaet_new`: Content timeliness assessment (checklist)
      - `aktualitaet_old`: Content timeliness assessment (ordinal)
      - `sprachliche_angemessenheit_new`: Language appropriateness (checklist)
      - `sprachliche_angemessenheit_old`: Language appropriateness (ordinal)
      - `medial_passend_new`: Media format suitability (checklist)
      - `medial_passend_old`: Media format suitability (ordinal)
    
    - **Legal Gates**: Binary compliance checks
      - `jugendschutz_gate`: Youth protection compliance
      - `strafrecht_gate`: Criminal law compliance
      - `persoenlichkeitsrechte_gate`: Privacy rights compliance
    
    - **Derived Evaluations**: Combined assessments
      - `rechtliche_compliance`: Overall legal compliance
      - `overall_quality`: Weighted quality combination
    
    **Example Response:**
    ```json
    {
        "schemes": [
            {
                "id": "neutralitaet_new",
                "name": "Neutralität (Neue Bewertung)",
                "description": "Bewertung der politischen Neutralität...",
                "dimension": "neutrality",
                "type": "checklist_additive",
                "output_range": {"min": 0.0, "max": 5.0}
            }
        ],
        "total": 15,
        "status": "success"
    }
    ```
    
    Use this endpoint to discover available schemes before making evaluation requests.
    """
    try:
        engine = EvaluationEngine("schemes")
        schemes_data = engine.get_schemes()
        
        # Simple response without complex Pydantic models
        response = {
            "schemes": schemes_data,
            "total": len(schemes_data),
            "status": "success"
        }
        
        return response
        
    except Exception as e:
        # Detailed error logging
        error_details = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to load schemes: {str(e)}"
        )
