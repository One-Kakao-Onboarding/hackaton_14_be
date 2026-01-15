"""
AI 인테리어 생성 API
Frontend 명세서에 맞춘 엔드포인트
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Optional
import cv2
import numpy as np
import json
import base64
from pydantic import BaseModel
import time
import os
from io import BytesIO
from PIL import Image

from app.core.circle_detector import CircleDetector
from app.core.gemini_analyzer import GeminiAnalyzer
from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager
from app.core.product_loader import get_product_loader
import re


router = APIRouter()


def infer_product_placement_type(product_name: str) -> str:
    """
    상품명으로부터 배치 유형을 추론

    Args:
        product_name: 상품명

    Returns:
        "wall": 벽걸이/벽부착 상품
        "floor": 바닥에 놓는 상품
        "table": 테이블/가구 위에 올리는 상품
        "any": 어디에나 가능
    """
    name_lower = product_name.lower()

    # 벽걸이 키워드
    wall_keywords = [
        '벽걸이', '벽시계', '액자', '그림', '거울', '미러', '벽선반', '벽 선반',
        '스위치', '벽등', '벽조명', '월', 'wall', '벽부착', '벽면',
        '벽걸이형', '월클락', '월미러', '월선반'
    ]

    # 바닥 가구 키워드
    floor_keywords = [
        '책장', '옷장', '수납장', '책상', '테이블', '의자', '소파', '침대',
        '서랍장', '행거', '옷걸이', '선반장', '캐비닛', '콘솔', '화분대',
        '스탠드', '조명스탠드', '장롱', '붙박이', '수납박스', '바구니',
        '가구', 'furniture', '3단', '4단', '5단', '다단', '다용도수납'
    ]

    # 탁상 소품 키워드
    table_keywords = [
        '탁상', '데스크', '미니', '소형', '컵', '홀더', '정리함', '펜꽂이',
        '시계', '액자', '화분', '캔들', '향초', '디퓨저', '소품', '장식',
        '오브제', '피규어', '인형', '쿠션', '쿠션커버'
    ]

    # 우선순위: 벽걸이 > 바닥 > 탁상
    for keyword in wall_keywords:
        if keyword in name_lower:
            return "wall"

    for keyword in floor_keywords:
        if keyword in name_lower:
            return "floor"

    for keyword in table_keywords:
        if keyword in name_lower:
            return "table"

    return "any"


def calculate_spatial_suitability_score(
    placement_surface: str,
    product_placement_type: str
) -> float:
    """
    공간 적합성 점수 계산

    Args:
        placement_surface: Gemini가 분석한 공간 유형 ("wall", "floor", "ceiling", "furniture_surface")
        product_placement_type: 상품 배치 유형 ("wall", "floor", "table", "any")

    Returns:
        0.0 ~ 1.0 점수 (1.0 = 완벽히 적합, 0.0 = 전혀 부적합)
    """
    # 완벽한 매칭
    perfect_match = {
        ("wall", "wall"): 1.0,
        ("floor", "floor"): 1.0,
        ("furniture_surface", "table"): 1.0,
    }

    # 적절한 매칭
    good_match = {
        ("floor", "table"): 0.7,  # 바닥에 탁상 소품도 괜찮음 (작은 가구처럼)
        ("furniture_surface", "any"): 0.8,
    }

    # 부적합한 매칭
    poor_match = {
        ("wall", "floor"): 0.1,  # 벽면에 바닥 가구 = 매우 부적합
        ("wall", "table"): 0.3,  # 벽면에 탁상 소품 = 부적합 (벽선반이 아닌 이상)
        ("floor", "wall"): 0.2,  # 바닥에 벽걸이 = 매우 부적합
        ("ceiling", "floor"): 0.0,  # 천장에 바닥 가구 = 불가능
        ("ceiling", "wall"): 0.0,  # 천장에 벽걸이 = 불가능
    }

    # any는 어디에나 가능
    if product_placement_type == "any":
        return 0.8

    # 매칭 테이블에서 점수 찾기
    key = (placement_surface, product_placement_type)

    if key in perfect_match:
        return perfect_match[key]
    elif key in good_match:
        return good_match[key]
    elif key in poor_match:
        return poor_match[key]
    else:
        # 정의되지 않은 조합은 중립
        return 0.5


def calculate_keyword_match_score(product_name: str, gemini_keywords: List[str]) -> float:
    """
    상품 이름과 Gemini 추천 키워드 간의 매칭 점수 계산

    Args:
        product_name: 상품명 (예: "소프시스 포인트 다용도 3단 선반")
        gemini_keywords: Gemini 추천 키워드 리스트 (예: ["사이드 테이블", "스탠드 조명", "화분"])

    Returns:
        매칭 점수 (0.0 ~ 1.0)
    """
    if not gemini_keywords:
        return 0.5  # 키워드 없으면 중립 점수

    product_name_lower = product_name.lower()
    max_score = 0.0

    for keyword in gemini_keywords:
        keyword_lower = keyword.lower()

        # 키워드 정규화 (공백 제거, 한글/영어 모두 지원)
        keyword_clean = re.sub(r'\s+', '', keyword_lower)
        product_clean = re.sub(r'\s+', '', product_name_lower)

        # 1. 완전 일치
        if keyword_clean in product_clean or product_clean in keyword_clean:
            max_score = max(max_score, 1.0)
            continue

        # 2. 부분 매칭 (키워드 토큰 분리)
        keyword_tokens = keyword_lower.split()
        match_count = sum(1 for token in keyword_tokens if token in product_name_lower)

        if match_count > 0:
            partial_score = match_count / len(keyword_tokens)
            max_score = max(max_score, partial_score * 0.8)  # 부분 매칭은 최대 0.8

        # 3. 유사 키워드 매칭 (동의어)
        synonym_map = {
            '테이블': ['탁자', '책상', '데스크', '선반', '협탁'],
            '조명': ['램프', '등', '라이트', '스탠드'],
            '화분': ['식물', '플랜트', '화초', '그린'],
            '의자': ['체어', '스툴', '좌석'],
            '수납': ['정리', '보관', '수납장', '서랍'],
            '시계': ['클락', 'clock'],
            '액자': ['프레임', '그림'],
            '거울': ['미러'],
        }

        for main_word, synonyms in synonym_map.items():
            if main_word in keyword_lower:
                for syn in synonyms:
                    if syn in product_name_lower:
                        max_score = max(max_score, 0.7)  # 동의어 매칭

    return max_score


# 요청 모델
class CircleInfo(BaseModel):
    x: float  # 상대 좌표 0.0 ~ 1.0 (왼쪽=0, 오른쪽=1)
    y: float  # 상대 좌표 0.0 ~ 1.0 (아래=0, 위=1)
    radius: float  # 상대 크기 0.0 ~ 1.0 (이미지 너비 기준)


# 응답 모델
class AIInteriorResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    circle_info: Optional[Dict] = None
    background_mood: Optional[Dict] = None
    recommended_products: Optional[List[Dict]] = None


def _simulate_product_in_room(
    background_image: np.ndarray,
    product_image_base64: str,
    product_name: str,
    circle_x: int,
    circle_y: int,
    circle_radius: int,
    product_thumbnail_url: Optional[str] = None
) -> Optional[str]:
    """
    Gemini Nano Banana를 사용해 상품을 배경에 합성한 시뮬레이션 이미지 생성

    Args:
        background_image: 배경 이미지 (OpenCV BGR)
        product_image_base64: 상품 이미지 (Base64, 배경 제거됨)
        product_name: 상품명
        circle_x, circle_y, circle_radius: 동그라미 위치 및 크기
        product_thumbnail_url: 원본 썸네일 URL (공간적 컨텍스트 참조용)

    Returns:
        base64 인코딩된 시뮬레이션 이미지 (PNG) 또는 None
    """
    try:
        # Gemini API 사용 가능 여부 확인
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            print("⚠️  GEMINI_API_KEY 없음. Mock 시뮬레이션 사용")
            return _mock_simulate_product(background_image, product_name, circle_x, circle_y, circle_radius)

        # Gemini Nano Banana로 실제 이미지 합성
        try:
            from google import genai
            from google.genai import types

            # Gemini 클라이언트 생성
            client = genai.Client(api_key=api_key)

            # 배경 이미지: OpenCV BGR -> RGB PIL Image 변환
            rgb_image = cv2.cvtColor(background_image, cv2.COLOR_BGR2RGB)
            pil_bg = Image.fromarray(rgb_image)

            # 상품 이미지: Base64 -> PIL Image 변환
            if not product_image_base64:
                print(f"   ⚠️  상품 이미지 없음. Mock 사용")
                return _mock_simulate_product(background_image, product_name, circle_x, circle_y, circle_radius)

            # data:image/png;base64, 프리픽스 제거
            product_b64 = product_image_base64
            if ',' in product_b64 and product_b64.startswith('data:'):
                product_b64 = product_b64.split(',', 1)[1]

            product_image_data = base64.b64decode(product_b64)
            pil_product = Image.open(BytesIO(product_image_data))

            # 원본 썸네일 이미지 다운로드 (공간적 컨텍스트 참조용)
            pil_thumbnail = None
            if product_thumbnail_url:
                try:
                    import requests
                    print(f"   📥 원본 썸네일 다운로드 중...")
                    thumbnail_response = requests.get(product_thumbnail_url, timeout=10)
                    if thumbnail_response.status_code == 200:
                        pil_thumbnail = Image.open(BytesIO(thumbnail_response.content))
                        print(f"   ✅ 원본 썸네일 로드 성공 ({len(thumbnail_response.content)/1024:.1f}KB)")
                    else:
                        print(f"   ⚠️  썸네일 다운로드 실패: HTTP {thumbnail_response.status_code}")
                except Exception as e:
                    print(f"   ⚠️  썸네일 다운로드 오류: {e}")

            # 이미지 크기
            img_height, img_width = background_image.shape[:2]

            # 상대 위치 계산 (이미지 기준 퍼센트)
            rel_x = (circle_x / img_width) * 100
            rel_y = (circle_y / img_height) * 100
            rel_size = (circle_radius * 2 / img_width) * 100

            # 위치 설명 생성
            if rel_x < 33:
                x_desc = "left side"
            elif rel_x > 66:
                x_desc = "right side"
            else:
                x_desc = "center"

            if rel_y < 33:
                y_desc = "top"
            elif rel_y > 66:
                y_desc = "bottom"
            else:
                y_desc = "middle"

            location_desc = f"{y_desc} {x_desc}"

            # 프롬프트 생성 (상품 제목과 용도를 고려)
            thumbnail_instruction = ""
            if pil_thumbnail:
                thumbnail_instruction = """5. REFERENCE IMAGE: Original product thumbnail showing spatial context
   - This shows how the product naturally exists in space (on wall, on floor, on table, etc.)
   - Use this as reference for proper placement, scale, and viewing angle
   - Match the product's orientation and positioning style from this reference
"""

            prompt = f"""You are an expert CGI artist and photo-realistic compositor specializing in seamless product integration for interior design visualization.

MISSION:
Add a single product to the existing room photograph. This is an OBJECT INSERTION task, NOT a scene generation task.

INPUTS:
1. BASE IMAGE: Original interior room photograph
2. PRODUCT IMAGE: Isolated product with transparent background
3. PRODUCT NAME: "{product_name}"
4. TARGET LOCATION: Approximately ({rel_x:.1f}%, {rel_y:.1f}%) - {location_desc} area
{thumbnail_instruction}

⚠️ CRITICAL RULE #1: PRESERVE 100% OF THE ORIGINAL BACKGROUND ⚠️
- DO NOT modify, replace, or regenerate ANY part of the original room
- DO NOT create new walls, floors, ceilings, or backgrounds
- DO NOT change the room's architecture, windows, doors, or furniture
- ONLY ADD the product to the existing scene
- Think of this as "inpainting" or "object insertion" - the background must remain pixel-perfect identical
- If the target area shows a window, place product near/on the window frame - DO NOT replace the window with a wall
- If the target area shows existing furniture, place product on/near it - DO NOT remove or modify the furniture

CRITICAL REALISM REQUIREMENTS:

1. [CAMERA PERSPECTIVE & SCALE]
   - **Match the camera angle**: Analyze the room's perspective lines (walls, floor, ceiling converging points)
   - **Match the focal length**: Observe lens distortion in the original photo
   - **Scale appropriately**: The product must have realistic proportions relative to nearby objects
   - **Apply correct foreshortening**: Objects closer to camera appear larger
   - **Maintain vanishing points**: Ensure product follows same perspective as room

2. [LIGHTING & SHADOWS - CRITICAL]
   - **Identify light source**: Determine exact direction, intensity, warmth (soft/hard light)
   - **Cast accurate shadows**:
     * Contact shadows (dark, sharp at contact point)
     * Cast shadows (softer, longer, following light direction)
     * Shadow opacity based on light intensity
   - **Add ambient occlusion**: Subtle darkening where product meets surface
   - **Match highlights**: Product shine must match room's lighting conditions
   - **Light color temperature**: Warm/cool tones must match the room's atmosphere

3. [MOOD & ATMOSPHERE MATCHING]
   - **Color grading**: Match the room's overall color tone (warm/cool/neutral)
   - **Exposure level**: Product brightness must match ambient light level
   - **Contrast**: Match the room's contrast level (soft/harsh)
   - **Saturation**: Align product color saturation with room's palette
   - **White balance**: Ensure product whites match room whites

4. [INTEGRATION DETAILS]
   - **Depth of field**: If background is slightly blurred, blur product edges similarly
   - **Film grain/noise**: Match the image sensor noise pattern
   - **Color bleeding**: Add subtle color reflection from nearby objects
   - **Atmospheric haze**: Add slight haze if present in original photo
   - **Edge softness**: Avoid hard cutout edges - blend naturally

5. [PLACEMENT LOGIC - PRESERVE EXISTING SCENE]
   Product type: "{product_name}"
   - FIRST: Identify what's ALREADY in the target location (wall? window? furniture? door?)
   - SECOND: Place product in a way that makes sense with what's already there
   - Wall-mounted items: Place ON THE EXISTING WALL - do not create a new wall
   - Floor items: Place ON THE EXISTING FLOOR - do not modify floor texture
   - Table items: Place ON EXISTING FURNITURE - do not replace furniture
   - **CRITICAL**: If reference thumbnail is provided, observe how the product is positioned in its original context
     * Is it photographed from above/below/straight-on? Match that viewing angle
     * Is it on a surface or mounted? Use that as guidance
     * What's the distance/scale in the reference? Match proportionally
   - If target area has a window: Place product near the window (on window frame or adjacent wall), DO NOT cover or replace the window
   - If target area is empty space: Add product naturally without changing the background

6. [FINAL QUALITY CHECK]
   - ⚠️ MOST IMPORTANT: Original room background is 100% preserved (no new walls/floors/ceilings)
   - Product appears naturally added to the scene (not replacing scene elements)
   - No floating objects - ensure proper surface contact with EXISTING surfaces
   - No artificial-looking edges or halos
   - Shadows point in same direction as other objects in room
   - Product appears to be affected by same light as the room
   - Overall composition looks like product was naturally placed in room during original photo

OUTPUT REQUIREMENT:
Return the original room photograph WITH THE PRODUCT ADDED. The background must be identical to the input image. Only the product should be new. The viewer should see the exact same room with one new item added naturally."""

            print(f"   🎨 Gemini 이미지 편집 중: {product_name}")

            # Gemini API 호출 (배경 + 상품 이미지 + 원본 썸네일)
            contents = [prompt, pil_bg, pil_product]
            if pil_thumbnail:
                contents.append(pil_thumbnail)
                print(f"   📸 원본 썸네일 공간 컨텍스트 반영")

            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=contents
            )

            # 생성된 이미지 추출
            if response and hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]

                # 이미지 파트 찾기
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # 이미지 데이터 추출
                        image_data = part.inline_data.data

                        # PIL Image로 변환
                        generated_image = Image.open(BytesIO(image_data))

                        # base64 인코딩
                        buffer = BytesIO()
                        generated_image.save(buffer, format='PNG')
                        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                        print(f"   ✅ Gemini 이미지 생성 완료 ({len(image_data)/1024:.1f}KB)")
                        return image_base64

            # 이미지를 찾지 못한 경우
            print(f"   ⚠️  Gemini 응답에 이미지 없음. Mock 사용")
            return _mock_simulate_product(background_image, product_name, circle_x, circle_y, circle_radius)

        except ImportError:
            print("⚠️  google.genai 패키지 없음. Mock 시뮬레이션 사용")
            print("   설치: pip install google-genai")
            return _mock_simulate_product(background_image, product_name, circle_x, circle_y, circle_radius)
        except Exception as e:
            print(f"⚠️  Gemini 이미지 생성 실패: {e}")
            print(f"   Mock 시뮬레이션으로 대체")
            import traceback
            traceback.print_exc()
            return _mock_simulate_product(background_image, product_name, circle_x, circle_y, circle_radius)

    except Exception as e:
        print(f"이미지 시뮬레이션 오류: {e}")
        return None


def _mock_simulate_product(
    background_image: np.ndarray,
    product_name: str,
    circle_x: int,
    circle_y: int,
    circle_radius: int
) -> str:
    """
    Mock 이미지 시뮬레이션 (실제 Gemini API 대신 사용)
    배경 이미지에 상품 위치를 표시
    """
    # 이미지 복사
    result_image = background_image.copy()

    # 동그라미 영역에 반투명 원 그리기
    overlay = result_image.copy()
    cv2.circle(overlay, (circle_x, circle_y), circle_radius, (100, 200, 100), -1)
    cv2.addWeighted(overlay, 0.3, result_image, 0.7, 0, result_image)

    # 상품명 텍스트 추가
    cv2.circle(result_image, (circle_x, circle_y), circle_radius, (0, 255, 0), 3)

    # 텍스트 위치 계산 (동그라미 위쪽)
    text_y = max(30, circle_y - circle_radius - 10)
    cv2.putText(
        result_image,
        product_name,
        (circle_x - 100, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    # BGR -> RGB -> PIL -> base64
    rgb_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)

    # base64 인코딩
    buffer = BytesIO()
    pil_image.save(buffer, format='PNG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return image_base64


@router.post("/ai-interior", response_model=AIInteriorResponse)
async def generate_ai_interior(
    image: UploadFile = File(..., description="방 이미지 파일 (PNG, JPEG)"),
    circles: str = Form(..., description="동그라미 영역 정보 (JSON 배열)")
):
    """
    AI 인테리어 생성 API (단일 동그라미 처리)

    첫 번째 동그라미 영역만 분석하고 상품을 추천합니다.
    추천 상품들을 배경에 합성한 시뮬레이션 이미지도 함께 제공합니다.

    Args:
        image: 방 이미지 파일
        circles: JSON 문자열 - [{"x": 100, "y": 200, "radius": 50}] (첫 번째만 사용)

    Returns:
        success: 성공 여부
        circle_info: 동그라미 영역 분석 결과
        background_mood: 배경 무드 분석 결과
        recommended_products: 추천 상품 목록 (시뮬레이션 이미지 포함)
    """
    start_time = time.time()

    try:
        # 1. 이미지 파일 검증
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=415, detail="지원하지 않는 미디어 타입입니다. PNG 또는 JPEG 파일을 업로드해주세요.")

        # 2. 이미지 파일 읽기
        image_bytes = await image.read()

        # 파일 크기 검증 (10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="파일 크기가 너무 큽니다. 최대 10MB까지 지원됩니다.")

        # 3. OpenCV 이미지로 변환
        nparr = np.frombuffer(image_bytes, np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if cv_image is None:
            raise HTTPException(status_code=400, detail="이미지를 읽을 수 없습니다. 올바른 이미지 파일인지 확인해주세요.")

        # 4. circles JSON 파싱
        try:
            circles_data = json.loads(circles)
            if not isinstance(circles_data, list):
                raise ValueError("circles는 배열이어야 합니다.")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="circles 파라미터가 올바른 JSON 형식이 아닙니다.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 5. circles 배열이 비어있으면 에러
        if len(circles_data) == 0:
            raise HTTPException(status_code=400, detail="최소 1개의 동그라미 정보가 필요합니다.")

        # 6. 첫 번째 동그라미만 처리
        circle = circles_data[0]

        try:
            # 상대 좌표 (0.0~1.0)를 절대 좌표로 변환
            # Frontend: 왼쪽 아래가 (0, 0), 오른쪽 위가 (1, 1)
            # OpenCV: 왼쪽 위가 (0, 0), 오른쪽 아래가 (width, height)

            image_height, image_width = cv_image.shape[:2]

            x_relative = float(circle['x'])  # 0.0 (왼쪽) ~ 1.0 (오른쪽)
            y_relative = float(circle['y'])  # 0.0 (아래) ~ 1.0 (위)
            radius_relative = float(circle['radius'])  # 0.0 ~ 1.0 (이미지 너비 기준)

            # 입력 값 검증 (0.0 ~ 1.0 범위)
            if not (0.0 <= x_relative <= 1.0 and 0.0 <= y_relative <= 1.0 and 0.0 <= radius_relative <= 1.0):
                raise ValueError("좌표 값은 0.0과 1.0 사이여야 합니다.")

            # 절대 좌표로 변환
            center_x = int(round(x_relative * image_width))
            center_y = int(round((1.0 - y_relative) * image_height))  # Y축 반전 (아래->위를 위->아래로)
            radius = int(round(radius_relative * image_width))

            print(f"📍 좌표 변환:")
            print(f"   입력 (상대): x={x_relative:.4f}, y={y_relative:.4f}, r={radius_relative:.4f}")
            print(f"   이미지 크기: {image_width}x{image_height}")
            print(f"   출력 (절대): x={center_x}, y={center_y}, r={radius}")

        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {str(e)}")
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"좌표 값이 올바르지 않습니다: {str(e)}")

        # 7. 영역 분석
        circle_detector = CircleDetector()
        gemini_analyzer = GeminiAnalyzer()
        mood_analyzer = MoodAnalyzer()
        vector_manager = MoodVectorManager()

        # 영역 추출
        region_image = circle_detector.extract_circle_region(
            cv_image, center_x, center_y, radius
        )

        # Gemini로 영역 분석
        print(f"🤖 Gemini로 영역 분석 중...")
        gemini_result = gemini_analyzer.analyze_region(region_image)

        # 배경 무드 분석 (동그라미 영역을 마스킹하여 제외)
        print(f"🎨 배경 무드 분석 중...")
        # 동그라미 영역 마스크 생성
        mask = np.zeros(cv_image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (center_x, center_y), radius, 255, -1)

        # 배경 이미지 복사 후 동그라미 영역을 주변 픽셀로 inpainting
        clean_bg = cv2.inpaint(cv_image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        bg_analysis = mood_analyzer.analyze(
            image=clean_bg,
            image_type='background',
            image_id='ai_interior'
        )

        # Mood Vector 생성
        bg_mood_vector = vector_manager.create_mood_vector(bg_analysis, image_type='background')

        # 8. JSON에서 상품 후보 가져오기
        # Gemini 분석 결과에 따라 카테고리 결정
        if gemini_result['category'] == 'furniture':
            search_category = 'furniture'
        else:
            search_category = 'prop'

        print(f"🛍️ 상품 추천 중... (카테고리: {search_category})")

        # ProductLoader에서 유사 상품 검색
        product_loader = get_product_loader()
        candidates = product_loader.search_similar(
            mood_vector=bg_mood_vector,  # 이미 리스트임
            category=search_category,
            top_k=10
        )

        # 9. 상품 순위 재계산 (weighted method)
        ranked_products = vector_manager.rank_products(
            background_vector=bg_mood_vector,
            product_vectors=candidates,
            top_k=5,  # 키워드 매칭 전에 5개 선택
            method='weighted'
        )

        # 10. Gemini 추천 키워드 + 공간 적합성 기반 재순위화
        gemini_keywords = gemini_result.get('recommendations', [])
        placement_surface = gemini_result.get('placement_surface', 'floor')  # 공간 유형

        print(f"🔍 Gemini 키워드 매칭 중... (키워드: {gemini_keywords})")
        print(f"📍 공간 유형: {placement_surface}")

        for product in ranked_products:
            # 키워드 매칭 점수 계산
            keyword_score = calculate_keyword_match_score(
                product_name=product['name'],
                gemini_keywords=gemini_keywords
            )

            # 공간 적합성 점수 계산
            product_placement_type = infer_product_placement_type(product['name'])
            spatial_score = calculate_spatial_suitability_score(
                placement_surface=placement_surface,
                product_placement_type=product_placement_type
            )

            # 무드 점수 + 키워드 점수 + 공간 적합성 점수 결합
            # (무드 50%, 키워드 10%, 공간적합성 40%)
            mood_score = product['match_score']
            combined_score = mood_score * 0.5 + keyword_score * 0.1 + spatial_score * 0.4

            # 점수 업데이트
            product['keyword_match_score'] = keyword_score
            product['spatial_suitability_score'] = spatial_score
            product['product_placement_type'] = product_placement_type
            product['original_mood_score'] = mood_score
            product['match_score'] = combined_score

            print(f"   {product['name'][:50]}")
            print(f"      무드: {mood_score:.3f} | 키워드: {keyword_score:.3f} | 공간: {spatial_score:.3f} ({product_placement_type}) | 최종: {combined_score:.3f}")

        # 최종 점수로 재정렬
        ranked_products.sort(key=lambda x: x['match_score'], reverse=True)

        # 최상위 1개만 선택
        ranked_products = ranked_products[:1]

        # 11. 각 추천 상품에 대해 시뮬레이션 이미지 생성
        print(f"🎨 시뮬레이션 이미지 생성 중...")
        recommended_products_with_simulation = []

        for product in ranked_products:
            simulated_image_base64 = _simulate_product_in_room(
                background_image=cv_image,
                product_image_base64=product.get('removed_bg_image_base64', ''),
                product_name=product['name'],
                circle_x=center_x,
                circle_y=center_y,
                circle_radius=radius,
                product_thumbnail_url=product.get('image_url', '')
            )

            # match_details에 모든 점수 추가
            match_details = product['match_details'].copy()
            match_details['keyword_match_score'] = product['keyword_match_score']
            match_details['spatial_suitability_score'] = product['spatial_suitability_score']
            match_details['product_placement_type'] = product['product_placement_type']
            match_details['original_mood_score'] = product['original_mood_score']

            recommended_products_with_simulation.append({
                'product_id': product['product_id'],
                'name': product['name'],
                'category': product.get('category'),
                'price': product.get('price'),
                'image_url': product.get('image_url'),
                'match_score': product['match_score'],
                'match_details': match_details,
                'simulated_image_base64': simulated_image_base64
            })

        # 11. 응답 생성
        processing_time = (time.time() - start_time) * 1000

        bg_style = bg_analysis['analysis_result']['style']
        bg_colors = bg_analysis['analysis_result']['colors']

        return AIInteriorResponse(
            success=True,
            circle_info={
                'center_x': center_x,
                'center_y': center_y,
                'radius': radius,
                'category': gemini_result['category'],
                'confidence': gemini_result['confidence'],
                'description': gemini_result['description'],
                'gemini_recommendations': gemini_result['recommendations'],
                'placement_surface': gemini_result.get('placement_surface', 'floor')
            },
            background_mood={
                'primary_style': bg_style['primary_keyword'],
                'category': bg_style['category'],
                'confidence': bg_style['primary_score'],
                'warmth_score': bg_colors['warmth_score'],
                'dominant_colors': bg_colors['dominant_hex'][:3]
            },
            recommended_products=recommended_products_with_simulation,
            message=f"처리 완료 ({len(recommended_products_with_simulation)}개 상품 추천, {processing_time:.0f}ms)"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI Interior API Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI 모델 처리 중 오류가 발생했습니다: {str(e)}")


