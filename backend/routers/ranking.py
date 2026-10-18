import io
import csv
import re
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from backend.config import settings
from backend.services.hybrid_retrieval import execute_hybrid_retrieval
from backend.services.reranker_service import (
    CrossEncoderReranker,
    get_reranker,
    rerank_candidates_with_cross_encoder,
    TOP_K_RERANK_LIMIT,
)
from backend.services.explanation_service import (
    generate_grounded_explanation,
    batch_explain_top_candidates,
    CandidateExplanation,
)

router = APIRouter(prefix="/api", tags=["Ranking & Compatibility"])

COMMON_SKILLS_LIST = [
    "python", "pytorch", "tensorflow", "kubernetes", "docker", "ray", "pinecone", "milvus", "qdrant",
    "react", "typescript", "javascript", "fastapi", "django", "flask", "postgresql", "redis", "elasticsearch",
    "mlflow", "kubeflow", "vllm", "tensorrt", "aws", "gcp", "azure", "ci/cd", "go", "rust", "c++", "java"
]


def parse_job_description(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    exp_required = 0

    m = re.search(r"(\d+)\+?\s*(?:-\s*\d+\s*)?\s*(?:years?|yrs?)\b", text_lower)
    if m:
        exp_required = int(m.group(1))

    required_skills = []
    preferred_skills = []
    pref_section = ""
    if "preferred" in text_lower:
        pref_split = text_lower.split("preferred")
        pref_section = pref_split[1]

    for skill in COMMON_SKILLS_LIST:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            if pref_section and re.search(pattern, pref_section):
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)

    if not required_skills:
        for skill in COMMON_SKILLS_LIST:
            if skill in text_lower:
                required_skills.append(skill)

    domain_keywords = []
    for kw in ["llm", "rag", "ai", "ml", "nlp", "frontend", "backend", "cloud", "devops"]:
        if re.search(rf"\b{kw}\b", text_lower):
            domain_keywords.append(kw)

    return {
        "text": text,
        "requiredSkills": required_skills if required_skills else ["engineering"],
        "preferredSkills": preferred_skills,
        "experienceYearsRequired": exp_required,
        "domainKeywords": domain_keywords
    }


class RankRequest(BaseModel):
    jobDescriptionText: str
    topKRetrieval: Optional[int] = 50
    useGeminiEmbedding: Optional[bool] = True
    enableCrossEncoder: Optional[bool] = True
    enableExplanations: Optional[bool] = False  # Optional on rank for performance
    weights: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {"semantic": 0.5, "skills": 0.25, "career": 0.15, "behavioral": 0.10}
    )


class ExplainRequest(BaseModel):
    candidate: Dict[str, Any]
    jobDescriptionText: str
    evidenceChunks: Optional[List[Dict[str, Any]]] = None


@router.post("/init-model")
def init_model():
    """Confirms model, embedding, and cross-encoder are initialized."""
    try:
        get_reranker().get_model()
        return {"success": True, "status": "loaded", "crossEncoderModel": "cross-encoder/ms-marco-MiniLM-L-6-v2"}
    except Exception as e:
        print(f"Error warming cross encoder in /api/init-model: {e}")
        return {"success": False, "status": "error", "error": str(e)}


@router.post("/rank")
def rank_candidates(req: RankRequest):
    """
    Phase 4 + Phase 5 Ranking Pipeline with Phase 7 Latency Instrumentation:
    1. Parse hard eligibility filters (min experience years)
    2. Phase 4 Hybrid Retrieval (PostgreSQL FTS + pgvector dense + RRF) -> Up to 50 candidates
    3. Phase 5 Cross-Encoder Reranking -> Top 15 candidates
    4. Optional Phase 6 Grounded Explanations
    5. Returns candidates with Phase 4 RRF scores and Phase 5 cross_encoder_scores intact.
    """
    total_start_time = time.time()
    if not req.jobDescriptionText or not req.jobDescriptionText.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")

    parsed_features = parse_job_description(req.jobDescriptionText)
    min_exp = float(parsed_features.get("experienceYearsRequired", 0))

    # Phase 4 Hybrid Retrieval (Top-K, capped at 50)
    phase4_start = time.time()
    top_k = min(req.topKRetrieval or 50, 50)
    try:
        retrieval_output = execute_hybrid_retrieval(
            job_description_text=req.jobDescriptionText,
            min_experience_years=min_exp,
            top_k=top_k,
            use_gemini_embedding=req.useGeminiEmbedding if req.useGeminiEmbedding is not None else True,
        )
    except Exception as e:
        print(f"Error in Phase 4 Hybrid Retrieval: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid retrieval failed: {str(e)}")

    phase4_latency_ms = int((time.time() - phase4_start) * 1000)
    phase4_candidates = retrieval_output["topCandidates"]
    telemetry = retrieval_output["telemetry"]
    telemetry["phase4RetrievalLatencyMs"] = phase4_latency_ms

    # Phase 5 Cross-Encoder Reranking (Top 15)
    final_candidates = phase4_candidates
    rerank_telemetry: Dict[str, Any] = {}
    phase5_latency_ms = 0

    if req.enableCrossEncoder and phase4_candidates:
        phase5_start = time.time()
        try:
            final_candidates, rerank_telemetry = rerank_candidates_with_cross_encoder(
                job_description=req.jobDescriptionText,
                candidates=phase4_candidates,
                top_k=TOP_K_RERANK_LIMIT,
            )
        except Exception as e:
            print(f"Error in Phase 5 Cross-Encoder Reranking: {e}")
            raise HTTPException(status_code=500, detail=f"Cross-encoder reranking failed: {str(e)}")
        phase5_latency_ms = int((time.time() - phase5_start) * 1000)
    elif len(phase4_candidates) > TOP_K_RERANK_LIMIT:
        final_candidates = phase4_candidates[:TOP_K_RERANK_LIMIT]

    telemetry["phase5RerankLatencyMs"] = phase5_latency_ms

    # Optional Phase 6 Explanations
    phase6_latency_ms = 0
    if req.enableExplanations and final_candidates:
        phase6_start = time.time()
        try:
            final_candidates = batch_explain_top_candidates(
                job_description=req.jobDescriptionText,
                top_candidates=final_candidates,
            )
        except Exception as e:
            print(f"Non-fatal error generating explanations in /rank: {e}")
        phase6_latency_ms = int((time.time() - phase6_start) * 1000)

    telemetry["phase6ExplanationLatencyMs"] = phase6_latency_ms

    total_latency_ms = int((time.time() - total_start_time) * 1000)
    telemetry["totalLatencyMs"] = total_latency_ms
    telemetry["totalTimeMs"] = total_latency_ms

    w = req.weights or {"semantic": 0.5, "skills": 0.25, "career": 0.15, "behavioral": 0.10}
    telemetry["weights"] = w
    telemetry["stage1CandidatesCount"] = telemetry["lexicalCount"] + telemetry["vectorCount"]
    telemetry["stage1TimeMs"] = telemetry.get("lexicalTimeMs", 0)
    telemetry["stage2TimeMs"] = telemetry.get("vectorTimeMs", 0)
    telemetry["stage3CandidatesCount"] = len(final_candidates)
    telemetry["stage3RerankTimeMs"] = rerank_telemetry.get("rerankTimeMs", phase5_latency_ms)
    telemetry["rerankerModel"] = rerank_telemetry.get("modelName", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    telemetry["totalCandidates"] = telemetry.get("totalCandidates", 0)

    return {
        "success": True,
        "data": {
            "topCandidates": final_candidates,
            "parsedFeatures": parsed_features,
            "telemetry": telemetry,
        }
    }


@router.post("/explain")
def explain_candidate(req: ExplainRequest):
    """
    Phase 6 Grounded Gemini Recruiter RAG Explanation Endpoint:
    Provides structured, evidence-backed evaluation for an already-ranked candidate.
    Gemini does NOT rank or change candidate scores.
    """
    candidate = req.candidate
    jd_text = req.jobDescriptionText

    if not candidate or not jd_text:
        raise HTTPException(status_code=400, detail="Missing candidate or job description")

    explanation_start = time.time()
    explanation = generate_grounded_explanation(
        job_description=jd_text,
        candidate=candidate,
        evidence_chunks=req.evidenceChunks,
    )
    explanation_time_ms = int((time.time() - explanation_start) * 1000)

    return {
        "success": True,
        "reasoning": explanation.summary,
        "explanation": explanation.model_dump(),
        "latencyMs": explanation_time_ms,
    }


@router.post("/export-csv")
def export_csv(payload: Dict[str, Any]):
    candidates = payload.get("candidates", [])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Candidate ID", "Name", "Headline", "Experience Years",
        "Education", "Skills", "Final Score", "Cross-Encoder Score", "RRF Score",
        "Lexical Rank", "Vector Rank", "Reasoning"
    ])

    for c in candidates:
        scores = c.get("scores", {})
        writer.writerow([
            c.get("rank", ""),
            c.get("candidate_id", ""),
            c.get("name", ""),
            c.get("headline", ""),
            c.get("experience_years", ""),
            c.get("education", ""),
            ", ".join(c.get("skills", [])),
            scores.get("finalScore", ""),
            c.get("cross_encoder_score", ""),
            c.get("rrf_score", ""),
            c.get("lexical_rank", ""),
            c.get("vector_rank", ""),
            c.get("reasoning", "")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=matched_talent_export.csv"}
    )
