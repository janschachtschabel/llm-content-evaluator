"""LLM Content Evaluator - AI-powered content evaluation using LLM as Judge methodology."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.routes import health, schemes, evaluate
from core.dependencies import initialize_engine, shutdown_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup: Initialize singleton EvaluationEngine
    logger.info("🚀 Initializing EvaluationEngine singleton...")
    initialize_engine("schemes")
    logger.info("✅ EvaluationEngine initialized successfully")
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("🔄 Shutting down EvaluationEngine...")
    shutdown_engine()
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="LLM Content Evaluator",
    description="AI-powered content evaluation API using LLM as Judge methodology for educational content quality assessment and legal compliance",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(schemes.router)
app.include_router(evaluate.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
