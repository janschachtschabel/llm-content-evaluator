"""FastAPI dependencies for singleton instances."""

from typing import Optional

from core.config import settings
from core.evaluation import EvaluationEngine

# Global singleton instance
_engine_instance: Optional[EvaluationEngine] = None


def get_engine_instance() -> EvaluationEngine:
    """Return the singleton EvaluationEngine instance, creating it if necessary."""
    global _engine_instance

    if _engine_instance is None:
        # Fallback for environments where FastAPI startup hooks (lifespan)
        # are not triggered (e.g. some serverless cold starts).
        initialize_engine(settings.schemes_dir)

    return _engine_instance


def initialize_engine(schemes_dir: str = "schemes") -> None:
    """Initialize the singleton EvaluationEngine instance.
    
    This should be called once during application startup.
    
    Args:
        schemes_dir: Directory containing YAML scheme files
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EvaluationEngine(schemes_dir)


def shutdown_engine() -> None:
    """Cleanup the singleton EvaluationEngine instance.
    
    This should be called during application shutdown.
    """
    global _engine_instance
    _engine_instance = None
