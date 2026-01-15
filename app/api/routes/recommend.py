"""
상품 추천 API 라우트
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    RecommendRequest,
    RecommendResponse,
    RecommendedProduct,
    MatchDetails,
    MoodAnalysis,
    ColorAnalysis,
    PhysicsAnalysis,
    StyleAnalysis,
    ErrorResponse
)
from app.analyzer import MoodAnalyzer
from app.core.image_utils import base64_to_opencv, validate_image
from app.core.vector_manager import MoodVectorManager
import time

router = APIRouter()

# 전역 인스턴스
analyzer = MoodAnalyzer()
vector_manager = MoodVectorManager()


# TODO: DB 연결 후 실제 데이터 사용
# 현재는 Mock 데이터로 응답
MOCK_PRODUCTS = [
    {
        'product_id': 'prod_001',
        'name': '우드 원형 테이블',
        'category': 'furniture',
        'price': 150000,
        'image_url': 'https://example.com/prod_001.jpg',
        'mood_vector': [0.78, 0.65, 0.42, 0.92, 0.15, 0.28] + [0.85, 0.08, 0.02, 0.01, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.01],
        'primary_keyword': 'natural_wood',
        'cluster_id': 3
    },
    {
        'product_id': 'prod_002',
        'name': '화이트 오크 수납장',
        'category': 'furniture',
        'price': 280000,
        'image_url': 'https://example.com/prod_002.jpg',
        'mood_vector': [0.72, 0.58, 0.45, 0.88, 0.12, 0.25] + [0.12, 0.88, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        'primary_keyword': 'white_wood',
        'cluster_id': 3
    },
    {
        'product_id': 'prod_003',
        'name': '패브릭 쿠션 (베이지)',
        'category': 'decor',
        'price': 35000,
        'image_url': 'https://example.com/prod_003.jpg',
        'mood_vector': [0.80, 0.60, 0.50, 0.95, 0.08, 0.15] + [0.45, 0.35, 0.10, 0.05, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.00, 0.01],
        'primary_keyword': 'cozy',
        'cluster_id': 1
    }
]


@router.post(
    "/match/recommend",
    response_model=RecommendResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def recommend_products(request: RecommendRequest):
    """
    배경 이미지 분석 후 가장 잘 맞는 상품 추천

    1. 배경 이미지의 무드를 분석합니다.
    2. DB에서 유사한 무드의 상품들을 찾습니다.
    3. Top-K 상품을 반환합니다.
    """
    start_time = time.time()

    try:
        # 1. 배경 이미지 분석
        image = base64_to_opencv(request.background_image_base64)

        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid image format")

        result = analyzer.analyze(
            image=image,
            image_type='background',
            image_id='bg_request'
        )

        # Mood Vector 생성
        bg_mood_vector = vector_manager.create_mood_vector(result, image_type='background')

        # 2. DB에서 상품 가져오기 (TODO: 실제 DB 연동)
        # 현재는 Mock 데이터 사용
        candidate_products = MOCK_PRODUCTS.copy()

        # 필터 적용
        if request.filters:
            if request.filters.categories:
                candidate_products = [
                    p for p in candidate_products
                    if p['category'] in request.filters.categories
                ]

            if request.filters.price_range:
                min_price = request.filters.price_range.get('min', 0)
                max_price = request.filters.price_range.get('max', float('inf'))
                candidate_products = [
                    p for p in candidate_products
                    if min_price <= p['price'] <= max_price
                ]

            if request.filters.styles:
                candidate_products = [
                    p for p in candidate_products
                    if p['primary_keyword'] in request.filters.styles
                ]

        # 3. 유사도 계산 및 Top-K 선택
        ranked_products = vector_manager.rank_products(
            background_vector=bg_mood_vector,
            product_vectors=candidate_products,
            top_k=request.top_k,
            method=request.matching_strategy.value
        )

        # 필터: min_score 적용
        if request.filters and request.filters.min_score:
            ranked_products = [
                p for p in ranked_products
                if p['match_score'] >= request.filters.min_score
            ]

        # 4. 응답 데이터 구성
        analysis_result = result['analysis_result']

        mood_analysis = MoodAnalysis(
            colors=ColorAnalysis(**analysis_result['colors']),
            physics=PhysicsAnalysis(
                linearity=analysis_result['physics'].get('linearity'),
                glossiness=analysis_result['physics']['glossiness'],
                complexity=analysis_result['physics']['complexity']
            ),
            style=StyleAnalysis(**analysis_result['style'])
        )

        recommended_products = []
        for product in ranked_products:
            # Match quality 판정
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

        return RecommendResponse(
            success=True,
            background_mood=mood_analysis,
            recommended_products=recommended_products,
            processing_time_ms=round(processing_time_ms, 2)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.get(
    "/products/{product_id}/similar",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_similar_products(product_id: str, top_k: int = 5):
    """
    특정 상품과 유사한 상품 찾기

    TODO: DB 연동 후 구현
    """
    # TODO: DB에서 product_id로 상품 조회
    # TODO: 해당 상품의 mood_vector로 유사 상품 검색

    return {
        "success": True,
        "reference_product": {
            "product_id": product_id,
            "name": "상품명"
        },
        "similar_products": [
            {
                "product_id": "prod_089",
                "name": "유사 상품 1",
                "similarity_score": 0.96
            }
        ],
        "message": "TODO: Implement DB integration"
    }
