"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings for the AI Startup Boardroom backend."""

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    PRO_MODEL: str = os.getenv("PRO_MODEL", "gemini-2.0-flash")
    FLASH_MODEL: str = os.getenv("FLASH_MODEL", "gemini-2.0-flash")
    LLM_PROVIDER: str = (
        os.getenv("LLM_PROVIDER", "").strip().lower()
        or (
            "groq"
            if os.getenv("GROQ_API_KEY", "").strip() or os.getenv("GROQ_API_KEYS", "").strip()
            else "openrouter"
            if os.getenv("OPENROUTER_API_KEY", "").strip() or os.getenv("OPENROUTER_API_KEYS", "").strip()
            else "sambanova"
            if os.getenv("SAMBANOVA_API_KEY", "").strip() or os.getenv("SAMBANOVA_API_KEYS", "").strip()
            else "together"
            if os.getenv("TOGETHER_API_KEY", "").strip() or os.getenv("TOGETHER_API_KEYS", "").strip()
            else "gemini"
        )
    )
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    
    SAMBANOVA_API_KEY: str = os.getenv("SAMBANOVA_API_KEY", "")
    SAMBANOVA_MODEL: str = os.getenv("SAMBANOVA_MODEL", "Meta-Llama-3.1-70B-Instruct")
    
    TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")
    TOGETHER_MODEL: str = os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")

    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    # Agent configuration
    DEBATE_ROUNDS: int = 3
    MAX_TOKENS_PER_AGENT: int = 4096

    @property
    def groq_api_keys(self) -> list[str]:
        """List of all available Groq API keys."""
        keys_str = os.getenv("GROQ_API_KEYS", "")
        if keys_str:
            return [k.strip() for k in keys_str.split(",") if k.strip()]
        single_key = self.GROQ_API_KEY.strip()
        return [single_key] if single_key else []

    @property
    def google_api_keys(self) -> list[str]:
        """List of all available Google Gemini API keys."""
        keys_str = os.getenv("GOOGLE_API_KEYS", "")
        if keys_str:
            return [k.strip() for k in keys_str.split(",") if k.strip()]
        single_key = self.GOOGLE_API_KEY.strip()
        return [single_key] if single_key else []

    @property
    def openrouter_api_keys(self) -> list[str]:
        """List of all available OpenRouter API keys."""
        keys_str = os.getenv("OPENROUTER_API_KEYS", "")
        if keys_str:
            return [k.strip() for k in keys_str.split(",") if k.strip()]
        single_key = self.OPENROUTER_API_KEY.strip()
        return [single_key] if single_key else []

    @property
    def sambanova_api_keys(self) -> list[str]:
        """List of all available SambaNova API keys."""
        keys_str = os.getenv("SAMBANOVA_API_KEYS", "")
        if keys_str:
            return [k.strip() for k in keys_str.split(",") if k.strip()]
        single_key = self.SAMBANOVA_API_KEY.strip()
        return [single_key] if single_key else []

    @property
    def together_api_keys(self) -> list[str]:
        """List of all available Together AI API keys."""
        keys_str = os.getenv("TOGETHER_API_KEYS", "")
        if keys_str:
            return [k.strip() for k in keys_str.split(",") if k.strip()]
        single_key = self.TOGETHER_API_KEY.strip()
        return [single_key] if single_key else []

    # Model mapping
    @property
    def founder_model(self) -> str:
        """Founder/CEO uses the Pro model for orchestration."""
        return self.PRO_MODEL

    @property
    def executive_model(self) -> str:
        """Executive agents use Flash for speed."""
        return self.FLASH_MODEL


settings = Settings()
