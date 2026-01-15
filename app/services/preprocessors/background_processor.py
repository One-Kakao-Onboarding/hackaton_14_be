"""
Background Preprocessing Module
배경 이미지에서 벽/바닥을 분리하는 Semantic Segmentation 처리
"""
import cv2
import numpy as np
from typing import Dict, Tuple
from PIL import Image


class BackgroundProcessor:
    """
    배경 이미지 전처리 클래스
    Semantic Segmentation을 통해 벽(wall)과 바닥(floor)을 분리
    """

    def __init__(self):
        """
        초기화 - 필요시 Segmentation 모델 로드
        TODO: DeepLabV3, U-Net 등의 모델 통합
        """
        pass

    def process(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        배경 이미지를 처리하여 벽/바닥 영역을 분리

        Args:
            image: OpenCV 형식의 이미지 (BGR)

        Returns:
            Dict containing:
                - 'original': 원본 이미지
                - 'wall': 벽 영역 이미지
                - 'floor': 바닥 영역 이미지
                - 'mask_wall': 벽 마스크 (0-255)
                - 'mask_floor': 바닥 마스크 (0-255)
        """
        # TODO: 실제 Semantic Segmentation 모델 적용
        # 현재는 간단한 색상 기반 분할로 placeholder 구현

        height, width = image.shape[:2]

        # Placeholder: 상단 60%를 벽, 하단 40%를 바닥으로 간주
        wall_mask = np.zeros((height, width), dtype=np.uint8)
        floor_mask = np.zeros((height, width), dtype=np.uint8)

        split_line = int(height * 0.6)
        wall_mask[:split_line, :] = 255
        floor_mask[split_line:, :] = 255

        # 마스크 적용하여 영역 추출
        wall_image = cv2.bitwise_and(image, image, mask=wall_mask)
        floor_image = cv2.bitwise_and(image, image, mask=floor_mask)

        return {
            'original': image,
            'wall': wall_image,
            'floor': floor_image,
            'mask_wall': wall_mask,
            'mask_floor': floor_mask
        }

    def load_image(self, image_path: str) -> np.ndarray:
        """
        이미지 파일을 로드

        Args:
            image_path: 이미지 파일 경로

        Returns:
            OpenCV 형식의 이미지 (BGR)
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        return image

    def load_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """
        바이트 데이터에서 이미지 로드 (FastAPI 업로드용)

        Args:
            image_bytes: 이미지 바이트 데이터

        Returns:
            OpenCV 형식의 이미지 (BGR)
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image from bytes")
        return image
