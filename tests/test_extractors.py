"""
Feature Extractor 테스트
"""
import pytest
import numpy as np
import cv2
from app.services.extractors.color_extractor import ColorExtractor
from app.services.extractors.shape_extractor import ShapeExtractor
from app.services.extractors.texture_extractor import TextureExtractor


class TestColorExtractor:
    """Color Extractor 테스트"""

    def setup_method(self):
        """테스트 전 초기화"""
        self.extractor = ColorExtractor(n_colors=5)
        # 테스트용 더미 이미지 생성 (100x100 빨간색)
        self.test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.test_image[:, :] = [0, 0, 255]  # BGR: 빨간색

    def test_extract_returns_dict(self):
        """extract 함수가 딕셔너리를 반환하는지 테스트"""
        result = self.extractor.extract(self.test_image)
        assert isinstance(result, dict)

    def test_extract_has_required_keys(self):
        """extract 결과에 필수 키가 있는지 테스트"""
        result = self.extractor.extract(self.test_image)
        required_keys = ['dominant_colors', 'dominant_hex', 'color_percentages', 'warmth_score', 'main_rgb']
        for key in required_keys:
            assert key in result

    def test_warmth_score_range(self):
        """warmth_score가 0~1 범위인지 테스트"""
        result = self.extractor.extract(self.test_image)
        assert 0.0 <= result['warmth_score'] <= 1.0

    def test_dominant_colors_count(self):
        """주조색 개수가 정확한지 테스트"""
        result = self.extractor.extract(self.test_image)
        assert len(result['dominant_colors']) == 5
        assert len(result['dominant_hex']) == 5

    def test_hex_format(self):
        """HEX 코드 형식이 올바른지 테스트"""
        result = self.extractor.extract(self.test_image)
        for hex_code in result['dominant_hex']:
            assert hex_code.startswith('#')
            assert len(hex_code) == 7


class TestShapeExtractor:
    """Shape Extractor 테스트"""

    def setup_method(self):
        """테스트 전 초기화"""
        self.extractor = ShapeExtractor()
        # 테스트용 더미 이미지 생성
        self.test_image = np.zeros((200, 200, 3), dtype=np.uint8)
        self.test_image[:, :] = [255, 255, 255]  # 흰색

    def test_extract_background_returns_dict(self):
        """배경 분석 결과가 딕셔너리인지 테스트"""
        result = self.extractor.extract_background(self.test_image)
        assert isinstance(result, dict)

    def test_background_has_linearity(self):
        """배경 분석 결과에 linearity가 있는지 테스트"""
        result = self.extractor.extract_background(self.test_image)
        assert 'linearity' in result
        assert 0.0 <= result['linearity'] <= 1.0

    def test_extract_prop_with_mask(self):
        """소품 분석이 마스크와 함께 동작하는지 테스트"""
        # 원형 마스크 생성
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 50, 255, -1)

        result = self.extractor.extract_prop(self.test_image, mask)
        assert 'circularity' in result
        assert 0.0 <= result['circularity'] <= 1.0

    def test_circularity_of_circle(self):
        """완전한 원의 circularity가 높은지 테스트"""
        # 원 그리기
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 50, 255, -1)

        result = self.extractor.extract_prop(image, mask)
        # 완전한 원은 circularity가 1.0에 가까워야 함
        assert result['circularity'] > 0.8


class TestTextureExtractor:
    """Texture Extractor 테스트"""

    def setup_method(self):
        """테스트 전 초기화"""
        self.extractor = TextureExtractor()
        # 테스트용 더미 이미지 생성
        self.test_image = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)

    def test_extract_returns_dict(self):
        """extract 함수가 딕셔너리를 반환하는지 테스트"""
        result = self.extractor.extract(self.test_image)
        assert isinstance(result, dict)

    def test_extract_has_required_keys(self):
        """extract 결과에 필수 키가 있는지 테스트"""
        result = self.extractor.extract(self.test_image)
        required_keys = ['complexity_score', 'glossiness_score', 'edge_density', 'laplacian_variance']
        for key in required_keys:
            assert key in result

    def test_scores_in_range(self):
        """모든 점수가 0~1 범위인지 테스트"""
        result = self.extractor.extract(self.test_image)
        assert 0.0 <= result['complexity_score'] <= 1.0
        assert 0.0 <= result['glossiness_score'] <= 1.0
        assert 0.0 <= result['edge_density'] <= 1.0

    def test_laplacian_variance_positive(self):
        """Laplacian variance가 0 이상인지 테스트"""
        result = self.extractor.extract(self.test_image)
        assert result['laplacian_variance'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
