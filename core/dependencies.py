"""FastAPI dependencies for singleton instances."""

from typing import Optional
from core.evaluation import EvaluationEngine

# Global singleton instance
_engine_instance: Optional[EvaluationEngine] = None


def get_engine_instance() -> EvaluationEngine:
    """Get or create the singleton EvaluationEngine instance.
    
    This function returns a cached instance of the EvaluationEngine,
    ensuring that YAML schemas are only loaded once during app startup.
    
    Returns:
        EvaluationEngine: The singleton engine instance
        
    Raises:
        RuntimeError: If engine has not been initialized via initialize_engine()
    """
    global _engine_instance
    if _engine_instance is None:
        raise RuntimeError(
            "EvaluationEngine not initialized. "
            "Call initialize_engine() during app startup."
        )
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
