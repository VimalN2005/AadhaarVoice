from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # Application Info
    APP_NAME: str = "AadhaarVoice - Biometric Voice Identity System"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Cryptography & Security
    SECRET_KEY: str = "aadhaar-voice-dev-secret-key-change-in-production-64byteslong"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Fernet key for field encryption
    ENCRYPTION_KEY: str = "dGVzdF9mZXJuZXRfa2V5X2Zvcl9kZXZlbG9wbWVudF8xMjM="

    # Storage & Database
    DATA_DIR: Path = BASE_DIR / "data"
    STORAGE_DIR: Path = BASE_DIR / "data" / "storage"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'aadhaar_voice.db'}"

    # Audio Signal Processing & Biometrics
    SAMPLE_RATE: int = 16000
    N_MFCC: int = 40
    N_FFT: int = 512
    HOP_LENGTH: int = 160
    VERIFICATION_SIMILARITY_THRESHOLD: float = 0.82
    DEEPFAKE_DETECTION_THRESHOLD: float = 0.65
    LIVENESS_EXPIRATION_SECONDS: int = 120


settings = Settings()

# Ensure required directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
