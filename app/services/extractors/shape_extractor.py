"""
Shape/Geometry Vector Extraction Module
Hough Line Transform (배경) 및 Circularity (소품) 계산
"""
import cv2
import numpy as np
from typing import Dict
import math


class ShapeExtractor:
    """
    형태/기하학 특징 추출 클래스
    배경: 직선성(Linearity) 계산
    소품: 원형도(Circularity) 계산
    """

    def __init__(self):
        """
        초기화
        """
        pass

    def extract_background(self, image: np.ndarray, mask: np.ndarray = None) -> Dict:
        """
        배경 이미지의 형태 특징 추출 (직선성)

        Hough Line Transform을 사용하여 수직/수평선의 비율 계산
        직선이 많을수록 Modern, 적을수록 Curved

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            mask: 분석할 영역 마스크 (선택, 0-255)

        Returns:
            Dict containing:
                - 'linearity': 직선성 점수 (0.0=Curved, 1.0=Straight/Modern)
                - 'line_count': 검출된 직선 개수
                - 'horizontal_ratio': 수평선 비율
                - 'vertical_ratio': 수직선 비율
        """
        # Grayscale 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 마스크 적용
        if mask is not None:
            gray = cv2.bitwise_and(gray, gray, mask=mask)

        # 엣지 검출
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough Line Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=80,
            minLineLength=50,
            maxLineGap=10
        )

        if lines is None or len(lines) == 0:
            return {
                'linearity': 0.0,
                'line_count': 0,
                'horizontal_ratio': 0.0,
                'vertical_ratio': 0.0
            }

        # 수평선과 수직선 분류
        horizontal_count = 0
        vertical_count = 0

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # 각도 계산
            angle = math.atan2(y2 - y1, x2 - x1) * 180 / math.pi

            # 수평선: -15도 ~ 15도 또는 165도 ~ 195도
            if (-15 <= angle <= 15) or (165 <= abs(angle) <= 180):
                horizontal_count += 1
            # 수직선: 75도 ~ 105도 또는 -105도 ~ -75도
            elif (75 <= angle <= 105) or (-105 <= angle <= -75):
                vertical_count += 1

        total_lines = len(lines)
        straight_lines = horizontal_count + vertical_count

        # 직선성 점수 계산 (직선 비율)
        linearity = straight_lines / total_lines if total_lines > 0 else 0.0

        # 수평/수직 비율
        horizontal_ratio = horizontal_count / total_lines if total_lines > 0 else 0.0
        vertical_ratio = vertical_count / total_lines if total_lines > 0 else 0.0

        return {
            'linearity': float(linearity),
            'line_count': int(total_lines),
            'horizontal_ratio': float(horizontal_ratio),
            'vertical_ratio': float(vertical_ratio)
        }

    def extract_prop(self, image: np.ndarray, mask: np.ndarray) -> Dict:
        """
        소품 이미지의 형태 특징 추출 (원형도)

        Contour의 Circularity를 계산
        1.0에 가까울수록 원형(Soft), 낮을수록 각짐(Sharp)

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            mask: 객체 영역 마스크 (필수, 0-255)

        Returns:
            Dict containing:
                - 'circularity': 원형도 (0.0=Sharp/Angular, 1.0=Round/Soft)
                - 'area': 객체 면적
                - 'perimeter': 객체 둘레
                - 'aspect_ratio': 종횡비 (width/height)
        """
        # Contour 추출
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {
                'circularity': 0.0,
                'area': 0,
                'perimeter': 0,
                'aspect_ratio': 1.0
            }

        # 가장 큰 contour 선택
        largest_contour = max(contours, key=cv2.contourArea)

        # 면적과 둘레
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)

        # Circularity 계산: 4π * Area / Perimeter^2
        # 완전한 원: 1.0, 직선이나 복잡한 형태: 0에 가까움
        if perimeter > 0:
            circularity = (4 * math.pi * area) / (perimeter ** 2)
            circularity = min(circularity, 1.0)  # 1.0 초과 방지
        else:
            circularity = 0.0

        # Bounding Box로 종횡비 계산
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = w / h if h > 0 else 1.0

        return {
            'circularity': float(circularity),
            'area': float(area),
            'perimeter': float(perimeter),
            'aspect_ratio': float(aspect_ratio)
        }

    def extract(self, image: np.ndarray, mask: np.ndarray = None, image_type: str = 'background') -> Dict:
        """
        통합 추출 함수

        Args:
            image: OpenCV 형식의 이미지 (BGR)
            mask: 마스크 (선택)
            image_type: 'background' 또는 'prop'

        Returns:
            이미지 타입에 따른 형태 특징 딕셔너리
        """
        if image_type == 'background':
            return self.extract_background(image, mask)
        elif image_type == 'prop':
            if mask is None:
                raise ValueError("Mask is required for prop image type")
            return self.extract_prop(image, mask)
        else:
            raise ValueError(f"Unknown image_type: {image_type}")
