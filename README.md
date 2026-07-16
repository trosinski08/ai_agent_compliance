# AML Compliance Agent — lokalny RAG na polskich przepisach

Agent AI wspomagający analityków AML/KYC w decyzji o flagowaniu spraw. Całość działa lokalnie — żadne dane nie opuszczają maszyny.

## Stack

| Warstwa | Technologia |
|---|---|
| LLM | [Ollama](https://ollama.com) + `qwen2.5:3b` (domyślnie) / `bielik` (dla PL) |
| Embeddingi | `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers) |
| Baza wektorowa | [Qdrant](https://qdrant.tech) — lokalny plik, bez serwera |
| Parser PDF | PyMuPDF + pdfplumber |
| API | FastAPI |
| UI | Streamlit |

## Workflow

```
PDF ustaw → parse → chunk (per artykuł) → embed → Qdrant
                                                       ↓
Analityk opisuje sprawę → embed → retrieval top-k → prompt + LLM → decyzja + cytaty
```

## Instalacja

```bash
# 1. Zależności Python
make install

# 2. Ollama (wymaga sudo)
curl -fsSL https://ollama.com/install.sh | sh
make pull-model   # pobiera qwen2.5:3b (~1.9 GB)
```

## Ingest bazy prawnej

Wrzuć PDF z ustawą do `knowledge_base/`, dodaj wpis w `ingest/sources.py`, a następnie:

```bash
make ingest
```

Lub jednorazowo bez edytowania sources.py:

```bash
make ingest-file SOURCE=knowledge_base/ustawa_aml.pdf NAME="Ustawa AML 2018"
```

Priorytety dokumentów do zaindeksowania:

| Priorytet | Dokument | Źródło |
|---|---|---|
| P1 | Ustawa AML 2018 (Dz.U. 2018 poz. 723) | isap.sejm.gov.pl |
| P1 | Wytyczne GIIF | giif.mf.gov.pl |
| P2 | Rekomendacje KNF AML | knf.gov.pl |
| P2 | Ustawa RODO PL 2018 | isap.sejm.gov.pl |
| P3 | Dyrektywy UE 5AMLD/6AMLD | EUR-Lex |

## Uruchomienie

```bash
# terminal 1
ollama serve

# terminal 2 — API (http://localhost:8000/docs)
make api

# terminal 3 — UI (http://localhost:8501)
make ui
```

## Konfiguracja

Skopiuj `.env.example` do `.env` i dostosuj:

```bash
cp .env.example .env
```

Kluczowe zmienne:

```env
# Szybki model (dev): 384-dim, ~2 min na 150 chunków
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# Jakościowy model (prod): 1024-dim, najlepszy dla PL, ~20 min na 150 chunków na CPU
# EMBEDDING_MODEL=sdadas/mmlw-retrieval-roberta-large

LLM_MODEL=qwen2.5:3b   # lub: bielik (wymaga ~8 GB RAM)

RETRIEVAL_TOP_K=6
RETRIEVAL_SCORE_THRESHOLD=0.60
```

## Struktura projektu

```
├── config.py              # ustawienia (pydantic-settings, .env)
├── ingest/
│   ├── parser.py          # PDF/HTML → tekst (PyMuPDF + pdfplumber)
│   ├── chunker.py         # podział po Art. N., fallback char-split
│   ├── embedder.py        # sentence-transformers, auto-detect dim
│   ├── store.py           # Qdrant CRUD (qdrant-client ≥1.9)
│   ├── sources.py         # rejestr ustaw do zaindeksowania
│   └── pipeline.py        # skrypt CLI: python -m ingest.pipeline
├── agent/
│   ├── models.py          # CaseInput, Citation, AnalysisResult (Pydantic)
│   ├── retriever.py       # embed query → Qdrant top-k
│   ├── prompt.py          # system prompt + template kontekstu prawnego
│   ├── llm.py             # Ollama chat + JSON extraction
│   └── agent.py           # pipeline: retrieve → prompt → LLM → wynik
├── api/main.py            # FastAPI: POST /analyze, GET /health
├── ui/app.py              # Streamlit: formularz + wynik + cytaty
└── knowledge_base/        # PDFs ustaw (lokalnie, nie w repo)
```

## RODO / Bezpieczeństwo

- Opis sprawy podawany przez analityka **nie może zawierać danych osobowych** (nazwiska, PESEL, numery rachunków) — tylko opis zachowania/transakcji.
- Żadne dane nie są wysyłane do zewnętrznych API — LLM, embeddingi i baza wektorowa działają lokalnie.
- `qdrant_storage/` i `knowledge_base/*.pdf` są w `.gitignore`.
