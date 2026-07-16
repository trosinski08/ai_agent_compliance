from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Qdrant: set QDRANT_PATH for local file mode (no Docker needed),
    # or QDRANT_URL for a running server. Path takes priority.
    qdrant_path: str = "./qdrant_storage"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "aml_przepisy"

    # paraphrase-multilingual-MiniLM-L12-v2: 384-dim, fast on CPU, solid multilingual
    # sdadas/mmlw-retrieval-roberta-large: 1024-dim, best Polish quality, ~20min/150chunks on CPU
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_batch_size: int = 32

    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b"

    retrieval_top_k: int = 6
    retrieval_score_threshold: float = 0.60

    model_config = {"env_file": ".env"}


settings = Settings()
