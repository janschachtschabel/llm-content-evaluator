"""LLM Content Evaluator - AI-powered content evaluation using LLM as Judge methodology."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, schemes, evaluate

app = FastAPI(
    title="LLM Content Evaluator",
    description="AI-powered content evaluation API using LLM as Judge methodology for educational content quality assessment and legal compliance",
    version="0.1.0",
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
