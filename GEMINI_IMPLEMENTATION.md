# Gemini Nano Banana 이미지 합성 구현

## 구현 완료 ✅

### 1. 기능 개요
- **Mock 시뮬레이션 제거**: 기존의 초록색 원과 텍스트를 그리는 Mock 방식 제거
- **실제 AI 이미지 생성**: Gemini 2.5 Flash Image 모델을 사용한 실제 상품 합성 이미지 생성
- **지능형 영역 분석**: Gemini 2.0 Flash Exp 모델로 영역 분석 (가구/소품 판단)

### 2. 사용된 Gemini 모델

#### A. 영역 분석 (Region Analysis)
- **모델**: `gemini-2.0-flash-exp`
- **용도**: 동그라미 영역 분석 → 가구/소품 판단
- **출력**: 카테고리, 확신도, 설명, 추천 아이템
- **예시**:
  ```json
  {
    "category": "furniture",
    "confidence": 0.90,
    "description": "침대 옆 공간으로, 협탁, 램프, 수납장이 들어가면 실용적입니다.",
    "recommendations": ["원목 협탁", "단스탠드", "라탄 수납 바구니"]
  }
  ```

#### B. 이미지 생성/편집 (Image Generation)
- **모델**: `gemini-2.5-flash-image` (Nano Banana)
- **용도**: 상품을 배경에 합성한 시뮬레이션 이미지 생성
- **입력**:
  - 배경 이미지 (504x381px)
  - 프롬프트 (상품명, 위치 좌표, 합성 지침)
- **출력**:
  - 고해상도 이미지 (1152x896px)
  - Base64 인코딩
  - 평균 1.2MB (PNG)

### 3. 구현 상세

#### 파일 수정
1. **`app/api/routes/ai_interior.py`**
   - `_simulate_product_in_room()` 함수 완전 재작성
   - Gemini API 통합 (google.genai 패키지)
   - 좌표 기반 위치 설명 생성
   - 프롬프트 최적화

2. **`app/core/gemini_analyzer.py`**
   - 구 `google.generativeai` 패키지에서 신규 `google.genai`로 마이그레이션
   - 모델 업그레이드: `gemini-pro-vision` → `gemini-2.0-flash-exp`

#### 새 패키지 설치
```bash
pip3 install google-genai
```

### 4. 프롬프트 전략

#### 초기 시도 (실패)
❌ 빨간 원으로 위치 표시 → Gemini가 완전히 새로운 이미지 생성

#### 최종 방식 (개선)
✅ 깨끗한 배경 + 상대 좌표 텍스트 설명
- 위치: "left side, top" 등의 자연어 설명
- 정확한 좌표: "22.2% from left, 39.4% from top"
- 크기: "23.1% of image width"
- 강조: "PRESERVE EVERYTHING", "ONLY ADD ONE ITEM"

### 5. 실제 테스트 결과

#### 입력
- 이미지: `test_image.png` (504x381px)
- 좌표: `x=0.2216, y=0.6070, radius=0.2306`
- 위치: 좌측 상단 (침대 영역)

#### 출력
- ✅ 2개 상품 추천 (가구 카테고리)
- ✅ 시뮬레이션 이미지 2개 생성
- ✅ 각 이미지: 1152x896px, ~1.2MB
- ✅ 처리 시간: ~24초 (Gemini API 호출 포함)

#### 생성된 이미지 품질
- 고해상도 (1152x896px, 원본의 2.3배)
- 사실적인 인테리어 렌더링
- 상품이 자연스럽게 배치됨
- 조명/그림자/원근감 자동 적용

### 6. 현재 동작 방식

#### 이미지 합성 방식
Gemini는 **정확한 픽셀 단위 합성(compositing)**이 아닌, **의미론적 재구성(semantic reconstruction)**을 수행합니다:

1. 원본 이미지의 레이아웃/스타일/분위기를 이해
2. 지정된 위치에 요청된 상품을 배치
3. 전체 장면을 일관성 있게 재생성
4. 조명/그림자/원근감을 자동으로 조정

**결과**:
- ✅ 매우 사실적인 인테리어 시뮬레이션
- ✅ 상품이 자연스럽게 통합됨
- ⚠️ 원본의 픽셀이 100% 보존되지는 않음 (유사한 장면으로 재생성)

#### Mock vs Gemini 비교

| 항목 | Mock (기존) | Gemini (현재) |
|------|-------------|---------------|
| 이미지 크기 | 504x381px | 1152x896px |
| 파일 크기 | 100-200KB | 1200KB |
| 상품 표현 | 초록색 원 + 텍스트 | 실제 상품 렌더링 |
| 조명/그림자 | 없음 | 자동 생성 |
| 원근감 | 없음 | 자동 적용 |
| 현실감 | 매우 낮음 | 매우 높음 |

### 7. API 응답 예시

```json
{
  "success": true,
  "message": "처리 완료 (2개 상품 추천, 23683ms)",
  "circle_info": {
    "center_x": 112,
    "center_y": 150,
    "radius": 116,
    "category": "furniture",
    "confidence": 0.90,
    "description": "침대 옆 공간으로, 협탁, 램프, 수납장이 들어가면 실용적이고 아늑한 분위기를 연출할 수 있습니다.",
    "gemini_recommendations": ["원목 협탁", "단스탠드", "라탄 수납 바구니"]
  },
  "background_mood": {
    "primary_style": "white_wood",
    "category": "Natural & Cozy",
    "confidence": 0.5981,
    "warmth_score": 0.51,
    "dominant_colors": ["#d8d2d3", "#beb1ae"]
  },
  "recommended_products": [
    {
      "product_id": "furn_002",
      "name": "화이트 옷장 (3도어)",
      "category": "furniture",
      "price": 680000,
      "match_score": 0.9565,
      "simulated_image_base64": "iVBORw0KGgoAAAANS..."
    }
  ]
}
```

### 8. 성능 및 비용

#### 처리 시간
- 영역 분석: ~1-2초
- 이미지 생성 (상품 1개): ~10-12초
- 전체 (3개 상품): ~25-35초

#### API 사용량
- Request당 Gemini API 호출: 1 + N (N = 추천 상품 개수)
  - 영역 분석: 1회 (gemini-2.0-flash-exp)
  - 이미지 생성: N회 (gemini-2.5-flash-image)

#### 비용 고려사항
- `gemini-2.5-flash-image`는 이미지 생성 모델로 비용이 높을 수 있음
- 프로덕션 환경에서는 생성 개수 제한 고려 (현재 3-5개)

### 9. 환경 변수

```bash
export GEMINI_API_KEY="AIzaSyAsLpRBd6H8g0HuF2k_jaUUQQR5YMnGqAU"
```

서버 시작:
```bash
./start_server_with_gemini.sh
```

### 10. Fallback 동작

Gemini API가 실패하거나 API 키가 없는 경우:
- ✅ 자동으로 Mock 시뮬레이션으로 전환
- ✅ 에러 없이 계속 동작
- ⚠️ 콘솔에 경고 메시지 출력

### 11. 테스트 방법

```bash
# 1. 서버 시작
./start_server_with_gemini.sh

# 2. 테스트 실행
python3 test_custom_coordinates.py

# 3. 결과 확인
ls -lh custom_simulated_*.png
```

### 12. 향후 개선 가능사항

1. **더 정교한 합성**:
   - 전통적인 CV 기법과 결합 (perspective transform, alpha blending)
   - 상품 이미지 DB 구축 후 직접 합성

2. **캐싱**:
   - 동일 이미지/위치/상품 조합은 캐싱하여 비용 절감

3. **Gemini 3 Pro Image**:
   - 더 정교한 편집 기능 제공 (현재 preview 단계)
   - "thinking" 프로세스로 더 나은 결과

4. **배치 처리**:
   - 여러 상품을 한 번의 API 호출로 생성

5. **해상도 옵션**:
   - 1K/2K/4K 옵션 제공 (현재 기본값 사용)

---

## 결론

✅ **Gemini Nano Banana 통합 완료**
- Mock 시뮬레이션 → 실제 AI 이미지 생성
- 초록색 원 + 텍스트 → 사실적인 상품 렌더링
- 저해상도(504x381) → 고해상도(1152x896)
- 즉각 완료 → 25-35초 처리 시간 (AI 생성)

🎨 **품질 향상**
- 매우 사실적인 인테리어 시뮬레이션
- 자동 조명/그림자/원근감 적용
- 상품이 공간에 자연스럽게 통합

💡 **주의사항**
- 원본 이미지가 100% 보존되지는 않음 (유사한 장면으로 재생성)
- 처리 시간이 길어짐 (Mock: <100ms, Gemini: ~25초)
- API 비용 발생 (상품당 1회 호출)
