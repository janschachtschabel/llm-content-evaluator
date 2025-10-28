"""Schemes endpoint for listing available evaluation schemes."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from loguru import logger
import traceback

from core.dependencies import get_engine_instance
from models.schemas import SchemesResponse

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("/", response_model=SchemesResponse,
         summary="List Available Schemes")
async def list_schemes(
    include_parts: bool = Query(
        False,
        description="Include part schemas (e.g., *_part1, *_part2). Default: False (only master and gate schemas)"
    )
):
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
    
    - **Master Gates**: Combined assessments (a + b catalogs)
      - `criminal_law_gate`: Strafrecht (1A + 1B)
      - `protection_of_minors_gate`: Jugendschutz (2A + 2B)
      - `personal_law_gate`: Persönlichkeitsrechte (3A + 3B)
      - `data_privacy_gate`: Datenschutz (4A + 4B)
    
    - **Derived Evaluations**: Combined assessments
      - `rechtliche_compliance`: Overall legal compliance
      - `overall_quality`: Weighted quality combination
    
    **Query Parameters:**
      - `include_parts`: Include part schemas (default: False)
        - False: Only master/gate schemas (e.g., criminal_law_gate)
        - True: All schemas including parts (e.g., criminal_law_1a_part1)
    
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
        # Use singleton engine instance (initialized at app startup)
        engine = get_engine_instance()
        schemes_data = engine.get_schemes()
        
        # Filter out part schemas unless explicitly requested
        if not include_parts:
            schemes_data = [
                scheme for scheme in schemes_data
                if "_part" not in scheme.get("id", "")
            ]
        
        # Simple response without complex Pydantic models
        response = {
            "schemes": schemes_data,
            "total": len(schemes_data),
            "status": "success"
        }
        
        return response
        
    except Exception as e:
        # Log detailed error internally
        logger.error(f"Failed to load schemes: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        
        # Return generic error to client (avoid info leakage)
        raise HTTPException(
            status_code=500, 
            detail="Failed to load evaluation schemes. Please contact support if this persists."
        )
