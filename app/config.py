from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8766
    data_dir: str = "./data"
    secret_key: str = "athena-dev-secret-troque-antes-de-producao"
    session_hours: int = 8
    inactivity_lock_minutes: int = 10
    log_level: str = "INFO"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_model: str = "deepseek-r1-distill-qwen-14b"
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
