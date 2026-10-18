from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.evaluation.ranking_metrics import evaluate_ranking_run

router = APIRouter(prefix="/api/evaluation", tags=["Ranking Evaluation"])


class EvaluationRequest(BaseModel):
    predicted_candidate_ids: List[str] = Field(
        ..., min_length=1, description="Candidate IDs in ranked order"
    )
    relevance_grades: Dict[str, int] = Field(
        ...,
        description="Human-reviewed relevance grades: 0=irrelevant, 1=low, 2=good, 3=high"
    )
    cutoffs: List[int] = Field(default_factory=lambda: [5, 10, 15])

    @model_validator(mode="after")
    def validate_evaluation_data(self):
        if not self.relevance_grades:
            raise ValueError("At least one relevance judgment is required.")

        if any(not candidate_id.strip() for candidate_id in self.predicted_candidate_ids):
            raise ValueError("Candidate IDs cannot be empty.")

        if any(not candidate_id.strip() for candidate_id in self.relevance_grades):
            raise ValueError("Relevance-label candidate IDs cannot be empty.")

        if any(grade not in (0, 1, 2, 3) for grade in self.relevance_grades.values()):
            raise ValueError("Relevance grades must be integers from 0 to 3.")

        if not self.cutoffs or any(k <= 0 for k in self.cutoffs):
            raise ValueError("Cutoffs must contain positive integers.")

        if len(set(self.cutoffs)) != len(self.cutoffs):
            raise ValueError("Cutoffs cannot contain duplicates.")

        return self


@router.post("/run")
def run_ranking_evaluation(req: EvaluationRequest):
    """
    Evaluate an existing ranked list against supplied relevance judgments.

    This endpoint does not generate rankings or verify labels against a
    database. The caller is responsible for supplying verified judgments.
    """
    graded_relevance = req.relevance_grades
    relevant_ids = {
        candidate_id
        for candidate_id, grade in graded_relevance.items()
        if grade > 0
    }

    try:
        metrics = evaluate_ranking_run(
            predicted_ids=req.predicted_candidate_ids,
            relevant_ids=relevant_ids,
            graded_relevance=graded_relevance,
            cutoffs=req.cutoffs,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "success": True,
        "evaluation_type": "ranking_metrics",
        "label_source": "caller_supplied_not_independently_verified",
        "metrics": metrics,
    }