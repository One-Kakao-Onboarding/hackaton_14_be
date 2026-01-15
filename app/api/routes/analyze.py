"""
상품 및 배경 분석 API 라우트
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ProductAnalyzeRequest,
    ProductAnalyzeResponse,
    ProductBatchAnalyzeRequest,
    ProductBatchAnalyzeResponse,
    ProductBatchResult,
    BackgroundAnalyzeRequest,
    BackgroundAnalyzeResponse,
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

# 전역 인스턴스 (서버 시작 시 한 번만 로드)
analyzer = MoodAnalyzer()
vector_manager = MoodVectorManager()


@router.post(
    "/products/analyze",
    response_model=ProductAnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def analyze_product(request: ProductAnalyzeRequest):
    """
    단일 상품의 무드 분석

    removed_background_image_base64를 받아서 4가지 축의 특징을 추출하고
    Mood Vector를 생성합니다.
    """
    try:
        # Base64 → OpenCV Image
        image = base64_to_opencv(request.removed_bg_image_base64)

        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid image format")

        # 무드 분석
        result = analyzer.analyze(
            image=image,
            image_type='prop',
            image_id=request.product_id
        )

        # Mood Vector 생성
        mood_vector = vector_manager.create_mood_vector(result, image_type='prop')

        # 응답 데이터 구성
        analysis_result = result['analysis_result']

        mood_analysis = MoodAnalysis(
            colors=ColorAnalysis(**analysis_result['colors']),
            physics=PhysicsAnalysis(
                circularity=analysis_result['physics'].get('circularity'),
                glossiness=analysis_result['physics']['glossiness'],
                complexity=analysis_result['physics']['complexity']
            ),
            style=StyleAnalysis(**analysis_result['style'])
        )

        return ProductAnalyzeResponse(
            success=True,
            product_id=request.product_id,
            mood_analysis=mood_analysis,
            mood_vector=mood_vector,
            cluster_id=None  # TODO: Clustering 후 업데이트
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post(
    "/products/batch-analyze",
    response_model=ProductBatchAnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def batch_analyze_products(request: ProductBatchAnalyzeRequest):
    """
    여러 상품을 배치로 무드 분석

    최대 100개까지 한 번에 처리할 수 있습니다.
    """
    if len(request.products) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 products allowed per batch"
        )

    start_time = time.time()
    results = []
    success_count = 0
    failed_count = 0

    for product_req in request.products:
        try:
            # 개별 상품 분석
            image = base64_to_opencv(product_req.removed_bg_image_base64)

            if not validate_image(image):
                results.append(ProductBatchResult(
                    product_id=product_req.product_id,
                    status="failed",
                    error="Invalid image format"
                ))
                failed_count += 1
                continue

            result = analyzer.analyze(
                image=image,
                image_type='prop',
                image_id=product_req.product_id
            )

            mood_vector = vector_manager.create_mood_vector(result, image_type='prop')

            # TODO: DB 저장 로직 추가
            # save_to_database(product_req, result, mood_vector)

            results.append(ProductBatchResult(
                product_id=product_req.product_id,
                status="success",
                cluster_id=None  # TODO: Clustering 후 업데이트
            ))
            success_count += 1

        except Exception as e:
            results.append(ProductBatchResult(
                product_id=product_req.product_id,
                status="failed",
                error=str(e)
            ))
            failed_count += 1

    processing_time = time.time() - start_time

    return ProductBatchAnalyzeResponse(
        success=True,
        total_count=len(request.products),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        processing_time_seconds=round(processing_time, 2)
    )


@router.post(
    "/analyze/background",
    response_model=BackgroundAnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def analyze_background(request: BackgroundAnalyzeRequest):
    """
    배경 이미지의 무드 분석

    인테리어 공간 이미지를 분석하여 무드를 추출합니다.
    """
    try:
        # Base64 → OpenCV Image
        image = base64_to_opencv(request.background_image_base64)

        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid image format")

        # 무드 분석
        result = analyzer.analyze(
            image=image,
            image_type='background',
            image_id='bg_temp'
        )

        # Mood Vector 생성
        mood_vector = vector_manager.create_mood_vector(result, image_type='background')

        # 응답 데이터 구성
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

        return BackgroundAnalyzeResponse(
            success=True,
            mood_analysis=mood_analysis,
            mood_vector=mood_vector
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
