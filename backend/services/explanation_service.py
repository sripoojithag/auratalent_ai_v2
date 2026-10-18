"""
Phase 6: Grounded Gemini Explanations / Recruiter RAG Service
Generates evidence-backed explanations for candidates ranked by Phase 5.

Critical Principles:
1. Gemini NEVER ranks candidates or changes ranking order/scores.
2. Ranking order and scores (RRF, Cross-Encoder) are strictly authoritative from Phase 4 & 5.
3. Every piece of matching evidence MUST be grounded in real candidate database records
   (resume chunks, extracted skills, career history, headline/summary).
4. No hallucinations or synthetic candidate/evidence data. If evidence is insufficient,
   Gemini explicitly reports that evidence is insufficient.
5. Evidence references are strictly mapped to actual database chunk IDs or real candidate data.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from backend.config import settings
from backend.database import get_db_connection


class MatchingEvidenceItem(BaseModel):
    evidence_type: str = Field(description="Type of evidence: 'resume_chunk', 'skill', 'experience', or 'summary'")
    text: str = Field(description="Exact or directly extracted snippet supporting the qualification")
    source_chunk_id: Optional[str] = Field(default=None, description="Actual UUID of the supporting chunk from DB if available")
    section_name: Optional[str] = Field(default=None, description="Resume section (e.g., 'Work Experience', 'Skills', 'Education')")
    page_number: Optional[int] = Field(default=None, description="Page number of the resume chunk")


class CandidateExplanation(BaseModel):
    candidate_id: str
    rank: int
    rrf_score: float
    cross_encoder_score: float
    summary: str = Field(description="Concise 2-sentence executive summary of candidate fit based strictly on supplied evidence")
    matching_evidence: List[MatchingEvidenceItem] = Field(default_factory=list, description="Ground truth evidence excerpts")
    strengths: List[str] = Field(default_factory=list, description="Top concrete strengths supported by evidence")
    gaps_or_missing_evidence: List[str] = Field(default_factory=list, description="Requisition criteria with missing or unverified evidence")
    confidence: str = Field(default="high", description="Level of evidential support: 'high', 'moderate', or 'insufficient_evidence'")
    error: Optional[str] = None


def fetch_candidate_evidence_chunks(candidate_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves real resume chunk evidence from PostgreSQL for the candidate.
    Uses only existing schema: resume_chunks JOIN resumes.
    """
    query = """
        SELECT 
            rc.id::text as chunk_id,
            rc.section_name,
            rc.page_number,
            rc.content,
            r.filename
        FROM resume_chunks rc
        JOIN resumes r ON rc.resume_id = r.id
        WHERE r.candidate_id = %s
        ORDER BY rc.chunk_index ASC
        LIMIT %s;
    """
    for conn in get_db_connection():
        with conn.cursor() as cur:
            cur.execute(query, (candidate_id, limit))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    return []


def generate_grounded_explanation(
    job_description: str,
    candidate: Dict[str, Any],
    evidence_chunks: Optional[List[Dict[str, Any]]] = None,
    client: Optional[genai.Client] = None,
) -> CandidateExplanation:
    """
    Generates a structured, evidence-grounded explanation for an already-ranked candidate.
    Preserves candidate rank, RRF score, and Cross-Encoder score from Phase 4 & 5.
    """
    candidate_id = str(candidate.get("candidate_id") or candidate.get("id") or "")
    rank = int(candidate.get("rank") or candidate.get("rerank_position") or 1)
    rrf_score = float(candidate.get("rrf_score", 0.0))
    cross_encoder_score = float(candidate.get("cross_encoder_score", 0.0))

    # Retrieve real chunks if not supplied in candidate profile
    if evidence_chunks is None:
        matched_chunks = candidate.get("matched_chunks", [])
        if matched_chunks:
            evidence_chunks = [
                {
                    "chunk_id": str(mc.get("chunk_id", "")),
                    "section_name": mc.get("section_name", "Resume"),
                    "page_number": mc.get("page_number", 1),
                    "content": mc.get("content", ""),
                }
                for mc in matched_chunks
            ]
        elif candidate_id:
            try:
                evidence_chunks = fetch_candidate_evidence_chunks(candidate_id, limit=5)
            except Exception as e:
                print(f"[ExplanationService] DB chunk fetch error for {candidate_id}: {e}")
                evidence_chunks = []
        else:
            evidence_chunks = []

    # Map verified chunk IDs for validation against hallucinations
    valid_chunk_map = {
        c["chunk_id"]: c for c in (evidence_chunks or []) if c.get("chunk_id")
    }

    # Extract real profile fields
    headline = candidate.get("headline", "Not specified")
    summary = candidate.get("summary", "")
    skills = candidate.get("skills", [])
    if isinstance(skills, list):
        skills_str = ", ".join(str(s) for s in skills)
    else:
        skills_str = str(skills)
    experience_years = candidate.get("experience_years", candidate.get("total_experience_years", 0.0))
    education = candidate.get("education", "Not specified")
    career_history = candidate.get("career_history", [])

    # Check for empty / insufficient data
    has_meaningful_evidence = bool(
        evidence_chunks or skills or (career_history and len(career_history) > 0) or summary
    )
    if not has_meaningful_evidence:
        return CandidateExplanation(
            candidate_id=candidate_id,
            rank=rank,
            rrf_score=rrf_score,
            cross_encoder_score=cross_encoder_score,
            summary="Insufficient evidence available in the candidate's records to formulate an evaluation.",
            matching_evidence=[],
            strengths=[],
            gaps_or_missing_evidence=["Complete resume profile or excerpts missing from database."],
            confidence="insufficient_evidence",
        )

    # Format evidence excerpts for Gemini prompt
    evidence_text_blocks = []
    for idx, chunk in enumerate(evidence_chunks or [], start=1):
        cid = chunk.get("chunk_id", f"ref_{idx}")
        sec = chunk.get("section_name", "General")
        page = chunk.get("page_number", 1)
        cnt = chunk.get("content", "").strip()
        evidence_text_blocks.append(
            f"[CHUNK ID: {cid} | SECTION: {sec} | PAGE: {page}]\n{cnt}"
        )
    evidence_payload_str = "\n\n".join(evidence_text_blocks) if evidence_text_blocks else "No resume text chunks indexed."

    prompt = f"""You are a professional recruiting analyst providing a strictly evidence-grounded explanation for a candidate match.

CRITICAL INSTRUCTIONS:
1. Base your explanation SOLELY on the supplied Candidate Profile and Resume Evidence Chunks below.
2. DO NOT invent, hallucinate, or assume any skills, companies, tools, achievements, or tenure.
3. If specific required qualifications from the job description are not directly stated in the evidence, list them under 'gaps_or_missing_evidence'.
4. For each item in 'matching_evidence', provide:
   - 'evidence_type': one of 'resume_chunk', 'skill', 'experience', 'summary'
   - 'text': the specific text or quote from the evidence
   - 'source_chunk_id': MUST match one of the exact CHUNK IDs provided (e.g. from [CHUNK ID: ...]) if citing a resume chunk, or null if from skills/profile.
   - 'section_name': the section name if from a chunk, or null.
   - 'page_number': the integer page number if from a chunk, or null.
5. DO NOT score or change the candidate's rank. Ranking has already been completed by Phase 5 Cross-Encoder.
6. If the evidence is weak or missing core requirements, explicitly state confidence as 'insufficient_evidence' or 'moderate'.

Target Job Description:
{job_description}

Candidate Profile:
- ID: {candidate_id}
- Headline: {headline}
- Experience: {experience_years} years
- Skills: {skills_str}
- Education: {education}
- Summary: {summary}

Resume Evidence Chunks:
{evidence_payload_str}
"""

    api_key = settings.gemini_api_key
    if not api_key:
        # Graceful fallback when API key is missing (without hallucinating)
        return CandidateExplanation(
            candidate_id=candidate_id,
            rank=rank,
            rrf_score=rrf_score,
            cross_encoder_score=cross_encoder_score,
            summary=f"Candidate profile shows {experience_years} years experience with skills: {skills_str[:120]}. (AI explanation unconfigured)",
            matching_evidence=[
                MatchingEvidenceItem(
                    evidence_type="skill",
                    text=f"Skills recorded in profile: {skills_str[:100]}",
                )
            ] if skills else [],
            strengths=[f"Verified skills: {skills_str[:80]}"] if skills else [],
            gaps_or_missing_evidence=["AI explanation model requires GEMINI_API_KEY."],
            confidence="moderate",
            error="GEMINI_API_KEY not configured",
        )

    try:
        genai_client = client or genai.Client(api_key=api_key)
        response = genai_client.models.generate_content(
            model=settings.extraction_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateExplanation,
                temperature=0.1,  # Low temperature for strict adherence to facts
            ),
        )

        response_text = response.text.strip()
        parsed_data = json.loads(response_text)

        # Enforce ranking integrity: overwrite any hallucinated rank or score fields
        parsed_data["candidate_id"] = candidate_id
        parsed_data["rank"] = rank
        parsed_data["rrf_score"] = rrf_score
        parsed_data["cross_encoder_score"] = cross_encoder_score

        # Validate evidence references against real chunks
        sanitized_evidence: List[MatchingEvidenceItem] = []
        for ev in parsed_data.get("matching_evidence", []):
            cid = ev.get("source_chunk_id")
            if cid:
                if cid in valid_chunk_map:
                    # Verified real chunk reference
                    real_c = valid_chunk_map[cid]
                    sanitized_evidence.append(
                        MatchingEvidenceItem(
                            evidence_type=ev.get("evidence_type", "resume_chunk"),
                            text=ev.get("text", real_c.get("content", "")[:200]),
                            source_chunk_id=cid,
                            section_name=real_c.get("section_name"),
                            page_number=real_c.get("page_number"),
                        )
                    )
                else:
                    # Hallucinated or invalid chunk ID -> downgrade to un-chunked reference
                    sanitized_evidence.append(
                        MatchingEvidenceItem(
                            evidence_type="experience",
                            text=ev.get("text", ""),
                            source_chunk_id=None,
                            section_name=None,
                            page_number=None,
                        )
                    )
            else:
                sanitized_evidence.append(
                    MatchingEvidenceItem(
                        evidence_type=ev.get("evidence_type", "skill"),
                        text=ev.get("text", ""),
                        source_chunk_id=None,
                        section_name=None,
                        page_number=None,
                    )
                )

        parsed_data["matching_evidence"] = [e.model_dump() for e in sanitized_evidence]
        return CandidateExplanation(**parsed_data)

    except Exception as e:
        print(f"[ExplanationService] Error generating Gemini explanation for candidate {candidate_id}: {e}")
        return CandidateExplanation(
            candidate_id=candidate_id,
            rank=rank,
            rrf_score=rrf_score,
            cross_encoder_score=cross_encoder_score,
            summary=f"Automated evaluation encountered an error: {str(e)}",
            matching_evidence=[],
            strengths=[f"Documented skills: {skills_str[:80]}"] if skills else [],
            gaps_or_missing_evidence=["Could not complete AI evaluation due to service error."],
            confidence="insufficient_evidence",
            error=str(e),
        )


def batch_explain_top_candidates(
    job_description: str,
    top_candidates: List[Dict[str, Any]],
    client: Optional[genai.Client] = None,
) -> List[Dict[str, Any]]:
    """
    Generates explanations for the top ranked candidates from Phase 5 (up to 15).
    Guarantees that input candidate order and scores are 100% preserved.
    """
    if not top_candidates:
        return []

    client_instance = client or (genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None)
    explained_candidates: List[Dict[str, Any]] = []

    for cand in top_candidates:
        cand_copy = dict(cand)
        explanation = generate_grounded_explanation(
            job_description=job_description,
            candidate=cand,
            client=client_instance,
        )
        cand_copy["explanation"] = explanation.model_dump()
        # Keep reasoning string updated for backward compatibility with existing UI
        cand_copy["reasoning"] = explanation.summary
        explained_candidates.append(cand_copy)

    return explained_candidates
