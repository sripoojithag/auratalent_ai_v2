from fastapi import APIRouter, Response, status
import psycopg
from pgvector.psycopg import register_vector
from backend.config import settings
from backend.schemas import SystemStatusResponse, DatabaseStatus, EmbeddingStatus, EmbeddingHealthResponse
from backend.services.embedding_service import check_embedding_service_health, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS

router = APIRouter(prefix="/api", tags=["Status & Health"])


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status():
    has_api_key = bool(settings.gemini_api_key)
    db_connected = False
    pgvector_version = "Not detected"
    real_candidate_count = 0
    real_resume_count = 0
    real_chunk_count = 0

    try:
        with psycopg.connect(settings.conn_info) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
                row = cur.fetchone()
                if row:
                    db_connected = True
                    pgvector_version = f"Enabled ({row[1]})"

                cur.execute("SELECT COUNT(*) FROM candidates;")
                cand_row = cur.fetchone()
                real_candidate_count = cand_row[0] if cand_row else 0

                cur.execute("SELECT COUNT(*) FROM resumes;")
                res_row = cur.fetchone()
                real_resume_count = res_row[0] if res_row else 0

                cur.execute("SELECT COUNT(*) FROM resume_chunks;")
                chk_row = cur.fetchone()
                real_chunk_count = chk_row[0] if chk_row else 0
    except Exception as e:
        print(f"Cloud SQL db check error: {e}")

    return SystemStatusResponse(
        success=True,
        poolSize=100000,
        isPoolGenerated=True,
        modelStatus="loaded",
        faissStatus="loaded",
        envHasApiKey=has_api_key,
        database=DatabaseStatus(
            connected=db_connected,
            engine="PostgreSQL 16 (Cloud SQL)",
            pgvector=pgvector_version,
            realCandidateCount=real_candidate_count,
            realResumeCount=real_resume_count,
            realChunkCount=real_chunk_count,
        ),
        embeddings=EmbeddingStatus(
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
            status="operational" if has_api_key else "unconfigured",
        ),
    )


@router.get("/embeddings/health", response_model=EmbeddingHealthResponse)
def get_embedding_health(response: Response):
    health_data = check_embedding_service_health()
    if not health_data.get("healthy", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return EmbeddingHealthResponse(**health_data)
