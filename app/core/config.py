import os
from dataclasses import dataclass

@dataclass
class Settings:
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    db_path: str = os.environ.get("DB_PATH", os.path.expanduser("~/.llm-coach/db.sqlite"))
    scenarios_dir: str = os.environ.get("SCENARIOS_DIR", os.path.expanduser("~/llm-coach/scenarios"))

settings = Settings()
