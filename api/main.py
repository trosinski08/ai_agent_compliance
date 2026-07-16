from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent.agent import run_analysis
from agent.models import AnalysisResult, CaseInput

app = FastAPI(
    title="AML Compliance Agent",
    description=(
        "Lokalny agent RAG wspomagający analityków AML/KYC. "
        "Dane przetwarzane wyłącznie lokalnie — brak wysyłania do chmury."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit UI
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
def analyze_case(case: CaseInput) -> AnalysisResult:
    try:
        return run_analysis(case)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy: {e}")
