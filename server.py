import os
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from src.server.generator import generate_candidate_dataset
from src.server.pipeline import run_ranking_pipeline
import src.server.embedding_ranker as er
from src.server.reasoning import generate_gemini_explanation

# Initialize FastAPI
app = FastAPI(title="AuraTalent AI Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global candidate database pool
cached_candidates = []
pool_generation_in_progress = False

def generate_pool_in_bg():
    global cached_candidates, pool_generation_in_progress
    pool_generation_in_progress = True
    print("Starting background generation of 100,000 resume pool...")
    try:
        cached_candidates = generate_candidate_dataset(100000)
        print(f"Successfully generated {len(cached_candidates)} candidates.")
        # Trigger background FAISS indexing
        er.build_faiss_index_bg(cached_candidates)
    except Exception as e:
        print(f"Error generating candidates: {e}")
    finally:
        pool_generation_in_progress = False

# Trigger background pool generation and eager model warming on startup
@app.on_event("startup")
async def startup_event():
    # Warm up local sentence transformer model
    er.init_embedding_model()
    # Generate 100,000 resumes
    threading.Thread(target=generate_pool_in_bg, daemon=True).start()

# Request schemas
class RankRequest(BaseModel):
    jobDescriptionText: str
    topKRetrieval: int = 2000
    useGeminiEmbedding: bool = False
    weights: dict = {
        "semantic": 0.50,
        "skills": 0.25,
        "career": 0.15,
        "behavioral": 0.10
    }

class ExplainRequest(BaseModel):
    candidate: dict
    jobDescriptionText: str

class ExportRequest(BaseModel):
    candidates: list

@app.get("/api/status")
async def get_status():
    has_api_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {
        "success": True,
        "poolSize": len(cached_candidates),
        "isPoolGenerated": len(cached_candidates) > 0,
        "modelStatus": er.get_model_status(),
        "faissStatus": er._faiss_status,
        "envHasApiKey": has_api_key
    }

@app.post("/api/init-model")
async def init_model():
    er.init_embedding_model()
    return {"success": True, "status": er.get_model_status()}

@app.post("/api/rank")
async def rank_candidates(payload: RankRequest):
    global cached_candidates
    if not cached_candidates:
        # If pool isn't ready, block briefly or generate a smaller pool for backup
        if pool_generation_in_progress:
            # wait up to 3 seconds
            for _ in range(15):
                if cached_candidates:
                    break
                time.sleep(0.2)
        if not cached_candidates:
            # fallback fast generation of 10,000 candidates
            print("Fallback generation of subset pool...")
            cached_candidates = generate_candidate_dataset(10000)
            er.build_faiss_index_bg(cached_candidates)

    try:
        results = run_ranking_pipeline(cached_candidates, payload.dict())
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/explain")
async def explain_candidate(payload: ExplainRequest):
    try:
        reasoning = generate_gemini_explanation(payload.candidate, payload.jobDescriptionText)
        return {"success": True, "reasoning": reasoning}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export-csv")
async def export_csv(payload: ExportRequest):
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Rank", "Candidate ID", "Name", "Headline", "Experience Years", 
        "Education", "Skills", "Final Score", "Semantic Score", 
        "Skill Score", "Career Score", "Behavioral Score", "Reasoning"
    ])
    
    for c in payload.candidates:
        writer.writerow([
            c.get("rank", ""),
            c.get("candidate_id", ""),
            c.get("name", ""),
            c.get("headline", ""),
            c.get("experience_years", ""),
            c.get("education", ""),
            ", ".join(c.get("skills", [])),
            c.get("scores", {}).get("finalScore", ""),
            c.get("scores", {}).get("semanticScore", ""),
            c.get("scores", {}).get("skillScore", ""),
            c.get("scores", {}).get("careerScore", ""),
            c.get("scores", {}).get("behavioralScore", ""),
            c.get("reasoning", "")
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.read().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=submission.csv"}
    )

# Static files of Vite compiled distribution SPA
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if os.path.exists("dist"):
        if full_path and os.path.exists(f"dist/{full_path}") and os.path.isfile(f"dist/{full_path}"):
            return FileResponse(f"dist/{full_path}")
        return FileResponse("dist/index.html")
    return {"message": "AuraTalent AI Backend - React Frontend not compiled yet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=False)
