"""
Vector Manager 테스트
"""
import pytest
from app.core.vector_manager import MoodVectorManager


class TestMoodVectorManager:
    """Mood Vector Manager 테스트"""

    def setup_method(self):
        """테스트 전 초기화"""
        self.manager = MoodVectorManager()

        # 테스트용 분석 결과 (Mock)
        self.mock_analysis_result = {
            'type': 'prop',
            'id': 'test_001',
            'analysis_result': {
                'colors': {
                    'dominant_hex': ['#FFFFFF', '#D2B48C'],
                    'warmth_score': 0.75
                },
                'physics': {
                    'circularity': 0.92,
                    'glossiness': 0.15,
                    'complexity': 0.28
                },
                'style': {
                    'primary_keyword': 'natural_wood',
                    'primary_score': 0.85,
                    'category': 'Natural & Cozy',
                    'vector_breakdown': {
                        'natural_wood': 0.85,
                        'white_wood': 0.08,
                        'japandi': 0.02,
                        'cozy': 0.01,
                        'modern': 0.01,
                        'minimalism': 0.01,
                        'mid_century_modern': 0.00,
                        'industrial': 0.00,
                        'classic': 0.00,
                        'modern_french': 0.00,
                        'hotel_luxury': 0.00,
                        'vintage': 0.01,
                        'pop_art': 0.00,
                        'planterior': 0.01
                    }
                }
            }
        }

    def test_create_mood_vector_dimension(self):
        """Mood Vector가 20차원인지 테스트"""
        vector = self.manager.create_mood_vector(self.mock_analysis_result, 'prop')
        assert len(vector) == 20

    def test_create_mood_vector_values_in_range(self):
        """Mood Vector 값들이 0~1 범위인지 테스트"""
        vector = self.manager.create_mood_vector(self.mock_analysis_result, 'prop')
        for value in vector:
            assert 0.0 <= value <= 1.0

    def test_calculate_similarity_cosine(self):
        """코사인 유사도 계산 테스트"""
        vector1 = [0.5] * 20
        vector2 = [0.5] * 20
        similarity = self.manager.calculate_similarity(vector1, vector2, method='cosine')

        assert 0.0 <= similarity <= 1.0
        # 동일한 벡터는 유사도 1.0
        assert similarity > 0.99

    def test_calculate_similarity_euclidean(self):
        """유클리디안 거리 기반 유사도 테스트"""
        vector1 = [0.5] * 20
        vector2 = [0.5] * 20
        similarity = self.manager.calculate_similarity(vector1, vector2, method='euclidean')

        assert 0.0 <= similarity <= 1.0
        # 동일한 벡터는 유사도 1.0
        assert similarity > 0.99

    def test_calculate_weighted_similarity(self):
        """가중치 기반 유사도 테스트"""
        vector1 = [0.5] * 20
        vector2 = [0.6] * 20

        similarity = self.manager.calculate_weighted_similarity(vector1, vector2)
        assert 0.0 <= similarity <= 1.0

    def test_get_similarity_breakdown(self):
        """유사도 분해 테스트"""
        vector1 = [0.5] * 20
        vector2 = [0.5] * 20

        breakdown = self.manager.get_similarity_breakdown(vector1, vector2)

        assert 'color_similarity' in breakdown
        assert 'physics_similarity' in breakdown
        assert 'style_similarity' in breakdown

        # 모든 유사도가 0~1 범위
        for key, value in breakdown.items():
            assert 0.0 <= value <= 1.0

    def test_rank_products(self):
        """상품 랭킹 테스트"""
        bg_vector = [0.5] * 20

        products = [
            {'product_id': 'prod_001', 'mood_vector': [0.5] * 20, 'name': 'Product 1'},
            {'product_id': 'prod_002', 'mood_vector': [0.3] * 20, 'name': 'Product 2'},
            {'product_id': 'prod_003', 'mood_vector': [0.7] * 20, 'name': 'Product 3'},
        ]

        ranked = self.manager.rank_products(bg_vector, products, top_k=2)

        assert len(ranked) == 2
        # 첫 번째 상품이 가장 유사해야 함
        assert ranked[0]['product_id'] == 'prod_001'
        assert ranked[0]['match_score'] > ranked[1]['match_score']

    def test_hex_to_hsv(self):
        """HEX to HSV 변환 테스트"""
        h, s, v = self.manager._hex_to_hsv('#FF0000')  # 빨간색

        assert 0.0 <= h <= 1.0
        assert 0.0 <= s <= 1.0
        assert 0.0 <= v <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
