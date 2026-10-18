from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
import psycopg
from pgvector.psycopg import register_vector
from backend.config import settings
from backend.services.resume_pipeline import process_resume_pdf
from backend.schemas import ResumeUploadResponse, CandidateListResponse, CandidateListItem

router = APIRouter(prefix="/api", tags=["Resumes & Candidates"])


@router.post("/resumes/upload", response_model=ResumeUploadResponse)
async def upload_resumes(resumes: List[UploadFile] = File(...)):
    if not resumes:
        raise HTTPException(status_code=400, detail="No PDF resume files uploaded.")

    results = []
    errors = []

    for file in resumes:
        try:
            if not file.filename.lower().endswith(".pdf"):
                errors.append({"filename": file.filename, "error": "Only PDF files are supported."})
                continue

            content = await file.read()
            print(f"FastAPI processing real resume upload: {file.filename} ({len(content)} bytes)")
            result = process_resume_pdf(content, file.filename)
            results.append(result)
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})

    return ResumeUploadResponse(
        success=len(results) > 0,
        processedCount=len(results),
        failedCount=len(errors),
        results=results,
        errors=errors,
    )


@router.get("/candidates", response_model=CandidateListResponse)
def get_candidates():
    try:
        with psycopg.connect(settings.conn_info) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        c.id::text, c.full_name, c.email, c.phone, c.location, c.headline, c.summary, 
                        c.total_experience_years::text, c.created_at::text,
                        r.id::text as resume_id, r.filename, r.file_size_bytes, r.processing_status,
                        COUNT(DISTINCT rc.id)::int as chunk_count,
                        ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as skills
                    FROM candidates c
                    LEFT JOIN resumes r ON r.candidate_id = c.id
                    LEFT JOIN resume_chunks rc ON rc.candidate_id = c.id
                    LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
                    LEFT JOIN skills s ON s.id = cs.skill_id
                    GROUP BY c.id, r.id
                    ORDER BY c.created_at DESC
                    LIMIT 100;
                    """
                )
                rows = cur.fetchall()
                candidates_list = []
                for row in rows:
                    candidates_list.append(
                        CandidateListItem(
                            id=row[0],
                            full_name=row[1],
                            email=row[2],
                            phone=row[3],
                            location=row[4],
                            headline=row[5],
                            summary=row[6],
                            total_experience_years=row[7],
                            created_at=row[8],
                            resume_id=row[9],
                            filename=row[10],
                            file_size_bytes=row[11],
                            processing_status=row[12],
                            chunk_count=row[13] or 0,
                            skills=row[14] if row[14] else [],
                        )
                    )

                return CandidateListResponse(
                    success=True,
                    candidates=candidates_list,
                )
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
