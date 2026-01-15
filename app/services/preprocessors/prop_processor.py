"""
Prop Preprocessing Module
소품 이미지에서 배경을 제거(누끼)하는 모듈
"""
import cv2
import numpy as np
from typing import Tuple
from PIL import Image
from rembg import remove


class PropProcessor:
    """
    소품 이미지 전처리 클래스
    배경 제거(Background Removal)를 통해 객체만 추출
    """

    def __init__(self):
        """
        초기화
        """
        pass

    def process(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        소품 이미지에서 배경을 제거하고 객체만 추출

        Args:
            image: OpenCV 형식의 이미지 (BGR)

        Returns:
            Tuple containing:
                - removed_bg_image: 배경이 제거된 이미지 (RGBA)
                - mask: 객체 영역 마스크 (0-255)
        """
        # OpenCV BGR -> PIL RGB 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # rembg로 배경 제거 (RGBA 반환)
        output_pil = remove(pil_image)

        # PIL -> numpy 배열 변환
        output_rgba = np.array(output_pil)

        # 알파 채널을 마스크로 추출
        if output_rgba.shape[2] == 4:
            mask = output_rgba[:, :, 3]
            # RGBA -> BGR 변환 (알파 채널 제거)
            output_bgr = cv2.cvtColor(output_rgba, cv2.COLOR_RGBA2BGR)
        else:
            # 알파 채널이 없는 경우 전체를 객체로 간주
            mask = np.full((output_rgba.shape[0], output_rgba.shape[1]), 255, dtype=np.uint8)
            output_bgr = cv2.cvtColor(output_rgba, cv2.COLOR_RGB2BGR)

        return output_bgr, mask

    def get_object_bbox(self, mask: np.ndarray) -> Tuple[int, int, int, int]:
        """
        객체의 Bounding Box 좌표 추출

        Args:
            mask: 객체 마스크 (0-255)

        Returns:
            (x, y, width, height) 형식의 bbox
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return (0, 0, mask.shape[1], mask.shape[0])

        # 가장 큰 contour 선택
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        return (x, y, w, h)

    def crop_to_object(self, image: np.ndarray, mask: np.ndarray, padding: int = 10) -> np.ndarray:
        """
        객체 영역만 크롭 (패딩 포함)

        Args:
            image: 원본 이미지
            mask: 객체 마스크
            padding: 크롭 시 추가할 패딩 픽셀

        Returns:
            크롭된 이미지
        """
        x, y, w, h = self.get_object_bbox(mask)

        # 패딩 적용
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.shape[1], x + w + padding)
        y2 = min(image.shape[0], y + h + padding)

        cropped = image[y1:y2, x1:x2]
        return cropped

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
