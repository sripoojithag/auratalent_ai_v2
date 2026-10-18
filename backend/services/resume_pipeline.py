import uuid
import hashlib
import psycopg

from pgvector.psycopg import register_vector

from backend.config import settings
from backend.services.pdf_extractor import extract_text_from_pdf
from backend.services.chunker import chunk_resume_pages, TextChunk
from backend.services.extraction_service import (
    extract_candidate_profile_with_gemini,
)
from backend.services.embedding_service import (
    generate_batch_embeddings,
    EMBEDDING_DIMENSIONS,
)
from backend.schemas import IngestionJobResult


def process_resume_pdf(buffer: bytes, filename: str) -> IngestionJobResult:
    """
    Executes the complete Python PDF Resume Ingestion Pipeline:

    1. PDF Byte Extraction -> raw text + pages (pypdf)
    2. Section-Aware Recursive Chunking -> text chunks
    3. Embedding Generation -> genuine 768-d vectors for EVERY chunk (Gemini)
    4. Gemini Structured Profile Extraction -> CandidateStructuredProfile
    5. PostgreSQL Persistence -> candidates, resumes, resume_chunks, skills
    """

    # ---------------------------------------------------------
    # 0. Calculate SHA-256 hash and check for exact duplicate
    # ---------------------------------------------------------
    file_hash = hashlib.sha256(buffer).hexdigest()

    with psycopg.connect(settings.conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT candidate_id, id
                FROM resumes
                WHERE file_hash = %s;
                """,
                (file_hash,),
            )

            existing_resume = cur.fetchone()

    if existing_resume:
        raise ValueError(
            f"This exact resume has already been uploaded. "
            f"Existing candidate: {existing_resume[0]}"
        )

    # ---------------------------------------------------------
    # 1. Extract text from PDF
    # ---------------------------------------------------------
    extraction = extract_text_from_pdf(buffer)

    if not extraction.has_sufficient_text:
        raise ValueError(
            f"Failed to extract text from {filename}: "
            f"file contains insufficient text "
            f"({len(extraction.full_text)} characters). "
            f"Ensure the PDF contains readable text."
        )

    # ---------------------------------------------------------
    # 2. Section & Page Chunking
    # ---------------------------------------------------------
    chunks = chunk_resume_pages(extraction.pages)

    if not chunks:
        chunks.append(
            TextChunk(
                chunk_index=0,
                section_name="General",
                page_number=1,
                content=extraction.full_text[:1000],
            )
        )

    # ---------------------------------------------------------
    # 3. Generate Genuine 768-d Semantic Embeddings
    # ---------------------------------------------------------
    print(
        f"Generating 768-d embeddings for "
        f"{len(chunks)} chunks from {filename}..."
    )

    chunk_texts = [
        f"{c.section_name}: {c.content}"
        for c in chunks
    ]

    embeddings = generate_batch_embeddings(chunk_texts)

    # Validate embeddings
    for idx, vec in enumerate(embeddings):
        if not vec or len(vec) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Failed to generate valid 768-dimension embedding "
                f"for chunk {idx} of {filename}. "
                f"Received {len(vec) if vec else 0} dimensions."
            )

    # ---------------------------------------------------------
    # 4. Structured Extraction via Gemini 2.5 Flash
    # ---------------------------------------------------------
    profile = extract_candidate_profile_with_gemini(
        extraction.full_text,
        filename,
    )

    print(
        f"Extracted candidate: "
        f"{profile.fullName} | "
        f"{profile.email} | "
        f"{profile.phone}"
    )

    # ---------------------------------------------------------
    # 5. Transactional PostgreSQL Persistence
    # ---------------------------------------------------------
    new_candidate_id = None

    with psycopg.connect(settings.conn_info) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            try:

                # -------------------------------------------------
                # Insert Candidate
                # -------------------------------------------------
                candidate_id = str(uuid.uuid4())

                full_name = (
                    profile.fullName
                    or filename.replace(".pdf", "")
                )

                headline = (
                    profile.headline
                    or "Software Professional"
                )

                total_exp = str(
                    profile.totalExperienceYears or 0.0
                )

                cur.execute(
                    """
                    INSERT INTO candidates (
                        id,
                        full_name,
                        email,
                        phone,
                        location,
                        headline,
                        summary,
                        total_experience_years,
                        created_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                    RETURNING id;
                    """,
                    (
                        candidate_id,
                        full_name,
                        profile.email,
                        profile.phone,
                        profile.location,
                        headline,
                        profile.summary,
                        total_exp,
                    ),
                )

                new_candidate_id = cur.fetchone()[0]

                # -------------------------------------------------
                # Insert Resume
                # -------------------------------------------------
                resume_id = str(uuid.uuid4())

                file_path = (
                    f"uploads/{new_candidate_id}_{filename}"
                )

                cur.execute(
                    """
                    INSERT INTO resumes (
                        id,
                        candidate_id,
                        filename,
                        file_size_bytes,
                        file_hash,
                        file_path,
                        raw_text,
                        processing_status,
                        created_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        'completed', NOW()
                    )
                    RETURNING id;
                    """,
                    (
                        resume_id,
                        new_candidate_id,
                        filename,
                        len(buffer),
                        file_hash,
                        file_path,
                        extraction.full_text,
                    ),
                )

                new_resume_id = cur.fetchone()[0]

                # -------------------------------------------------
                # Insert Resume Chunks + 768-d Embeddings
                # -------------------------------------------------
                for i, chunk in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())

                    cur.execute(
                        """
                        INSERT INTO resume_chunks (
                            id,
                            resume_id,
                            candidate_id,
                            chunk_index,
                            section_name,
                            page_number,
                            content,
                            embedding,
                            created_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, NOW()
                        );
                        """,
                        (
                            chunk_id,
                            new_resume_id,
                            new_candidate_id,
                            chunk.chunk_index,
                            chunk.section_name,
                            chunk.page_number,
                            chunk.content,
                            embeddings[i],
                        ),
                    )

                # -------------------------------------------------
                # Upsert Skills and Map to Candidate
                # -------------------------------------------------
                skill_count = 0

                for s in profile.skills:
                    if not s.name or not s.name.strip():
                        continue

                    clean_name = s.name.strip()
                    skill_id = str(uuid.uuid4())
                    category = s.category or "general"

                    cur.execute(
                        """
                        INSERT INTO skills (
                            id,
                            name,
                            category
                        )
                        VALUES (%s, %s, %s)
                        ON CONFLICT (name)
                        DO UPDATE SET
                            category = EXCLUDED.category
                        RETURNING id;
                        """,
                        (
                            skill_id,
                            clean_name,
                            category,
                        ),
                    )

                    canonical_skill_id = cur.fetchone()[0]

                    cand_skill_id = str(uuid.uuid4())

                    years_exp = (
                        str(s.yearsExperience)
                        if s.yearsExperience
                        else None
                    )

                    cur.execute(
                        """
                        INSERT INTO candidate_skills (
                            id,
                            candidate_id,
                            skill_id,
                            years_experience
                        )
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (
                            cand_skill_id,
                            new_candidate_id,
                            canonical_skill_id,
                            years_exp,
                        ),
                    )

                    skill_count += 1

                # -------------------------------------------------
                # Insert Candidate Experiences
                # -------------------------------------------------
                for exp in profile.experiences:
                    if not exp.jobTitle or not exp.company:
                        continue

                    exp_id = str(uuid.uuid4())

                    cur.execute(
                        """
                        INSERT INTO candidate_experiences (
                            id,
                            candidate_id,
                            job_title,
                            company,
                            start_date,
                            end_date,
                            is_current,
                            description
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s
                        );
                        """,
                        (
                            exp_id,
                            new_candidate_id,
                            exp.jobTitle,
                            exp.company,
                            exp.startDate,
                            exp.endDate,
                            bool(exp.isCurrent),
                            exp.description,
                        ),
                    )

                # -------------------------------------------------
                # Commit entire transaction
                # -------------------------------------------------
                conn.commit()

                return IngestionJobResult(
                    candidateId=str(new_candidate_id),
                    resumeId=str(new_resume_id),
                    fullName=full_name,
                    headline=headline,
                    totalExperienceYears=float(total_exp),
                    extractedSkillsCount=skill_count,
                    chunksCount=len(chunks),
                    totalPages=extraction.total_pages,
                    embeddingDimensions=EMBEDDING_DIMENSIONS,
                    status="completed",
                )

            except Exception as e:
                conn.rollback()
                raise e