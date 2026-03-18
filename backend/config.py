from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "qwen/qwen3-coder:free"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    DATABASE_PATH: str = str(Path(__file__).parent.parent / "data" / "ai_dynamics.db")

    @property
    def use_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def use_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def use_openrouter(self) -> bool:
        return bool(self.OPENROUTER_API_KEY)

    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
