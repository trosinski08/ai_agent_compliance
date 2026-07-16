"""
Full query pipeline: CaseInput → retrieve → prompt → LLM → AnalysisResult
"""
from .llm import analyze
from .models import AnalysisResult, CaseInput, Citation
from .prompt import build_prompt
from .retriever import retrieve
from config import settings


def run_analysis(case: CaseInput) -> AnalysisResult:
    chunks = retrieve(
        query=case.description,
        top_k=settings.retrieval_top_k,
        score_threshold=settings.retrieval_score_threshold,
    )

    if not chunks:
        return AnalysisResult(
            flag_recommended=False,
            confidence=0.0,
            citations=[],
            reasoning=(
                "System nie znalazł wystarczająco dopasowanych przepisów prawnych. "
                "Sprawdź czy baza wiedzy zawiera odpowiednie ustawy (uruchom ingest)."
            ),
            recommendation="Przeprowadź analizę manualnie lub uzupełnij bazę przepisów.",
            model_used=settings.llm_model,
            retrieved_chunks=0,
            processing_time_ms=0,
        )

    system_prompt, user_msg = build_prompt(case.description, chunks)
    return analyze(system_prompt, user_msg, retrieved_count=len(chunks))
