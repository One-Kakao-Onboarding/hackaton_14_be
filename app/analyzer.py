"""
통합 분석기 모듈
Background/Prop 이미지를 분석하여 4가지 축의 특징을 추출
"""
import numpy as np
from typing import Dict, Literal
from app.services.preprocessors.background_processor import BackgroundProcessor
from app.services.preprocessors.prop_processor import PropProcessor
from app.services.extractors.color_extractor import ColorExtractor
from app.services.extractors.shape_extractor import ShapeExtractor
from app.services.extractors.texture_extractor import TextureExtractor
from app.services.extractors.style_extractor import StyleExtractor


class MoodAnalyzer:
    """
    무드 매칭 시스템의 통합 분석기
    Background와 Prop 이미지를 분석하여 4가지 축의 특징을 추출
    """

    def __init__(self, clip_model: str = "ViT-B/32", device: str = None):
        """
        Args:
            clip_model: CLIP 모델 이름
            device: 디바이스 ('cuda', 'cpu', None=auto)
        """
        # 전처리기
        self.bg_processor = BackgroundProcessor()
        self.prop_processor = PropProcessor()

        # 특징 추출기
        self.color_extractor = ColorExtractor(n_colors=5)
        self.shape_extractor = ShapeExtractor()
        self.texture_extractor = TextureExtractor()
        self.style_extractor = StyleExtractor(model_name=clip_model, device=device)

    def analyze_background(self, image: np.ndarray, image_id: str = None) -> Dict:
        """
        배경 이미지 분석

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            image_id: 이미지 ID (선택)

        Returns:
            readme.md의 JSON 형식에 맞는 분석 결과 딕셔너리
        """
        # 전처리: 벽/바닥 분리
        processed = self.bg_processor.process(image)
        wall_image = processed['wall']
        floor_image = processed['floor']
        wall_mask = processed['mask_wall']
        floor_mask = processed['mask_floor']

        # 1. Color Vector 추출 (전체 이미지 기준)
        color_features = self.color_extractor.extract(image)

        # 2. Shape/Geometry Vector 추출 (배경용 - 직선성)
        shape_features = self.shape_extractor.extract_background(image)

        # 3. Texture Vector 추출 (전체 이미지 기준)
        texture_features = self.texture_extractor.extract(image)

        # 4. Style Vector 추출 (전체 이미지 기준)
        style_features = self.style_extractor.extract(image)

        # 결과 조합 (readme.md의 JSON 형식)
        result = {
            "type": "background",
            "id": image_id or "unknown",
            "analysis_result": {
                # 1. Color Axis
                "colors": {
                    "dominant_hex": color_features['dominant_hex'][:2],  # 상위 2개
                    "warmth_score": color_features['warmth_score']
                },

                # 2. Shape/Texture Axis
                "physics": {
                    "linearity": shape_features['linearity'],
                    "glossiness": texture_features['glossiness_score'],
                    "complexity": texture_features['complexity_score']
                },

                # 3. Style Axis
                "style": {
                    "primary_keyword": style_features['primary_keyword'],
                    "primary_score": style_features['primary_score'],
                    "category": style_features['category'],
                    "vector_breakdown": style_features['vector_breakdown']
                }
            }
        }

        return result

    def analyze_prop(self, image: np.ndarray, image_id: str = None) -> Dict:
        """
        소품 이미지 분석

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            image_id: 이미지 ID (선택)

        Returns:
            readme.md의 JSON 형식에 맞는 분석 결과 딕셔너리
        """
        # 전처리: 배경 제거
        processed_image, mask = self.prop_processor.process(image)

        # 1. Color Vector 추출 (객체 영역만)
        color_features = self.color_extractor.extract(processed_image, mask)

        # 2. Shape/Geometry Vector 추출 (소품용 - 원형도)
        shape_features = self.shape_extractor.extract_prop(processed_image, mask)

        # 3. Texture Vector 추출 (객체 영역만)
        texture_features = self.texture_extractor.extract(processed_image, mask)

        # 4. Style Vector 추출 (전체 이미지 기준)
        style_features = self.style_extractor.extract(processed_image)

        # 결과 조합 (readme.md의 JSON 형식)
        # Prop의 경우 circularity를 사용 (linearity 대신)
        result = {
            "type": "prop",
            "id": image_id or "unknown",
            "analysis_result": {
                # 1. Color Axis
                "colors": {
                    "dominant_hex": color_features['dominant_hex'][:2],  # 상위 2개
                    "warmth_score": color_features['warmth_score']
                },

                # 2. Shape/Texture Axis
                "physics": {
                    "circularity": shape_features['circularity'],  # Prop은 circularity 사용
                    "glossiness": texture_features['glossiness_score'],
                    "complexity": texture_features['complexity_score']
                },

                # 3. Style Axis
                "style": {
                    "primary_keyword": style_features['primary_keyword'],
                    "primary_score": style_features['primary_score'],
                    "category": style_features['category'],
                    "vector_breakdown": style_features['vector_breakdown']
                }
            }
        }

        return result

    def analyze(
        self,
        image: np.ndarray,
        image_type: Literal['background', 'prop'],
        image_id: str = None
    ) -> Dict:
        """
        통합 분석 함수

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            image_type: 'background' 또는 'prop'
            image_id: 이미지 ID (선택)

        Returns:
            분석 결과 딕셔너리
        """
        if image_type == 'background':
            return self.analyze_background(image, image_id)
        elif image_type == 'prop':
            return self.analyze_prop(image, image_id)
        else:
            raise ValueError(f"Invalid image_type: {image_type}. Must be 'background' or 'prop'.")
