"""
애플리케이션 설정 관리
환경 변수 및 설정값을 중앙에서 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경 변수 또는 .env 파일에서 값을 로드
    """

    # ===== Application Settings =====
    APP_NAME: str = "Interior Mood Matching API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production

    # ===== Server Settings =====
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # ===== CORS Settings =====
    CORS_ORIGINS: list = ["*"]  # 프로덕션에서는 특정 도메인만 허용
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # ===== Database Settings =====
    DATABASE_URL: Optional[str] = None
    # 예: "postgresql://user:password@localhost:5432/mood_matching"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mood_matching"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"

    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ===== Redis Settings (Caching) =====
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_CACHE_TTL: int = 3600  # 캐시 TTL (초)

    # ===== AI Model Settings =====
    CLIP_MODEL_NAME: str = "ViT-B/32"
    DEVICE: str = "auto"  # "auto", "cuda", "cpu"
    MODEL_CACHE_DIR: str = "./models"

    # ===== Image Processing Settings =====
    MAX_IMAGE_SIZE: int = 1024  # 최대 이미지 크기 (px)
    IMAGE_QUALITY: int = 85  # JPEG 품질 (1-100)
    SUPPORTED_FORMATS: list = ["jpg", "jpeg", "png", "webp"]

    # ===== Clustering Settings =====
    N_CLUSTERS: int = 20
    CLUSTER_MODEL_PATH: str = "./models/kmeans_cluster.pkl"
    AUTO_RECLUSTER_THRESHOLD: int = 1000  # 상품이 N개 추가되면 자동 재클러스터링

    # ===== Matching Settings =====
    DEFAULT_TOP_K: int = 10
    DEFAULT_MATCHING_STRATEGY: str = "weighted"  # "cosine", "euclidean", "weighted"

    # Matching Weights
    WEIGHT_COLOR: float = 0.25
    WEIGHT_PHYSICS: float = 0.20
    WEIGHT_STYLE: float = 0.55

    # ===== API Rate Limiting =====
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    # ===== Logging Settings =====
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = "./logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # ===== AWS/S3 Settings (Optional) =====
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET_NAME: Optional[str] = None
    S3_IMAGE_PREFIX: str = "products/"

    # ===== Monitoring Settings =====
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = False

    # ===== Security Settings =====
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    REQUIRE_API_KEY: bool = False

    # ===== Batch Processing Settings =====
    MAX_BATCH_SIZE: int = 100
    BATCH_TIMEOUT: int = 300  # 초

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def database_url_sync(self) -> str:
        """동기 PostgreSQL 연결 URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def database_url_async(self) -> str:
        """비동기 PostgreSQL 연결 URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self) -> str:
        """Redis 연결 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_matching_weights(self) -> dict:
        """매칭 가중치 딕셔너리 반환"""
        return {
            'color': self.WEIGHT_COLOR,
            'physics': self.WEIGHT_PHYSICS,
            'style': self.WEIGHT_STYLE
        }


@lru_cache()
def get_settings() -> Settings:
    """
    설정 인스턴스를 싱글톤으로 반환
    FastAPI Depends에서 사용
    """
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
