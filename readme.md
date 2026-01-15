# 인테리어 무드 매칭 시스템 개발 명세서 v2

## 1. 프로젝트 개요
사용자가 정의한 **4개 카테고리, 14개 세부 스타일**을 기준으로 공간(Background)과 소품(Prop)의 이미지를 분석하고, 4가지 핵심 축(Color, Shape, Texture, Style)을 통해 무드 적합도를 판별하는 시스템.

### 핵심 기능
1. **배경 이미지 분석**: 인테리어 공간의 무드를 4가지 축으로 추출
2. **상품 DB 구축**: 가구/소품의 무드를 미리 분석하여 Vector DB에 저장
3. **무드 매칭**: 배경 무드와 가장 잘 맞는 상품을 추천

## 2. 전체 시스템 플로우

### Phase 1: 상품 DB 구축 (Batch Processing)
```
[상품 이미지들]
  ↓ (removed_background_image_base64)
  ↓ Background Removal (누끼 제거)
  ↓ Feature Extraction (4가지 축)
  ↓ Vector 생성
[Vector DB 저장] (PostgreSQL + pgvector / Faiss / Milvus)
  - product_id
  - mood_vector (통합 벡터)
  - colors, physics, style (개별 특징)
```

### Phase 2: 배경 무드 분석 및 매칭 (Real-time API)
```
[사용자 배경 이미지 입력]
  ↓ Semantic Segmentation (벽/바닥 분리)
  ↓ Feature Extraction (4가지 축)
  ↓ Vector 생성
  ↓ Vector DB 유사도 검색
  ↓ Top-K 상품 추천
[추천 상품 리스트 반환]
```

## 3. 시스템 파이프라인 상세

### 3-1. Background (배경) 파이프라인
* **Input:** 인테리어 공간 이미지
* **Process:** Semantic Segmentation (벽/바닥 분리) → Feature Extraction
* **Output:** Background Mood Vector

### 3-2. Prop (상품) 파이프라인
* **Input:** 가구/소품 이미지 (removed_background_image_base64)
* **Process:** Background Removal (누끼) → Feature Extraction
* **Output:** Prop Mood Vector

---

## 3. 4가지 무드 축(Feature Axes) 상세 정의

각 축은 정규화된 수치(0.0 ~ 1.0) 또는 벡터로 변환되어야 한다.

### ① Color Vector (색상 및 온도)
* **라이브러리:** `OpenCV`, `Scikit-learn (K-Means)`
* **로직:**
    1.  이미지를 RGB에서 **Lab** 또는 **HSV** 색 공간으로 변환.
    2.  **K-Means Clustering (k=5)**을 수행하여 주조색(Dominant Colors) 추출.
    3.  **Warm/Cool Score:** 픽셀의 Red/Yellow 채널 비중(Warm) vs Blue 채널 비중(Cool) 계산.
* **Output:** `[Main_R, Main_G, Main_B, Warmth_Score]`

### ② Shape/Geometry Vector (형태 및 라인)
* **라이브러리:** `OpenCV`
* **배경(Background) 로직:**
    -   **Hough Line Transform**을 사용하여 수직/수평선의 비율 계산.
    -   직선이 많을수록 `Linearity` 점수 높음 (Modern), 적을수록 낮음.
* **소품(Prop) 로직:**
    -   객체 외곽선(Contour) 추출.
    -   **Circularity (원형도)** 계산: $(4 * \pi * Area) / (Perimeter^2)$
    -   1.0에 가까울수록 원형(Soft), 낮을수록 각짐(Sharp).
* **Output:** `[Linearity_Score]` (0.0=Curved, 1.0=Straight)

### ③ Texture Vector (질감 및 복잡도)
* **라이브러리:** `OpenCV`, `skimage`
* **로직:**
    1.  이미지를 Grayscale로 변환.
    2.  **Edge Density (Canny Edge):** 엣지의 밀도를 계산하여 패턴의 복잡도 측정.
    3.  **Laplacian Variance:** 이미지의 선명도/거칠기를 측정하여 소재감 유추 (매끈함 vs 거침).
    4.  **Glossiness (광택):** 밝기 히스토그램에서 상위 5% 밝은 픽셀의 집중도 분석.
* **Output:** `[Complexity_Score, Glossiness_Score]`

### ④ Style Vector (스타일 분석 - 업데이트됨)
사용자가 정의한 14가지 세부 키워드를 CLIP 모델의 텍스트 프롬프트로 사용하여 이미지와의 유사도(Cosine Similarity)를 계산한다.

* **라이브러리:** `PyTorch`, `CLIP (OpenAI - ViT-B/32 or equivalent)`
* **Prompt Engineering:** 모델의 정확도를 높이기 위해 제공된 설명을 영문 서술형으로 변환하여 사용한다.

#### [Defined Style Dictionary]

**Category 1: Natural & Cozy (내추럴 & 편안함)**
* `natural_wood`: "An interior with bright wood tones, plants, and natural materials, stable and comfortable atmosphere."
* `white_wood`: "Clean white wallpaper with wood furniture points, Korean popular style, neat and warm."
* `japandi`: "A mix of Japanese minimalism and Scandinavian functionality, neat, clean lines, neutral tones."
* `cozy`: "Warm lighting, soft fabric textures, comfortable and snug atmosphere."

**Category 2: Modern & Minimal (모던 & 미니멀)**
* `modern`: "City-like atmosphere, black, gray, and white tones, clean and sleek."
* `minimalism`: "Aesthetics of emptiness, minimal furniture, restrained colors, simple and clutter-free."
* `mid_century_modern`: "Mid-20th century design, vivid point colors, metal and plastic materials mixed with wood."
* `industrial`: "Raw concrete, brick walls, steel furniture, rough and vintage texture."

**Category 3: Glam & Classic (화려함 & 클래식)**
* `classic`: "Traditional details, chandeliers, heavy and antique furniture, dignified style."
* `modern_french`: "Classic details reinterpreted in a modern way, elegant and romantic atmosphere, molding on walls."
* `hotel_luxury`: "Luxury mood, marble materials, indirect lighting, symmetrical structure, high-end hotel feel."

**Category 4: Unique & Colorful (개성 & 컬러풀)**
* `vintage`: "Retro props, worn-out furniture, nostalgic and cozy old-fashioned space."
* `pop_art`: "Bold colors, unique props, artistic and distinct individuality."
* `planterior`: "Space filled with many plants, fresh, green, and lively nature-inspired mood."

* **Logic:**
    1.  위의 14개 프롬프트 텍스트를 CLIP 텍스트 인코더로 벡터화.
    2.  입력 이미지(공간 or 소품)를 이미지 인코더로 벡터화.
    3.  이미지와 14개 텍스트 간의 확률값(Softmax) 계산.
    4.  상위 1순위 스타일과 그 확률(Score)을 추출.

* **Output:**
    * `style_vector`: `[0.02, 0.85, 0.10, ...]` (14개 차원)
    * `primary_style`: `"white_wood"`
    * `category`: `"Natural & Cozy"`

---

## 4. 데이터 구조 (JSON 예시 - 업데이트됨)

### Background / Prop Data Common Structure
```json
{
  "type": "background", // or "prop"
  "id": "img_1024",
  "analysis_result": {
    // 1. Color Axis
    "colors": {
      "dominant_hex": ["#FFFFFF", "#D2B48C"], // 화이트, 우드
      "warmth_score": 0.75 // (0~1) 따뜻함
    },
    
    // 2. Shape/Texture Axis
    "physics": {
      "linearity": 0.8, // (0~1) 직선적임
      "glossiness": 0.1, // (0~1) 매트함
      "complexity": 0.3  // (0~1) 단순함
    },

    // 3. Style Axis (User Defined 14 Keywords)
    "style": {
      "primary_keyword": "white_wood", // 1순위 키워드
      "primary_score": 0.82,           // 확신도
      "category": "Natural & Cozy",    // 상위 카테고리
      "vector_breakdown": {
        "white_wood": 0.82,
        "japandi": 0.10,
        "minimalism": 0.05,
        "others": 0.03
      }
    }
  }
}