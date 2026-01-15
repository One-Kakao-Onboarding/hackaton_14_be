"""
스마트 추천 API
빨간색 원 감지 → Gemini 분석 → 배경 무드 분석 → 상품 추천
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import cv2
import numpy as np
import time

from app.core.circle_detector import CircleDetector
from app.core.gemini_analyzer import GeminiAnalyzer
from app.core.image_utils import base64_to_opencv
from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager
from app.models.schemas import RecommendedProduct, MatchDetails

router = APIRouter()

# 전역 인스턴스
circle_detector = CircleDetector()
gemini_analyzer = GeminiAnalyzer()
mood_analyzer = MoodAnalyzer()
vector_manager = MoodVectorManager()


# ===== Request/Response Schemas =====

class SmartRecommendRequest(BaseModel):
    """스마트 추천 요청"""
    image_base64: str = Field(..., description="빨간색 원이 표시된 인테리어 이미지 (Base64)")
    top_k: int = Field(10, ge=1, le=50, description="추천 상품 개수")
    matching_strategy: str = Field("weighted", description="매칭 전략")


class CircleRegionInfo(BaseModel):
    """감지된 원 영역 정보"""
    center_x: int
    center_y: int
    radius: int
    category: str  # 'furniture' or 'prop'
    confidence: float
    description: str
    gemini_recommendations: List[str]


class BackgroundMoodInfo(BaseModel):
    """배경 무드 정보"""
    primary_style: str
    warmth_score: float
    dominant_colors: List[str]


class SmartRecommendResponse(BaseModel):
    """스마트 추천 응답"""
    success: bool
    circle_detected: bool
    circle_info: Optional[CircleRegionInfo]
    background_mood: Optional[BackgroundMoodInfo]
    recommended_products: List[RecommendedProduct]
    processing_time_ms: float
    message: str


# ===== Mock Product Data =====
# TODO: 실제 DB 연동 후 교체
MOCK_FURNITURE_PRODUCTS = [
    {
        'product_id': 'furn_001',
        'name': '우드 침대 프레임',
        'category': 'furniture',
        'price': 450000,
        'image_url': 'https://example.com/bed1.jpg',
        'mood_vector': [0.75, 0.60, 0.50, 0.85, 0.20, 0.30] + [0.80, 0.10, 0.05, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.00],
        'primary_keyword': 'natural_wood',
        'cluster_id': 1
    },
    {
        'product_id': 'furn_002',
        'name': '화이트 옷장',
        'category': 'furniture',
        'price': 680000,
        'image_url': 'https://example.com/closet1.jpg',
        'mood_vector': [0.70, 0.55, 0.45, 0.90, 0.15, 0.25] + [0.15, 0.85, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        'primary_keyword': 'white_wood',
        'cluster_id': 1
    }
]

MOCK_PROP_PRODUCTS = [
    {
        'product_id': 'prop_001',
        'name': '우드 사이드 테이블',
        'category': 'decor',
        'price': 85000,
        'image_url': 'https://example.com/table1.jpg',
        'mood_vector': [0.78, 0.62, 0.48, 0.88, 0.18, 0.28] + [0.82, 0.08, 0.04, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.01],
        'primary_keyword': 'natural_wood',
        'cluster_id': 1
    },
    {
        'product_id': 'prop_002',
        'name': '미니멀 스탠드 조명',
        'category': 'lighting',
        'price': 65000,
        'image_url': 'https://example.com/lamp1.jpg',
        'mood_vector': [0.72, 0.58, 0.45, 0.85, 0.22, 0.30] + [0.25, 0.65, 0.05, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01],
        'primary_keyword': 'white_wood',
        'cluster_id': 1
    },
    {
        'product_id': 'prop_003',
        'name': '패브릭 쿠션 세트',
        'category': 'textile',
        'price': 45000,
        'image_url': 'https://example.com/cushion1.jpg',
        'mood_vector': [0.80, 0.60, 0.50, 0.95, 0.10, 0.20] + [0.40, 0.30, 0.10, 0.15, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.00, 0.01],
        'primary_keyword': 'cozy',
        'cluster_id': 2
    }
]


# ===== API Endpoint =====

@router.post(
    "/smart-recommend",
    response_model=SmartRecommendResponse,
    summary="스마트 추천 (원 감지 + Gemini + 무드 분석)",
    description="""
    빨간색 원이 표시된 인테리어 이미지를 분석하여 상품을 추천합니다.

    **처리 순서:**
    1. 빨간색 원 영역 감지
    2. Gemini로 해당 영역에 가구/소품 판단
    3. 배경 이미지의 무드 분석
    4. 무드에 맞는 상품 추천
    """
)
async def smart_recommend(request: SmartRecommendRequest):
    """
    스마트 추천 API - 전체 플로우 통합
    """
    start_time = time.time()

    try:
        # 1. 이미지 로드
        image = base64_to_opencv(request.image_base64)

        # 2. 빨간색 원 감지
        circle_result = circle_detector.detect_red_circle(image)

        if not circle_result:
            return SmartRecommendResponse(
                success=False,
                circle_detected=False,
                circle_info=None,
                background_mood=None,
                recommended_products=[],
                processing_time_ms=(time.time() - start_time) * 1000,
                message="빨간색 원을 감지하지 못했습니다."
            )

        center_x, center_y, radius = circle_result

        # 3. 원 영역 추출
        region_image = circle_detector.extract_circle_region(image, center_x, center_y, radius)

        # 4. Gemini로 영역 분석 (가구 vs 소품 판단)
        gemini_result = gemini_analyzer.analyze_region(region_image)

        # 5. 빨간색 원 제거한 배경 이미지로 무드 분석
        clean_background = circle_detector.remove_red_circle(image)
        bg_analysis = mood_analyzer.analyze(
            image=clean_background,
            image_type='background',
            image_id='smart_recommend'
        )

        # Mood Vector 생성
        bg_mood_vector = vector_manager.create_mood_vector(bg_analysis, image_type='background')

        # 6. 가구/소품에 따라 후보 상품 선택
        if gemini_result['category'] == 'furniture':
            candidate_products = MOCK_FURNITURE_PRODUCTS.copy()
        else:
            candidate_products = MOCK_PROP_PRODUCTS.copy()

        # 7. 무드 기반 상품 추천
        if candidate_products:
            ranked_products = vector_manager.rank_products(
                background_vector=bg_mood_vector,
                product_vectors=candidate_products,
                top_k=request.top_k,
                method=request.matching_strategy
            )
        else:
            ranked_products = []

        # 8. 응답 데이터 구성
        circle_info = CircleRegionInfo(
            center_x=center_x,
            center_y=center_y,
            radius=radius,
            category=gemini_result['category'],
            confidence=gemini_result['confidence'],
            description=gemini_result['description'],
            gemini_recommendations=gemini_result['recommendations']
        )

        bg_style = bg_analysis['analysis_result']['style']
        bg_colors = bg_analysis['analysis_result']['colors']

        background_mood = BackgroundMoodInfo(
            primary_style=bg_style['primary_keyword'],
            warmth_score=bg_colors['warmth_score'],
            dominant_colors=bg_colors['dominant_hex']
        )

        recommended_products = []
        for product in ranked_products:
            score = product['match_score']
            if score >= 0.8:
                overall_match = "excellent"
            elif score >= 0.6:
                overall_match = "good"
            else:
                overall_match = "fair"

            match_details = MatchDetails(
                **product['match_details'],
                overall_match=overall_match
            )

            recommended_products.append(RecommendedProduct(
                product_id=product['product_id'],
                name=product['name'],
                category=product.get('category'),
                price=product.get('price'),
                image_url=product.get('image_url'),
                match_score=product['match_score'],
                match_details=match_details,
                cluster_id=product.get('cluster_id')
            ))

        processing_time_ms = (time.time() - start_time) * 1000

        return SmartRecommendResponse(
            success=True,
            circle_detected=True,
            circle_info=circle_info,
            background_mood=background_mood,
            recommended_products=recommended_products,
            processing_time_ms=round(processing_time_ms, 2),
            message=f"✅ {gemini_result['category']} 카테고리에서 {len(recommended_products)}개 상품을 추천했습니다."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 실패: {str(e)}")
