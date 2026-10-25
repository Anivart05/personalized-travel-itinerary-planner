import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root or app root
base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class Settings:
    PROJECT_NAME: str = "Personalized Travel Itinerary Planner"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # AI Model Settings
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Local fallback SQLite path
    DB_PATH: str = str(base_dir / "itineraries.db")

    # Auth & Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-travel-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
