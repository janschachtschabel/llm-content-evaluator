"""Pydantic models for evaluation API."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ScaleType(str, Enum):
    """Supported evaluation scale types."""
    ORDINAL_RUBRIC = "ordinal_rubric"
    CHECKLIST_ADDITIVE = "checklist_additive"
    BINARY_GATE = "binary_gate"
    DERIVED = "derived"


class SelectionStrategy(str, Enum):
    """Selection strategies for ordinal rubrics."""
    FIRST_MATCH = "first_match"
    BEST_FIT = "best_fit"
    MANUAL = "manual"


class AggregationStrategy(str, Enum):
    """Aggregation strategies for scales."""
    FIRST_MATCH = "first_match"
    WEIGHTED_MEAN = "weighted_mean"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"


class MissingStrategy(str, Enum):
    """Strategies for handling missing values."""
    IGNORE = "ignore"
    ZERO = "zero"
    IMPUTE = "impute"


class EvaluationRequest(BaseModel):
    """Request for text evaluation against quality schemes.
    
    Examples:
        Single scheme evaluation:
        {
            "text": "Beispieltext für die Bewertung...",
            "schemes": ["neutralitaet_new"],
            "include_reasoning": true
        }
        
        Multiple schemes evaluation:
        {
            "text": "Bildungsinhalt zur Bewertung...",
            "schemes": ["neutralitaet_new", "sachrichtigkeit_old", "didaktik_methodik_new"],
            "include_reasoning": true
        }
        
        Legal compliance check:
        {
            "text": "Inhalt für rechtliche Prüfung...",
            "schemes": ["rechtliche_compliance"],
            "include_reasoning": true
        }
    """
    text: str = Field(
        ...,
        description="Text content to be evaluated (educational material, articles, etc.)",
        min_length=10,
        max_length=50000,
        example="Die deutsche Geschichte zwischen 1918 und 1945 war geprägt von politischen Umbrüchen..."
    )
    schemes: List[str] = Field(
        ...,
        description="List of evaluation scheme IDs to apply. Available schemes include quality dimensions (neutralitaet_new, sachrichtigkeit_old, etc.), legal gates (jugendschutz_gate, strafrecht_gate), and derived evaluations (rechtliche_compliance, overall_quality)",
        min_items=1,
        max_items=10,
        example=["neutralitaet_new", "sachrichtigkeit_old"]
    )
    include_reasoning: bool = Field(
        True,
        description="Whether to include detailed reasoning and criteria in the response. Set to false for faster evaluation without explanations."
    )


class SchemeInfo(BaseModel):
    """Detailed information about an available evaluation scheme.
    
    Provides metadata about scheme capabilities, scoring ranges,
    and intended use cases for API consumers.
    """
    id: str = Field(
        ..., 
        description="Unique scheme identifier used in evaluation requests",
        example="neutralitaet_new"
    )
    name: str = Field(
        ..., 
        description="Human-readable scheme name for display purposes",
        example="Neutralität (Neue Bewertung)"
    )
    description: str = Field(
        ..., 
        description="Detailed description of what this scheme evaluates",
        example="Bewertung der politischen und weltanschaulichen Neutralität von Bildungsinhalten"
    )
    dimension: str = Field(
        ..., 
        description="Quality dimension or compliance area being assessed",
        example="neutrality"
    )
    scale_type: ScaleType = Field(
        ..., 
        description="Type of evaluation scale: ordinal_rubric, checklist_additive, binary_gate, or derived"
    )
    output_range: Dict[str, Union[int, float, str, bool, List[Union[int, float, str, bool]]]] = Field(
        ..., 
        description="Possible output values and ranges for this scheme",
        example={"min": 0.0, "max": 5.0, "type": "float"}
    )
    version: str = Field(
        ..., 
        description="Scheme version for tracking updates and compatibility",
        example="2.0"
    )


class SchemesResponse(BaseModel):
    """Response containing all available evaluation schemes.
    
    Provides comprehensive information about loaded schemes
    to help users select appropriate evaluations.
    """
    schemes: List[SchemeInfo] = Field(
        ..., 
        description="List of all available evaluation schemes with detailed metadata"
    )
    total: int = Field(
        ..., 
        description="Total number of schemes available",
        example=15
    )
    status: str = Field(
        default="success", 
        description="Response status indicator",
        example="success"
    )


class EvaluationResult(BaseModel):
    """Result of a single scheme evaluation.
    
    Contains the evaluation outcome, score, label, and detailed breakdown
    of how the result was calculated including individual criteria.
    """
    scheme_id: str = Field(..., description="ID of the evaluation scheme used", example="neutralitaet_new")
    dimension: str = Field(..., description="Quality dimension being evaluated", example="neutrality")
    value: Optional[Union[int, float, str]] = Field(
        None, 
        description="Numeric score or result value. For quality scales: 0.0-5.0, for binary gates: 0 or 1",
        example=2.35
    )
    label: Optional[str] = Field(
        None, 
        description="Human-readable label corresponding to the score",
        example="Ideologisch eingefärbt, aber korrekter Inhalt"
    )
    confidence: Optional[float] = Field(
        None, 
        description="Confidence level of the evaluation (0.0-1.0)",
        example=0.8
    )
    reasoning: Optional[str] = Field(
        None, 
        description="Detailed explanation of the evaluation result and methodology"
    )
    criteria: Optional[Dict[str, Any]] = Field(
        None, 
        description="Breakdown of individual criteria evaluated (for checklist and derived schemes)"
    )
    scale_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Information about the evaluation scale, ranges, and methodology used"
    )
    na_reason: Optional[str] = Field(
        None, 
        description="Reason why evaluation could not be completed (if applicable)"
    )


class EvaluationResponse(BaseModel):
    """Complete evaluation response containing all scheme results and metadata.
    
    Example response for quality evaluation:
    {
        "results": [
            {
                "scheme_id": "neutralitaet_new",
                "dimension": "neutrality",
                "value": 2.35,
                "label": "Ideologisch eingefärbt, aber korrekter Inhalt",
                "confidence": 0.8,
                "reasoning": "Detaillierte Bewertung...",
                "criteria": {...},
                "scale_info": {...}
            }
        ],
        "gates_passed": true,
        "metadata": {...},
        "provenance": {...}
    }
    """
    results: List[EvaluationResult] = Field(
        ..., 
        description="List of evaluation results, one for each requested scheme"
    )
    gates_passed: bool = Field(
        ..., 
        description="Whether all binary gate evaluations passed. If false, content failed critical compliance checks."
    )
    metadata: Dict[str, Any] = Field(
        ..., 
        description="Processing metadata including timing, model used, and configuration"
    )
    provenance: Dict[str, Any] = Field(
        ..., 
        description="Audit trail information including timestamp, API version, and input characteristics"
    )


class HealthResponse(BaseModel):
    """Health check response indicating API status and readiness.
    
    Used to verify the evaluation service is running properly and
    has successfully loaded all evaluation schemes.
    """
    status: str = Field(
        ..., 
        description="Service health status: 'healthy', 'degraded', or 'unhealthy'",
        example="healthy"
    )
    version: str = Field(
        ..., 
        description="API version number",
        example="0.1.0"
    )
    schemes_loaded: int = Field(
        ..., 
        description="Number of evaluation schemes successfully loaded and available",
        example=15
    )
