"""
Gemini API를 사용한 영역 분석 모듈
해당 영역에 가구/소품 판단
"""
import os
import cv2
import numpy as np
from typing import Dict, Optional
import base64
from PIL import Image
import io


class GeminiAnalyzer:
    """
    Gemini API를 사용한 영역 분석 클래스
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (None이면 환경 변수에서 로드)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            print("⚠️  GEMINI_API_KEY not found. Gemini analysis will be mocked.")
            self.enabled = False
            self.client = None
        else:
            try:
                from google import genai
                # 새로운 google.genai 패키지 사용
                self.client = genai.Client(api_key=self.api_key)
                self.enabled = True
                print("✅ Gemini API initialized (gemini-2.0-flash-exp)")
            except ImportError:
                print("⚠️  google.genai 패키지 없음. pip install google-genai")
                self.enabled = False
                self.client = None
            except Exception as e:
                print(f"⚠️  Gemini API initialization failed: {e}")
                self.enabled = False
                self.client = None

    def analyze_region(self, region_image: np.ndarray) -> Dict:
        """
        영역 이미지를 분석하여 가구/소품 판단

        Args:
            region_image: 분석할 영역 이미지 (OpenCV BGR)

        Returns:
            {
                'category': 'furniture' or 'prop',
                'confidence': 0.0~1.0,
                'description': '설명',
                'recommendations': ['추천 아이템 1', '추천 아이템 2']
            }
        """
        if not self.enabled or not self.client:
            return self._mock_analysis(region_image)

        try:
            # OpenCV BGR → RGB PIL Image 변환
            region_rgb = cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(region_rgb)

            # 프롬프트 작성
            prompt = """
이미지를 분석하고 다음 질문에 JSON 형식으로 답변해주세요:

1. 이 영역에 어떤 가구 또는 소품이 들어가면 좋을까요?
2. 이것은 '가구(furniture)' 카테고리인가요, 아니면 '인테리어 소품(prop)' 카테고리인가요?
3. 확신도는 얼마나 되나요? (0.0~1.0)
4. 이 공간에 어울리는 구체적인 아이템 3개를 추천해주세요.
5. **중요**: 이 영역의 표면 유형은 무엇인가요? 정확히 분석해주세요:
   - "wall": 벽면 (그림, 시계, 스위치, 벽걸이 선반 등이 부착되는 수직면)
   - "floor": 바닥 (책장, 테이블, 의자, 화분 등이 놓이는 수평면)
   - "ceiling": 천장 (조명, 선풍기 등이 부착되는 상부 수평면)
   - "furniture_surface": 가구 표면 (테이블 위, 선반 위 등 기존 가구 위)

   판단 기준:
   - 벽면: 벽의 질감, 벽지, 페인트가 보이는 수직 공간
   - 바닥: 바닥재(나무, 타일 등)가 보이거나 바닥에 가구를 놓을 수 있는 공간
   - 가구 표면: 이미 책상, 선반, 수납장 등 가구가 있고 그 위에 소품을 올릴 수 있는 공간

응답 형식:
{
  "category": "furniture" or "prop",
  "confidence": 0.85,
  "description": "침대 옆 공간으로, 사이드 테이블이나 스탠드 조명이 적합합니다.",
  "recommendations": ["우드 사이드 테이블", "미니멀 스탠드 조명", "작은 화분"],
  "placement_surface": "floor" or "wall" or "ceiling" or "furniture_surface"
}
"""

            # 새로운 Gemini API 호출 (gemini-2.0-flash-exp)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt, pil_image]
            )

            # JSON 파싱
            import json
            response_text = response.text.strip()

            # ```json ... ``` 제거
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()

            result = json.loads(response_text)

            return result

        except Exception as e:
            print(f"Gemini analysis error: {e}")
            import traceback
            traceback.print_exc()
            return self._mock_analysis(region_image)

    def _mock_analysis(self, region_image: np.ndarray) -> Dict:
        """
        Gemini API가 없을 때 Mock 분석 결과 반환
        """
        # 이미지 크기 기반 간단한 휴리스틱
        height, width = region_image.shape[:2]
        area = height * width
        aspect_ratio = width / height if height > 0 else 1.0

        # placement_surface 판단 (세로로 긴 영역은 벽일 가능성)
        if aspect_ratio < 0.8:  # 세로로 긴 영역
            placement_surface = "wall"
        else:
            placement_surface = "floor"

        # 큰 영역이면 가구, 작은 영역이면 소품으로 판단
        if area > 100000:  # 대략 300x300 이상
            category = "furniture"
            description = "이 영역은 큰 가구가 들어갈 공간으로 보입니다."
            recommendations = ["침대", "소파", "옷장", "책상"]
        else:
            category = "prop"
            description = "이 영역은 소품이나 작은 가구가 들어갈 공간입니다."
            recommendations = ["사이드 테이블", "스탠드 조명", "화분", "쿠션"]

        return {
            'category': category,
            'confidence': 0.75,
            'description': description,
            'recommendations': recommendations[:3],
            'placement_surface': placement_surface
        }
