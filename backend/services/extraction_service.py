import os
import re
import json
from typing import Optional
from google import genai
from google.genai import types
from backend.config import settings
from backend.schemas import CandidateStructuredProfile, ExtractedSkill, ExtractedExperience

COMMON_SKILLS = [
    "Python", "PyTorch", "TensorFlow", "React", "TypeScript", "JavaScript",
    "PostgreSQL", "SQL", "Docker", "Kubernetes", "AWS", "GCP", "FastAPI",
    "Django", "Flask", "Node.js", "Redis", "Elasticsearch", "Git", "C++", "Java", "Ray", "pgvector"
]


def deterministic_resume_extraction(raw_text: str, filename: str) -> CandidateStructuredProfile:
    """
    Deterministic fallback parser in case LLM is unconfigured or unavailable.
    """
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    name = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE).replace("_", " ").replace("-", " ")
    for line in lines[:5]:
        if "Page" not in line and len(line) < 50 and "@" not in line:
            name = line
            break

    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw_text)
    email = email_match.group(0) if email_match else None

    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
    phone = phone_match.group(0) if phone_match else None

    exp_match = re.search(r"(\d+)\+?\s*(?:-\s*\d+\s*)?\s*(?:years?|yrs?)\b", raw_text, re.IGNORECASE)
    total_years = float(exp_match.group(1)) if exp_match else 3.0

    detected_skills = []
    for s in COMMON_SKILLS:
        if re.search(rf"\b{re.escape(s)}\b", raw_text, re.IGNORECASE):
            detected_skills.append(ExtractedSkill(name=s, category="technical"))

    if not detected_skills:
        detected_skills.append(ExtractedSkill(name="General Engineering", category="general"))

    return CandidateStructuredProfile(
        fullName=name,
        email=email,
        phone=phone,
        headline="Software & Systems Engineer",
        summary=raw_text[:300].strip(),
        totalExperienceYears=total_years,
        skills=detected_skills,
        experiences=[
            ExtractedExperience(
                jobTitle="Software Engineer",
                company="Technology Solutions",
                description=raw_text[:200]
            )
        ]
    )


def extract_candidate_profile_with_gemini(
    raw_text: str,
    filename: str,
    api_key: Optional[str] = None
) -> CandidateStructuredProfile:
    """
    Extracts structured candidate profile using Gemini 2.5 Flash with Pydantic JSON schema.
    """
    key = api_key or settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY not found; falling back to deterministic extraction.")
        return deterministic_resume_extraction(raw_text, filename)

    prompt = f"""You are a precise technical resume parsing system.
Extract structured candidate details from the following resume text:

Resume Filename: {filename}
Resume Content:
{raw_text[:12000]}

Extract:
1. fullName: The candidate's legal or professional full name
2. email: Candidate's email address if found
3. phone: Candidate's phone number if found
4. location: City, State/Country
5. headline: Candidate's primary title or role
6. summary: Professional summary
7. totalExperienceYears: Estimated total years of experience as a number
8. skills: Array of technical skills, languages, tools, frameworks with category and estimated years
9. experiences: Array of jobTitle, company, startDate, endDate, isCurrent, description
"""

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=settings.extraction_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateStructuredProfile,
                temperature=0.1,
            )
        )

        if not response.text:
            return deterministic_resume_extraction(raw_text, filename)

        parsed_data = json.loads(response.text)
        return CandidateStructuredProfile(**parsed_data)
    except Exception as e:
        print(f"Gemini structured extraction failed: {e}; using deterministic fallback.")
        return deterministic_resume_extraction(raw_text, filename)
