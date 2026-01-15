"""
Mood Vector 생성 및 관리 모듈
"""
import numpy as np
import cv2
from typing import Dict, List
from sklearn.metrics.pairwise import cosine_similarity


class MoodVectorManager:
    """
    Mood Vector 생성, 유사도 계산, 매칭 로직을 담당하는 클래스
    """

    # Vector 차원 정의
    VECTOR_DIM = 20
    COLOR_DIM = 3
    PHYSICS_DIM = 3
    STYLE_DIM = 14

    def __init__(self):
        """
        초기화
        """
        pass

    def create_mood_vector(self, analysis_result: Dict, image_type: str = 'prop') -> List[float]:
        """
        분석 결과로부터 통합 Mood Vector 생성 (20차원)

        Args:
            analysis_result: analyzer.analyze()의 결과 딕셔너리
            image_type: 'background' 또는 'prop'

        Returns:
            20차원 mood vector 리스트
        """
        colors = analysis_result['analysis_result']['colors']
        physics = analysis_result['analysis_result']['physics']
        style = analysis_result['analysis_result']['style']

        # === Color Features (3차원) ===
        warmth_score = colors['warmth_score']

        # 주조색의 HSV 추출
        dominant_hex = colors['dominant_hex'][0] if colors['dominant_hex'] else '#808080'
        h, s, v = self._hex_to_hsv(dominant_hex)

        color_features = [warmth_score, h, s]

        # === Physics Features (3차원) ===
        if image_type == 'background':
            shape_feature = physics.get('linearity', 0.5)
        else:  # prop
            shape_feature = physics.get('circularity', 0.5)

        glossiness = physics.get('glossiness', 0.0)
        complexity = physics.get('complexity', 0.0)

        physics_features = [shape_feature, glossiness, complexity]

        # === Style Features (14차원) ===
        style_vector = list(style['vector_breakdown'].values())[:14]

        # 14개가 안되면 0으로 패딩
        while len(style_vector) < 14:
            style_vector.append(0.0)

        # 통합 벡터 생성
        mood_vector = color_features + physics_features + style_vector

        # 20차원 검증
        assert len(mood_vector) == self.VECTOR_DIM, f"Vector dimension mismatch: {len(mood_vector)}"

        return mood_vector

    def calculate_similarity(
        self,
        vector1: List[float],
        vector2: List[float],
        method: str = 'cosine'
    ) -> float:
        """
        두 벡터 간의 유사도 계산

        Args:
            vector1: 첫 번째 mood vector
            vector2: 두 번째 mood vector
            method: 'cosine', 'euclidean', 'weighted'

        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        v1 = np.array(vector1).reshape(1, -1)
        v2 = np.array(vector2).reshape(1, -1)

        if method == 'cosine':
            similarity = cosine_similarity(v1, v2)[0][0]
            # -1~1 범위를 0~1로 정규화
            return (similarity + 1) / 2

        elif method == 'euclidean':
            distance = np.linalg.norm(v1 - v2)
            # 거리를 유사도로 변환 (작을수록 유사)
            # 최대 거리를 sqrt(20)로 가정하여 정규화
            max_distance = np.sqrt(self.VECTOR_DIM)
            similarity = 1 - (distance / max_distance)
            return max(0.0, similarity)

        elif method == 'weighted':
            return self.calculate_weighted_similarity(vector1, vector2)

        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_weighted_similarity(
        self,
        vector1: List[float],
        vector2: List[float],
        weights: Dict[str, float] = None
    ) -> float:
        """
        가중치 기반 유사도 계산

        Args:
            vector1: 첫 번째 mood vector
            vector2: 두 번째 mood vector
            weights: 각 축의 가중치 {'color': 0.25, 'physics': 0.20, 'style': 0.55}

        Returns:
            가중 유사도 점수 (0.0 ~ 1.0)
        """
        if weights is None:
            weights = {
                'color': 0.25,
                'physics': 0.20,
                'style': 0.55
            }

        # 벡터를 축별로 분리
        v1 = np.array(vector1)
        v2 = np.array(vector2)

        color1 = v1[:self.COLOR_DIM].reshape(1, -1)
        color2 = v2[:self.COLOR_DIM].reshape(1, -1)

        physics1 = v1[self.COLOR_DIM:self.COLOR_DIM + self.PHYSICS_DIM].reshape(1, -1)
        physics2 = v2[self.COLOR_DIM:self.COLOR_DIM + self.PHYSICS_DIM].reshape(1, -1)

        style1 = v1[self.COLOR_DIM + self.PHYSICS_DIM:].reshape(1, -1)
        style2 = v2[self.COLOR_DIM + self.PHYSICS_DIM:].reshape(1, -1)

        # 각 축별 코사인 유사도 계산
        color_sim = cosine_similarity(color1, color2)[0][0]
        physics_sim = cosine_similarity(physics1, physics2)[0][0]
        style_sim = cosine_similarity(style1, style2)[0][0]

        # -1~1 범위를 0~1로 정규화
        color_sim = (color_sim + 1) / 2
        physics_sim = (physics_sim + 1) / 2
        style_sim = (style_sim + 1) / 2

        # 가중치 적용
        weighted_score = (
            color_sim * weights['color'] +
            physics_sim * weights['physics'] +
            style_sim * weights['style']
        )

        return weighted_score

    def get_similarity_breakdown(
        self,
        vector1: List[float],
        vector2: List[float]
    ) -> Dict[str, float]:
        """
        각 축별 유사도를 상세히 반환

        Args:
            vector1: 첫 번째 mood vector
            vector2: 두 번째 mood vector

        Returns:
            각 축별 유사도 딕셔너리
        """
        v1 = np.array(vector1)
        v2 = np.array(vector2)

        color1 = v1[:self.COLOR_DIM].reshape(1, -1)
        color2 = v2[:self.COLOR_DIM].reshape(1, -1)

        physics1 = v1[self.COLOR_DIM:self.COLOR_DIM + self.PHYSICS_DIM].reshape(1, -1)
        physics2 = v2[self.COLOR_DIM:self.COLOR_DIM + self.PHYSICS_DIM].reshape(1, -1)

        style1 = v1[self.COLOR_DIM + self.PHYSICS_DIM:].reshape(1, -1)
        style2 = v2[self.COLOR_DIM + self.PHYSICS_DIM:].reshape(1, -1)

        color_sim = (cosine_similarity(color1, color2)[0][0] + 1) / 2
        physics_sim = (cosine_similarity(physics1, physics2)[0][0] + 1) / 2
        style_sim = (cosine_similarity(style1, style2)[0][0] + 1) / 2

        return {
            'color_similarity': float(color_sim),
            'physics_similarity': float(physics_sim),
            'style_similarity': float(style_sim)
        }

    def _hex_to_hsv(self, hex_color: str) -> tuple:
        """
        HEX 색상을 HSV로 변환 (정규화된 0~1 범위)

        Args:
            hex_color: '#FFFFFF' 형식의 HEX 색상

        Returns:
            (h, s, v) 튜플 (0~1 범위)
        """
        # HEX → RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # RGB → HSV (OpenCV)
        rgb_array = np.uint8([[[b, g, r]]])  # OpenCV는 BGR 순서
        hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_BGR2HSV)

        h, s, v = hsv_array[0][0]

        # 정규화 (0~1)
        h_norm = h / 180.0  # OpenCV HSV의 H는 0~180
        s_norm = s / 255.0
        v_norm = v / 255.0

        return (h_norm, s_norm, v_norm)

    def rank_products(
        self,
        background_vector: List[float],
        product_vectors: List[Dict],
        top_k: int = 10,
        method: str = 'weighted'
    ) -> List[Dict]:
        """
        배경 벡터와 상품 벡터들을 비교하여 Top-K 상품 선택

        Args:
            background_vector: 배경의 mood vector
            product_vectors: 상품들의 데이터 리스트
                [{'product_id': 'prod_001', 'mood_vector': [...], ...}, ...]
            top_k: 상위 K개 선택
            method: 유사도 계산 방법

        Returns:
            정렬된 상품 리스트 (유사도 높은 순)
        """
        scored_products = []

        for product in product_vectors:
            similarity = self.calculate_similarity(
                background_vector,
                product['mood_vector'],
                method=method
            )

            breakdown = self.get_similarity_breakdown(
                background_vector,
                product['mood_vector']
            )

            scored_products.append({
                **product,
                'match_score': float(similarity),
                'match_details': breakdown
            })

        # 유사도 순으로 정렬
        scored_products.sort(key=lambda x: x['match_score'], reverse=True)

        return scored_products[:top_k]
