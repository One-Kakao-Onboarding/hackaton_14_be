"""
이미지 변환 유틸리티 모듈
Base64 ↔ OpenCV Image 변환
"""
import base64
import numpy as np
import cv2
from PIL import Image
import io
from typing import Optional


def base64_to_opencv(base64_string: str) -> np.ndarray:
    """
    Base64 문자열을 OpenCV 이미지(numpy array)로 변환

    Args:
        base64_string: Base64로 인코딩된 이미지 문자열

    Returns:
        OpenCV 형식의 이미지 (BGR, numpy.ndarray)

    Raises:
        ValueError: 디코딩 실패 시
    """
    try:
        # Base64 디코딩
        image_bytes = base64.b64decode(base64_string)

        # PIL Image로 로드
        image_pil = Image.open(io.BytesIO(image_bytes))

        # numpy array로 변환
        image_array = np.array(image_pil)

        # 채널 수에 따라 처리
        if len(image_array.shape) == 2:
            # Grayscale → BGR
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
        elif image_array.shape[2] == 4:
            # RGBA → BGR (알파 채널 제거)
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
        elif image_array.shape[2] == 3:
            # RGB → BGR
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            raise ValueError(f"Unsupported image format: {image_array.shape}")

        return image_bgr

    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {str(e)}")


def opencv_to_base64(image: np.ndarray, format: str = 'PNG') -> str:
    """
    OpenCV 이미지를 Base64 문자열로 변환

    Args:
        image: OpenCV 형식의 이미지 (BGR)
        format: 저장 포맷 ('PNG', 'JPEG')

    Returns:
        Base64로 인코딩된 문자열
    """
    # BGR → RGB 변환
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # PIL Image로 변환
    pil_image = Image.fromarray(image_rgb)

    # BytesIO에 저장
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    buffer.seek(0)

    # Base64 인코딩
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return image_base64


def bytes_to_opencv(image_bytes: bytes) -> np.ndarray:
    """
    바이트 데이터를 OpenCV 이미지로 변환 (FastAPI 업로드용)

    Args:
        image_bytes: 이미지 바이트 데이터

    Returns:
        OpenCV 형식의 이미지 (BGR)

    Raises:
        ValueError: 디코딩 실패 시
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image from bytes")

        return image

    except Exception as e:
        raise ValueError(f"Failed to convert bytes to image: {str(e)}")


def resize_image(
    image: np.ndarray,
    max_width: int = 1024,
    max_height: int = 1024,
    keep_aspect: bool = True
) -> np.ndarray:
    """
    이미지 크기 조정 (처리 성능 향상용)

    Args:
        image: OpenCV 이미지
        max_width: 최대 너비
        max_height: 최대 높이
        keep_aspect: 종횡비 유지 여부

    Returns:
        리사이즈된 이미지
    """
    height, width = image.shape[:2]

    if width <= max_width and height <= max_height:
        return image

    if keep_aspect:
        # 종횡비 유지하며 리사이즈
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
    else:
        new_width = max_width
        new_height = max_height

    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized


def validate_image(image: np.ndarray) -> bool:
    """
    이미지 유효성 검사

    Args:
        image: OpenCV 이미지

    Returns:
        유효하면 True, 아니면 False
    """
    if image is None:
        return False

    if not isinstance(image, np.ndarray):
        return False

    if len(image.shape) not in [2, 3]:
        return False

    if image.shape[0] == 0 or image.shape[1] == 0:
        return False

    return True
