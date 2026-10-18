from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# Status & Health Schemas
class DatabaseStatus(BaseModel):
    connected: bool
    engine: str = "PostgreSQL 16 (Cloud SQL)"
    pgvector: str
    realCandidateCount: int = 0
    realResumeCount: int = 0
    realChunkCount: int = 0


class EmbeddingStatus(BaseModel):
    model: str
    dimensions: int
    status: str


class SystemStatusResponse(BaseModel):
    success: bool
    poolSize: int = 100000
    isPoolGenerated: bool = True
    modelStatus: str = "loaded"
    faissStatus: str = "loaded"
    envHasApiKey: bool
    database: DatabaseStatus
    embeddings: EmbeddingStatus


class EmbeddingHealthResponse(BaseModel):
    healthy: bool
    model: str
    dimensions: int
    error: Optional[str] = None


# Profile Extraction Schemas
class ExtractedSkill(BaseModel):
    name: str
    category: Optional[str] = "general"
    yearsExperience: Optional[float] = None


class ExtractedExperience(BaseModel):
    jobTitle: str
    company: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isCurrent: Optional[bool] = False
    description: Optional[str] = None


class CandidateStructuredProfile(BaseModel):
    fullName: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = "Software Professional"
    summary: Optional[str] = None
    totalExperienceYears: float = 0.0
    skills: List[ExtractedSkill] = Field(default_factory=list)
    experiences: List[ExtractedExperience] = Field(default_factory=list)


# Resume Upload Response
class IngestionJobResult(BaseModel):
    candidateId: str
    resumeId: str
    fullName: str
    headline: str
    totalExperienceYears: float
    extractedSkillsCount: int
    chunksCount: int
    totalPages: int
    embeddingDimensions: int
    status: str = "completed"
    error: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    success: bool
    processedCount: int
    failedCount: int
    results: List[IngestionJobResult]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# Candidate List
class CandidateListItem(BaseModel):
    id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    total_experience_years: Optional[Any] = None
    created_at: Optional[Any] = None
    resume_id: Optional[str] = None
    filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    processing_status: Optional[str] = None
    chunk_count: int = 0
    skills: List[str] = Field(default_factory=list)


class CandidateListResponse(BaseModel):
    success: bool
    candidates: List[CandidateListItem]

class CandidateRankScores(BaseModel):
    semanticScore: Optional[float] = None
    skillScore: Optional[float] = None
    careerScore: Optional[float] = None
    behavioralScore: Optional[float] = None
    crossEncoderScore: Optional[float] = None
    rawCrossEncoderScore: Optional[float] = None
    relativeCrossEncoderScore: Optional[float] = None
    finalScore: Optional[float] = None
    relativeScore: Optional[float] = None

class RankedCandidate(BaseModel):
    candidate_id: str
    name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    experience_years: Optional[float] = 0.0
    education: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    scores: CandidateRankScores

    cross_encoder_score: Optional[float] = None
    raw_cross_encoder_score: Optional[float] = None
    relative_cross_encoder_score: Optional[float] = None
    rrf_score: Optional[float] = None

    rank: Optional[int] = None
    rerank_position: Optional[int] = None
    reasoning: Optional[str] = None