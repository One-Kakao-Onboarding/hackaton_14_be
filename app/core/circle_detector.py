"""
빨간색 원 감지 모듈
이미지에서 빨간색 원으로 표시된 영역을 찾음
"""
import cv2
import numpy as np
from typing import Tuple, Optional, List


class CircleDetector:
    """
    빨간색 원 감지 클래스
    """

    def __init__(self):
        """초기화"""
        pass

    def detect_red_circle(self, image: np.ndarray) -> Optional[Tuple[int, int, int]]:
        """
        이미지에서 빨간색 원 감지

        Args:
            image: OpenCV 형식의 이미지 (BGR)

        Returns:
            (center_x, center_y, radius) 또는 None
        """
        # Method 1: Hough Circle Transform (선으로 그려진 원 감지)
        circle_hough = self._detect_by_hough(image)

        # Method 2: Contour-based (채워진 원 감지)
        circle_contour = self._detect_by_contour(image)

        # 두 방법 중 더 큰 원 선택
        if circle_hough and circle_contour:
            if circle_hough[2] > circle_contour[2]:
                return circle_hough
            else:
                return circle_contour
        elif circle_hough:
            return circle_hough
        elif circle_contour:
            return circle_contour
        else:
            return None

    def _detect_by_hough(self, image: np.ndarray) -> Optional[Tuple[int, int, int]]:
        """Hough Circle Transform으로 원 감지 (선으로 그려진 원)"""
        # HSV로 변환
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 빨간색 범위
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        # Hough Circle Transform
        circles = cv2.HoughCircles(
            red_mask,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=20,
            maxRadius=200
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # 가장 큰 원 선택
            largest_circle = max(circles, key=lambda c: c[2])
            return (int(largest_circle[0]), int(largest_circle[1]), int(largest_circle[2]))

        return None

    def _detect_by_contour(self, image: np.ndarray) -> Optional[Tuple[int, int, int]]:
        """윤곽선 기반 원 감지 (채워진 원)"""
        # HSV로 변환
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 빨간색 범위
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        # 노이즈 제거
        kernel = np.ones((5, 5), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

        # 윤곽선 찾기
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # 원형이면서 가장 큰 윤곽선 찾기
        candidates = []

        for contour in contours:
            area = cv2.contourArea(contour)

            # 최소 면적 필터링
            if area < 100:
                continue

            # Circularity 계산
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            circularity = (4 * np.pi * area) / (perimeter ** 2)

            # 원형에 가까운 윤곽선만 선택
            if circularity > 0.3:
                candidates.append((contour, area, circularity))

        if not candidates:
            return None

        # 가장 큰 것 선택
        best_contour = max(candidates, key=lambda x: x[1])[0]

        # 최소 외접원 계산
        (x, y), radius = cv2.minEnclosingCircle(best_contour)

        return (int(x), int(y), int(radius))

    def extract_circle_region(
        self,
        image: np.ndarray,
        center_x: int,
        center_y: int,
        radius: int,
        padding: int = 20
    ) -> np.ndarray:
        """
        원으로 표시된 영역을 추출

        Args:
            image: 원본 이미지
            center_x: 원의 중심 X
            center_y: 원의 중심 Y
            radius: 원의 반지름
            padding: 추가 패딩

        Returns:
            크롭된 영역 이미지
        """
        # 경계 계산 (패딩 포함)
        x1 = max(0, center_x - radius - padding)
        y1 = max(0, center_y - radius - padding)
        x2 = min(image.shape[1], center_x + radius + padding)
        y2 = min(image.shape[0], center_y + radius + padding)

        # 영역 크롭
        cropped = image[y1:y2, x1:x2]

        return cropped

    def remove_red_circle(self, image: np.ndarray) -> np.ndarray:
        """
        이미지에서 빨간색 원 표시를 제거 (배경 분석용)

        Args:
            image: 원본 이미지

        Returns:
            빨간색 원이 제거된 이미지
        """
        # HSV로 변환
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 빨간색 범위
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        # 빨간색 마스크
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        # 형태학 연산으로 원 영역 확장
        kernel = np.ones((7, 7), np.uint8)
        red_mask = cv2.dilate(red_mask, kernel, iterations=2)

        # Inpainting으로 빨간색 영역 복원
        result = cv2.inpaint(image, red_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        return result

    def visualize_detection(
        self,
        image: np.ndarray,
        center_x: int,
        center_y: int,
        radius: int
    ) -> np.ndarray:
        """
        감지된 원을 시각화

        Args:
            image: 원본 이미지
            center_x: 원의 중심 X
            center_y: 원의 중심 Y
            radius: 원의 반지름

        Returns:
            원이 그려진 이미지
        """
        result = image.copy()
        cv2.circle(result, (center_x, center_y), radius, (0, 255, 0), 3)
        cv2.circle(result, (center_x, center_y), 5, (0, 255, 0), -1)
        return result
