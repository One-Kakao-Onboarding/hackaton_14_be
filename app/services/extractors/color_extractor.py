"""
Color Vector Extraction Module
K-Means Clustering을 통한 주조색(Dominant Colors) 추출 및 Warm/Cool Score 계산
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
from sklearn.cluster import KMeans


class ColorExtractor:
    """
    색상 특징 추출 클래스
    이미지에서 주조색을 추출하고 색온도(Warm/Cool)를 계산
    """

    def __init__(self, n_colors: int = 5):
        """
        Args:
            n_colors: K-Means로 추출할 주조색 개수 (기본 5개)
        """
        self.n_colors = n_colors

    def extract(self, image: np.ndarray, mask: np.ndarray = None) -> Dict:
        """
        이미지에서 색상 특징 추출

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            mask: 분석할 영역 마스크 (선택, 0-255)

        Returns:
            Dict containing:
                - 'dominant_colors': 주조색 RGB 리스트 [[R,G,B], ...]
                - 'dominant_hex': 주조색 HEX 코드 리스트 ['#FFFFFF', ...]
                - 'color_percentages': 각 색상의 비율 [0.35, 0.25, ...]
                - 'warmth_score': 색온도 점수 (0.0=Cool, 1.0=Warm)
                - 'main_rgb': 가장 비중이 높은 색상 [R, G, B]
        """
        # 마스크가 있으면 해당 영역만 추출
        if mask is not None:
            pixels = image[mask > 0]
        else:
            pixels = image.reshape(-1, 3)

        # 빈 이미지 처리
        if len(pixels) == 0:
            return self._empty_result()

        # BGR -> RGB 변환
        pixels_rgb = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2RGB).reshape(-1, 3)

        # K-Means Clustering으로 주조색 추출
        kmeans = KMeans(n_clusters=self.n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels_rgb)

        # 클러스터 중심 (주조색)
        dominant_colors = kmeans.cluster_centers_.astype(int)

        # 각 색상의 비율 계산
        labels = kmeans.labels_
        label_counts = np.bincount(labels)
        color_percentages = label_counts / len(labels)

        # 비율 순으로 정렬
        sorted_indices = np.argsort(-color_percentages)
        dominant_colors = dominant_colors[sorted_indices]
        color_percentages = color_percentages[sorted_indices]

        # HEX 코드 변환
        dominant_hex = [self._rgb_to_hex(color) for color in dominant_colors]

        # Warm/Cool Score 계산
        warmth_score = self._calculate_warmth_score(pixels_rgb)

        # 가장 비중이 높은 색상
        main_rgb = dominant_colors[0].tolist()

        return {
            'dominant_colors': dominant_colors.tolist(),
            'dominant_hex': dominant_hex,
            'color_percentages': color_percentages.tolist(),
            'warmth_score': float(warmth_score),
            'main_rgb': main_rgb
        }

    def _calculate_warmth_score(self, pixels_rgb: np.ndarray) -> float:
        """
        색온도 점수 계산 (Warm vs Cool)

        Warm: Red/Yellow 계열 (높은 R, 높은 G)
        Cool: Blue 계열 (높은 B)

        Args:
            pixels_rgb: RGB 픽셀 배열 (N, 3)

        Returns:
            0.0 ~ 1.0 사이의 warmth score
            0.0 = 매우 차가운 색 (Cool)
            1.0 = 매우 따뜻한 색 (Warm)
        """
        # Lab 색공간으로 변환하여 a* 채널 사용
        # a* > 0: Red/Warm, a* < 0: Green/Cool
        # b* > 0: Yellow/Warm, b* < 0: Blue/Cool

        # RGB -> BGR 변환 (OpenCV용)
        pixels_bgr = pixels_rgb[:, ::-1]
        pixels_bgr = pixels_bgr.reshape(-1, 1, 3).astype(np.uint8)

        # Lab 변환
        pixels_lab = cv2.cvtColor(pixels_bgr, cv2.COLOR_BGR2Lab)
        pixels_lab = pixels_lab.reshape(-1, 3)

        # a* 채널 (Red-Green axis)
        a_channel = pixels_lab[:, 1].astype(float) - 128  # Lab의 a는 0-255이므로 중앙값 128 빼기
        # b* 채널 (Yellow-Blue axis)
        b_channel = pixels_lab[:, 2].astype(float) - 128

        # Warm 점수 계산: a*와 b*의 평균
        warm_score = (a_channel.mean() + b_channel.mean()) / 2

        # -128 ~ +128 범위를 0.0 ~ 1.0으로 정규화
        warmth_score = (warm_score + 128) / 256
        warmth_score = np.clip(warmth_score, 0.0, 1.0)

        return warmth_score

    def _rgb_to_hex(self, rgb: np.ndarray) -> str:
        """
        RGB를 HEX 코드로 변환

        Args:
            rgb: [R, G, B] 배열

        Returns:
            HEX 코드 문자열 (예: '#FFFFFF')
        """
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def _empty_result(self) -> Dict:
        """
        빈 이미지에 대한 기본 결과 반환
        """
        return {
            'dominant_colors': [[0, 0, 0]] * self.n_colors,
            'dominant_hex': ['#000000'] * self.n_colors,
            'color_percentages': [1.0 / self.n_colors] * self.n_colors,
            'warmth_score': 0.5,
            'main_rgb': [0, 0, 0]
        }
