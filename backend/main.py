from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import status, resumes, ranking
from backend.routers import status, resumes, ranking, evaluation
app = FastAPI(
    title="AuraTalent AI Backend",
    version="1.0.0",
    description="FastAPI Backend with PostgreSQL, pgvector (768-d), and Gemini Integration"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(status.router)
app.include_router(resumes.router)
app.include_router(ranking.router)
app.include_router(evaluation.router)