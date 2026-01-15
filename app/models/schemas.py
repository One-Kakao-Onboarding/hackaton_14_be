"""
FastAPI Pydantic 스키마 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================
# Enums
# ============================================================

class ImageType(str, Enum):
    """이미지 타입"""
    BACKGROUND = "background"
    PROP = "prop"


class MatchingStrategy(str, Enum):
    """매칭 전략"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    WEIGHTED = "weighted"


class ProductCategory(str, Enum):
    """상품 카테고리"""
    FURNITURE = "furniture"
    DECOR = "decor"
    LIGHTING = "lighting"
    TEXTILE = "textile"
    OTHER = "other"


# ============================================================
# Request Schemas
# ============================================================

class ProductAnalyzeRequest(BaseModel):
    """단일 상품 분석 요청"""
    product_id: str = Field(..., description="상품 고유 ID")
    name: str = Field(..., description="상품명")
    category: Optional[ProductCategory] = Field(None, description="상품 카테고리")
    price: Optional[int] = Field(None, description="가격")
    removed_bg_image_base64: str = Field(..., description="누끼 제거된 이미지 (Base64)")


class ProductBatchAnalyzeRequest(BaseModel):
    """배치 상품 분석 요청"""
    products: List[ProductAnalyzeRequest] = Field(..., description="상품 리스트 (최대 100개)")

    class Config:
        json_schema_extra = {
            "example": {
                "products": [
                    {
                        "product_id": "prod_001",
                        "name": "우드 원형 테이블",
                        "category": "furniture",
                        "price": 150000,
                        "removed_bg_image_base64": "iVBORw0KGgo..."
                    }
                ]
            }
        }


class RecommendationFilters(BaseModel):
    """추천 필터"""
    categories: Optional[List[ProductCategory]] = Field(None, description="필터링할 카테고리")
    min_score: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="최소 매칭 점수")
    price_range: Optional[Dict[str, int]] = Field(None, description="가격 범위 {'min': 50000, 'max': 500000}")
    styles: Optional[List[str]] = Field(None, description="특정 스타일만 필터링")


class RecommendRequest(BaseModel):
    """추천 요청"""
    background_image_base64: str = Field(..., description="배경 이미지 (Base64)")
    top_k: int = Field(10, ge=1, le=100, description="추천 상품 개수")
    filters: Optional[RecommendationFilters] = Field(None, description="필터 조건")
    matching_strategy: MatchingStrategy = Field(
        MatchingStrategy.WEIGHTED,
        description="매칭 전략 (cosine/euclidean/weighted)"
    )


class BackgroundAnalyzeRequest(BaseModel):
    """배경 분석 요청"""
    background_image_base64: str = Field(..., description="배경 이미지 (Base64)")


class ClusterRebuildRequest(BaseModel):
    """클러스터 재생성 요청"""
    n_clusters: int = Field(20, ge=2, le=100, description="클러스터 개수")


# ============================================================
# Response Schemas
# ============================================================

class ColorAnalysis(BaseModel):
    """색상 분석 결과"""
    dominant_hex: List[str] = Field(..., description="주조색 HEX 코드")
    warmth_score: float = Field(..., description="색온도 (0=Cool, 1=Warm)")


class PhysicsAnalysis(BaseModel):
    """물리적 특성 분석 결과"""
    linearity: Optional[float] = Field(None, description="직선성 (배경용)")
    circularity: Optional[float] = Field(None, description="원형도 (소품용)")
    glossiness: float = Field(..., description="광택도 (0=Matte, 1=Glossy)")
    complexity: float = Field(..., description="복잡도 (0=Simple, 1=Complex)")


class StyleAnalysis(BaseModel):
    """스타일 분석 결과"""
    primary_keyword: str = Field(..., description="1순위 스타일 키워드")
    primary_score: float = Field(..., description="1순위 확신도")
    category: str = Field(..., description="상위 카테고리")
    vector_breakdown: Dict[str, float] = Field(..., description="14개 스타일별 확률")


class MoodAnalysis(BaseModel):
    """무드 분석 결과"""
    colors: ColorAnalysis
    physics: PhysicsAnalysis
    style: StyleAnalysis


class ProductAnalyzeResponse(BaseModel):
    """단일 상품 분석 응답"""
    success: bool
    product_id: str
    mood_analysis: MoodAnalysis
    mood_vector: List[float] = Field(..., description="20차원 무드 벡터")
    cluster_id: Optional[int] = Field(None, description="클러스터 ID")


class ProductBatchResult(BaseModel):
    """배치 분석 개별 결과"""
    product_id: str
    status: str  # "success" or "failed"
    cluster_id: Optional[int] = None
    error: Optional[str] = None


class ProductBatchAnalyzeResponse(BaseModel):
    """배치 상품 분석 응답"""
    success: bool
    total_count: int
    success_count: int
    failed_count: int
    results: List[ProductBatchResult]
    processing_time_seconds: float


class MatchDetails(BaseModel):
    """매칭 상세 정보"""
    color_similarity: float
    physics_similarity: float
    style_similarity: float
    overall_match: str = Field(..., description="excellent/good/fair")


class RecommendedProduct(BaseModel):
    """추천 상품"""
    product_id: str
    name: str
    category: Optional[str]
    price: Optional[int]
    image_url: Optional[str]
    match_score: float = Field(..., description="매칭 점수 (0~1)")
    match_details: MatchDetails
    cluster_id: Optional[int]


class RecommendResponse(BaseModel):
    """추천 응답"""
    success: bool
    background_mood: MoodAnalysis
    recommended_products: List[RecommendedProduct]
    processing_time_ms: float


class BackgroundAnalyzeResponse(BaseModel):
    """배경 분석 응답"""
    success: bool
    mood_analysis: MoodAnalysis
    mood_vector: List[float]


class ClusterStats(BaseModel):
    """클러스터 통계"""
    cluster_id: int
    product_count: int
    dominant_style: str
    avg_warmth: float


class ClusterStatsResponse(BaseModel):
    """클러스터 통계 응답"""
    success: bool
    total_clusters: int
    cluster_distribution: List[ClusterStats]


class ClusterRebuildResponse(BaseModel):
    """클러스터 재생성 응답"""
    success: bool
    total_products: int
    clusters_created: int
    avg_cluster_size: float
    clustering_time_seconds: float


class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = False
    error: str
    detail: Optional[str] = None
