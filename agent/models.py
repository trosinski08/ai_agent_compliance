from pydantic import BaseModel, Field


class CaseInput(BaseModel):
    description: str = Field(
        ...,
        min_length=20,
        description=(
            "Opis sytuacji transakcyjnej lub behawioralnej. "
            "Nie podawaj danych osobowych (imię, PESEL, numer rachunku)."
        ),
    )
    analyst_id: str = Field(default="anonymous", description="ID analityka do logu audytowego")


class Citation(BaseModel):
    article_ref: str
    law_name: str
    text: str
    relevance_score: float


class AnalysisResult(BaseModel):
    flag_recommended: bool
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation]
    reasoning: str
    recommendation: str
    model_used: str
    retrieved_chunks: int
    processing_time_ms: int
