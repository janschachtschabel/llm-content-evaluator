"""Health check endpoint."""

from fastapi import APIRouter
from models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse, 
         summary="Health Check")
async def health_check() -> HealthResponse:
    """Health check endpoint to verify API status and loaded schemes.
    
    Returns the current status of the evaluation API including:
    - Service health status
    - API version information  
    - Number of evaluation schemes loaded and available
    
    Use this endpoint to verify the API is running and ready to process
    evaluation requests before sending content for analysis.
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "version": "0.1.0", 
        "schemes_loaded": 15
    }
    ```
    """
    from core.evaluation import EvaluationEngine
    
    try:
        engine = EvaluationEngine()
        schemes = engine.get_schemes()
        schemes_count = len(schemes)
        
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            schemes_loaded=schemes_count
        )
    except Exception:
        return HealthResponse(
            status="degraded",
            version="0.1.0",
            schemes_loaded=0
        )
