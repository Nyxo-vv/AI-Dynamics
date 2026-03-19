from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEYS: str = ""  # comma-separated multiple keys
    OPENROUTER_MODELS: str = "qwen/qwen3-coder:free"  # comma-separated, rotate on 429
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_QUALITY_MODEL: str = "qwen2.5:7b"
    DATABASE_PATH: str = str(Path(__file__).parent.parent / "data" / "ai_dynamics.db")

    @property
    def use_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def use_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def openrouter_api_keys(self) -> list[str]:
        """Parse comma-separated OpenRouter API keys."""
        return [k.strip() for k in self.OPENROUTER_API_KEYS.split(",") if k.strip()]

    @property
    def openrouter_models(self) -> list[str]:
        """Parse comma-separated OpenRouter models."""
        return [m.strip() for m in self.OPENROUTER_MODELS.split(",") if m.strip()]

    @property
    def use_openrouter(self) -> bool:
        return bool(self.openrouter_api_keys)

    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
