# 개발 가이드

## 프로젝트 구조

```
kakao_homes_back/
├── app/
│   ├── __init__.py
│   ├── analyzer.py                    # 통합 분석기 (MoodAnalyzer)
│   ├── api/                           # FastAPI 라우트 (향후 구현)
│   │   ├── __init__.py
│   │   └── routes/
│   │       └── __init__.py
│   ├── core/                          # 설정 및 코어 모듈 (향후 구현)
│   │   └── __init__.py
│   ├── models/                        # Pydantic 스키마 (향후 구현)
│   │   └── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── preprocessors/             # 전처리 모듈
│       │   ├── __init__.py
│       │   ├── background_processor.py    # 배경 Semantic Segmentation
│       │   └── prop_processor.py          # 소품 Background Removal
│       └── extractors/                # 특징 추출 모듈
│           ├── __init__.py
│           ├── color_extractor.py         # Color Vector 추출
│           ├── shape_extractor.py         # Shape/Geometry Vector 추출
│           ├── texture_extractor.py       # Texture Vector 추출
│           └── style_extractor.py         # Style Vector 추출 (CLIP)
├── requirements.txt                   # 의존성 라이브러리
├── .gitignore
├── example_usage.py                   # 사용 예제
├── readme.md                          # 프로젝트 명세서
└── DEVELOPMENT.md                     # 이 파일
```

---

## 현재 구현 상태 (1-3단계 완료)

### ✅ 1단계: 환경 설정 및 의존성 설치
- `requirements.txt` 생성 완료
- FastAPI, OpenCV, scikit-learn, PyTorch, CLIP 등 포함

### ✅ 2단계: 전처리 파이프라인 구축
- **BackgroundProcessor**: Semantic Segmentation (벽/바닥 분리)
  - 현재: 간단한 수평 분할로 placeholder 구현
  - TODO: DeepLabV3, U-Net 등 실제 모델 통합
- **PropProcessor**: Background Removal (누끼 제거)
  - `rembg` 라이브러리 사용하여 완전 구현

### ✅ 3단계: 4가지 축 Feature Extraction 모듈 개발

#### ① Color Vector (color_extractor.py)
- K-Means Clustering으로 주조색 5개 추출
- Lab 색공간 기반 Warm/Cool Score 계산
- Output: 주조색 HEX 코드, Warmth Score

#### ② Shape/Geometry Vector (shape_extractor.py)
- **Background**: Hough Line Transform으로 Linearity 계산
- **Prop**: Contour 기반 Circularity 계산
- Output: Linearity/Circularity Score

#### ③ Texture Vector (texture_extractor.py)
- Canny Edge Detection으로 Edge Density 계산
- Laplacian Variance로 선명도/거칠기 측정
- 밝기 히스토그램으로 Glossiness 계산
- Output: Complexity Score, Glossiness Score

#### ④ Style Vector (style_extractor.py)
- CLIP 모델 (ViT-B/32) 사용
- 14개 스타일 키워드와 이미지의 유사도 계산
- **⚠️ TODO**: `STYLE_PROMPTS` 딕셔너리에 14개 프롬프트 작성 필요

---

## 설치 및 실행

### 1. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

**참고**: CLIP 설치 시 시간이 걸릴 수 있습니다.

### 3. Style Prompts 작성
`app/services/extractors/style_extractor.py` 파일을 열고 `STYLE_PROMPTS` 딕셔너리를 작성하세요.

```python
STYLE_PROMPTS = {
    "natural_wood": "An interior with bright wood tones, plants, and natural materials...",
    "white_wood": "Clean white wallpaper with wood furniture points...",
    # ... 나머지 12개 작성
}
```

readme.md의 [Defined Style Dictionary] 섹션을 참고하세요.

### 4. 테스트 실행
```python
from app.analyzer import MoodAnalyzer
import cv2

# Analyzer 초기화
analyzer = MoodAnalyzer()

# 이미지 분석
image = cv2.imread("your_image.jpg")
result = analyzer.analyze(image, image_type='background', image_id='test_001')

print(result)
```

또는 `example_usage.py`를 수정하여 실행하세요.

---

## 다음 단계 (4단계 이후)

### 4단계: 통합 분석 API 개발 (FastAPI)
- `app/api/routes/analyze.py` 구현
- 이미지 업로드 엔드포인트 생성
- Pydantic 스키마 정의 (`app/models/schemas.py`)

### 5단계: 매칭 알고리즘 구현
- Background와 Prop 간 유사도 계산
- 4개 축 가중치 기반 매칭 점수 산출

### 6단계: 테스트 및 최적화
- 14가지 스타일별 정확도 검증
- CLIP 프롬프트 튜닝
- 성능 최적화

### 7단계: API 서버 구축
- FastAPI 앱 완성 (`app/main.py`)
- 엔드포인트 구현

### 8단계: 배포
- Docker 컨테이너화
- 클라우드 배포

---

## 주요 TODO 리스트

### 긴급 (필수)
- [ ] `style_extractor.py`의 `STYLE_PROMPTS` 작성
- [ ] `background_processor.py`에 실제 Semantic Segmentation 모델 통합

### 중요
- [ ] FastAPI 메인 앱 구현 (`app/main.py`)
- [ ] API 엔드포인트 구현 (`app/api/routes/analyze.py`)
- [ ] Pydantic 스키마 정의 (`app/models/schemas.py`)
- [ ] 설정 파일 구현 (`app/core/config.py`)

### 향후
- [ ] 매칭 알고리즘 구현
- [ ] 테스트 코드 작성
- [ ] Docker 설정

---

## 참고사항

### CLIP 모델 다운로드
첫 실행 시 CLIP 모델이 자동으로 다운로드됩니다 (~350MB).
기본 위치: `~/.cache/clip/`

### GPU 사용
CUDA가 설치된 GPU가 있으면 자동으로 사용됩니다.
CPU만 사용하려면:
```python
analyzer = MoodAnalyzer(device='cpu')
```

### 디버깅
각 모듈은 독립적으로 테스트 가능합니다:
```python
from app.services.extractors.color_extractor import ColorExtractor
import cv2

extractor = ColorExtractor()
image = cv2.imread("test.jpg")
result = extractor.extract(image)
print(result)
```
