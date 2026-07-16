"""
Ollama wrapper with robust JSON extraction from LLM output.
Temperature is kept low (0.1) for deterministic legal analysis.
"""
from __future__ import annotations

import json
import re
import time

import ollama

from .models import AnalysisResult, Citation
from config import settings


def _extract_json(raw: str) -> dict:
    """Parse JSON from LLM response, handling markdown code fences."""
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Last resort: find first {...} block in the response
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))

    raise ValueError(f"No valid JSON in LLM response. First 400 chars:\n{raw[:400]}")


def analyze(system_prompt: str, user_message: str, retrieved_count: int) -> AnalysisResult:
    t0 = time.monotonic()

    response = ollama.chat(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        options={"temperature": 0.1},
    )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    data = _extract_json(response["message"]["content"])

    citations = [
        Citation(
            article_ref=c.get("article_ref", ""),
            law_name=c.get("law_name", ""),
            text=c.get("text", ""),
            relevance_score=float(c.get("relevance_score", 0.0)),
        )
        for c in data.get("citations", [])
    ]

    return AnalysisResult(
        flag_recommended=bool(data["flag_recommended"]),
        confidence=float(data.get("confidence", 0.0)),
        citations=citations,
        reasoning=data.get("reasoning", ""),
        recommendation=data.get("recommendation", ""),
        model_used=settings.llm_model,
        retrieved_chunks=retrieved_count,
        processing_time_ms=elapsed_ms,
    )
