"""
Texture Vector Extraction Module
질감 및 복잡도 분석 (Edge Density, Laplacian Variance, Glossiness)
"""
import cv2
import numpy as np
from typing import Dict


class TextureExtractor:
    """
    질감 특징 추출 클래스
    Edge Density, Laplacian Variance, Glossiness 계산
    """

    def __init__(self):
        """
        초기화
        """
        pass

    def extract(self, image: np.ndarray, mask: np.ndarray = None) -> Dict:
        """
        이미지에서 질감 특징 추출

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            mask: 분석할 영역 마스크 (선택, 0-255)

        Returns:
            Dict containing:
                - 'complexity_score': 복잡도 점수 (0.0=Simple, 1.0=Complex)
                - 'glossiness_score': 광택 점수 (0.0=Matte, 1.0=Glossy)
                - 'edge_density': 엣지 밀도 (0.0~1.0)
                - 'laplacian_variance': Laplacian 분산 (선명도/거칠기)
        """
        # Grayscale 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 마스크 적용
        if mask is not None:
            gray = cv2.bitwise_and(gray, gray, mask=mask)
            valid_pixels = np.count_nonzero(mask)
        else:
            valid_pixels = gray.shape[0] * gray.shape[1]

        # 1. Edge Density (Canny Edge)
        edge_density = self._calculate_edge_density(gray, valid_pixels)

        # 2. Laplacian Variance (선명도/거칠기)
        laplacian_variance = self._calculate_laplacian_variance(gray, mask)

        # 3. Glossiness (광택도)
        glossiness_score = self._calculate_glossiness(image, mask)

        # Complexity Score: Edge Density와 Laplacian Variance를 결합
        # 엣지가 많고 분산이 높을수록 복잡함
        complexity_score = (edge_density * 0.6 + min(laplacian_variance / 1000, 1.0) * 0.4)
        complexity_score = min(complexity_score, 1.0)

        return {
            'complexity_score': float(complexity_score),
            'glossiness_score': float(glossiness_score),
            'edge_density': float(edge_density),
            'laplacian_variance': float(laplacian_variance)
        }

    def _calculate_edge_density(self, gray: np.ndarray, valid_pixels: int) -> float:
        """
        Canny Edge Detection을 통한 엣지 밀도 계산

        Args:
            gray: Grayscale 이미지
            valid_pixels: 유효한 픽셀 개수

        Returns:
            0.0 ~ 1.0 사이의 엣지 밀도 (엣지 픽셀 비율)
        """
        # Canny Edge Detection
        edges = cv2.Canny(gray, 50, 150)

        # 엣지 픽셀 개수
        edge_pixels = np.count_nonzero(edges)

        # 밀도 계산
        density = edge_pixels / valid_pixels if valid_pixels > 0 else 0.0

        return density

    def _calculate_laplacian_variance(self, gray: np.ndarray, mask: np.ndarray = None) -> float:
        """
        Laplacian Variance를 통한 선명도/거칠기 측정

        높은 분산: 선명하고 디테일 많음 (거친 질감)
        낮은 분산: 흐릿하고 매끄러움 (부드러운 질감)

        Args:
            gray: Grayscale 이미지
            mask: 마스크 (선택)

        Returns:
            Laplacian의 분산 값
        """
        # Laplacian 필터 적용
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)

        # 마스크가 있으면 해당 영역만 계산
        if mask is not None:
            laplacian_masked = laplacian[mask > 0]
            variance = laplacian_masked.var()
        else:
            variance = laplacian.var()

        return variance

    def _calculate_glossiness(self, image: np.ndarray, mask: np.ndarray = None) -> float:
        """
        광택도 계산

        밝기 히스토그램에서 상위 5% 밝은 픽셀의 집중도 분석
        광택이 있는 표면: 하이라이트(밝은 영역)가 강하게 나타남

        Args:
            image: BGR 이미지
            mask: 마스크 (선택)

        Returns:
            0.0 ~ 1.0 사이의 광택도 점수
        """
        # Grayscale 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 마스크 적용
        if mask is not None:
            pixels = gray[mask > 0]
        else:
            pixels = gray.flatten()

        if len(pixels) == 0:
            return 0.0

        # 상위 5% 밝은 픽셀의 임계값
        threshold = np.percentile(pixels, 95)

        # 상위 5% 픽셀들
        bright_pixels = pixels[pixels >= threshold]

        if len(bright_pixels) == 0:
            return 0.0

        # 상위 5% 픽셀의 평균 밝기
        bright_mean = bright_pixels.mean()

        # 전체 평균 밝기
        overall_mean = pixels.mean()

        # 광택도: 밝은 영역과 전체 평균의 차이가 클수록 광택 있음
        # 밝기 차이를 정규화 (0~255 범위)
        glossiness = (bright_mean - overall_mean) / 255.0

        # 0.0 ~ 1.0 범위로 클리핑
        glossiness = np.clip(glossiness, 0.0, 1.0)

        return glossiness
