VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv install up down ingest ingest-file api ui pull-model

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

up:
	docker compose up -d qdrant

down:
	docker compose down

pull-model:
	ollama pull qwen2.5:3b

ingest:
	$(PYTHON) -m ingest.pipeline

ingest-file:
	$(PYTHON) -m ingest.pipeline --source $(SOURCE) --law-name "$(NAME)"

api:
	$(VENV)/bin/uvicorn api.main:app --reload --port 8000

ui:
	$(VENV)/bin/streamlit run ui/app.py --server.port 8501 --browser.gatherUsageStats false
