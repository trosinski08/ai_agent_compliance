SYSTEM_PROMPT = """\
Jesteś ekspertem ds. compliance AML/KYC specjalizującym się w polskich przepisach prawnych.
Analizujesz opisane sytuacje pod kątem przepisów o przeciwdziałaniu praniu pieniędzy (AML) \
i finansowaniu terroryzmu (CFT).

Na podstawie dostarczonych fragmentów przepisów:
1. Oceń czy sytuacja powinna skutkować flagowaniem sprawy (np. SAR do GIIF)
2. Wskaż konkretne artykuły uzasadniające decyzję
3. Podaj pewność oceny jako liczba 0.0–1.0
4. Zaproponuj rekomendowane działanie analityka

Zasady:
- Bazuj WYŁĄCZNIE na dostarczonych przepisach
- Jeśli przepisy są niewystarczające — obniż pewność i zaznacz to w uzasadnieniu
- Zwróć WYŁĄCZNIE poprawny JSON, bez żadnego dodatkowego tekstu

Wymagany format odpowiedzi:
{
  "flag_recommended": true,
  "confidence": 0.85,
  "citations": [
    {
      "article_ref": "Art. 72 ust. 1 pkt 1",
      "law_name": "Ustawa AML 2018",
      "text": "cytat kluczowego fragmentu przepisu",
      "relevance_score": 0.9
    }
  ],
  "reasoning": "Uzasadnienie decyzji w języku polskim.",
  "recommendation": "Rekomendowane działanie analityka."
}
"""

_USER_TEMPLATE = """\
KONTEKST PRAWNY — fragmenty przepisów znalezione przez system RAG:
{legal_context}

---
OPIS SYTUACJI (bez danych osobowych):
{case_description}

Przeanalizuj sytuację względem powyższych przepisów i zwróć JSON.
"""


def build_prompt(case_description: str, chunks: list[dict]) -> tuple[str, str]:
    """Returns (system_prompt, user_message)."""
    parts = []
    for i, c in enumerate(chunks, start=1):
        ref = c.get("article_ref", "")
        law = c.get("law_name", "")
        label = f"[{i}] {law} — {ref}" if ref else f"[{i}] {law}"
        parts.append(f"{label}\n{c['text']}")

    user_msg = _USER_TEMPLATE.format(
        legal_context="\n\n".join(parts),
        case_description=case_description,
    )
    return SYSTEM_PROMPT, user_msg
