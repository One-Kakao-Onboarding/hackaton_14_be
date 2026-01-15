"""
FastAPI 엔드포인트 테스트
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import base64
import numpy as np
import cv2
import io
from PIL import Image


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def dummy_image_base64():
    """테스트용 더미 이미지 (Base64)"""
    # 100x100 빨간색 이미지 생성
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :] = [0, 0, 255]  # BGR: 빨간색

    # BGR → RGB 변환
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # PIL Image로 변환
    pil_image = Image.fromarray(image_rgb)

    # BytesIO에 저장
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    buffer.seek(0)

    # Base64 인코딩
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return image_base64


class TestHealthCheck:
    """헬스체크 엔드포인트 테스트"""

    def test_root(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'running'

    def test_health(self, client):
        """헬스체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


class TestAnalyzeAPI:
    """분석 API 테스트"""

    def test_analyze_background(self, client, dummy_image_base64):
        """배경 분석 API 테스트"""
        payload = {
            "background_image_base64": dummy_image_base64
        }

        response = client.post("/api/v1/analyze/background", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert 'mood_analysis' in data
        assert 'mood_vector' in data
        assert len(data['mood_vector']) == 20

    def test_analyze_product(self, client, dummy_image_base64):
        """상품 분석 API 테스트"""
        payload = {
            "product_id": "test_prod_001",
            "name": "테스트 상품",
            "category": "furniture",
            "removed_bg_image_base64": dummy_image_base64
        }

        response = client.post("/api/v1/products/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert data['product_id'] == "test_prod_001"
        assert 'mood_analysis' in data
        assert 'mood_vector' in data

    def test_batch_analyze_products(self, client, dummy_image_base64):
        """배치 상품 분석 API 테스트"""
        payload = {
            "products": [
                {
                    "product_id": "prod_001",
                    "name": "상품 1",
                    "category": "furniture",
                    "removed_bg_image_base64": dummy_image_base64
                },
                {
                    "product_id": "prod_002",
                    "name": "상품 2",
                    "category": "decor",
                    "removed_bg_image_base64": dummy_image_base64
                }
            ]
        }

        response = client.post("/api/v1/products/batch-analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert data['total_count'] == 2
        assert data['success_count'] >= 0


class TestRecommendAPI:
    """추천 API 테스트"""

    def test_recommend_products(self, client, dummy_image_base64):
        """상품 추천 API 테스트"""
        payload = {
            "background_image_base64": dummy_image_base64,
            "top_k": 5,
            "matching_strategy": "weighted"
        }

        response = client.post("/api/v1/match/recommend", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert 'background_mood' in data
        assert 'recommended_products' in data
        assert len(data['recommended_products']) <= 5

    def test_recommend_with_filters(self, client, dummy_image_base64):
        """필터링된 상품 추천 API 테스트"""
        payload = {
            "background_image_base64": dummy_image_base64,
            "top_k": 3,
            "filters": {
                "categories": ["furniture"],
                "min_score": 0.5
            }
        }

        response = client.post("/api/v1/match/recommend", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True


class TestAdminAPI:
    """관리 API 테스트"""

    def test_cluster_stats(self, client):
        """클러스터 통계 API 테스트"""
        response = client.get("/api/v1/admin/cluster-stats")
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert 'cluster_distribution' in data


class TestErrorHandling:
    """에러 처리 테스트"""

    def test_invalid_base64(self, client):
        """잘못된 Base64 이미지 테스트"""
        payload = {
            "background_image_base64": "invalid_base64_string"
        }

        response = client.post("/api/v1/analyze/background", json=payload)
        assert response.status_code == 400

    def test_empty_product_id(self, client, dummy_image_base64):
        """빈 product_id 테스트"""
        payload = {
            "product_id": "",
            "name": "상품",
            "removed_bg_image_base64": dummy_image_base64
        }

        response = client.post("/api/v1/products/analyze", json=payload)
        # Validation 에러
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
