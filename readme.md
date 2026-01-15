# Kakao Homes - 인테리어 AI 무드 매칭 시스템

> AI 기반 인테리어 공간 분석 및 맞춤형 가구/소품 추천 시스템

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://www.docker.com)

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [프로젝트 구조](#-프로젝트-구조)
- [빠른 시작](#-빠른-시작)
- [API 엔드포인트](#-api-엔드포인트)
- [환경 변수 설정](#-환경-변수-설정)
- [개발 가이드](#-개발-가이드)
- [문서](#-문서)

## 🎯 프로젝트 개요

Kakao Homes는 사용자가 업로드한 인테리어 공간 이미지를 AI로 분석하여, 해당 공간의 무드(Color, Shape, Texture, Style)를 추출하고, 가장 잘 어울리는 가구와 소품을 추천하는 시스템입니다.

### 핵심 가치

- **AI 기반 무드 분석**: Google Gemini API와 CLIP 모델을 활용한 정교한 스타일 분석
- **4가지 무드 축**: Color, Shape, Texture, Style을 기반으로 한 다차원 분석
- **14가지 스타일 분류**: Natural Wood, White Wood, Japandi, Modern, Minimalism 등
- **실시간 추천**: Vector DB 기반 빠른 유사도 검색
- **AI 인테리어 시뮬레이션**: 사진 위에 가구를 자연스럽게 배치한 시뮬레이션 이미지 생성

## ✨ 주요 기능

### 1. 공간 이미지 분석
- 배경(벽/바닥) 세그멘테이션 및 색상 분석
- 라인 패턴 및 질감 추출
- CLIP 기반 스타일 분류

### 2. 상품 무드 DB 구축
- 배경 제거 (rembg)
- 다차원 무드 벡터 생성 및 저장
- K-Means 클러스터링을 통한 상품 그룹화

### 3. 맞춤형 추천
- Vector DB 코사인 유사도 검색
- 카테고리별 필터링 지원
- 실시간 추천 API

### 4. AI 인테리어 시뮬레이션
- Gemini Vision API를 활용한 가구 배치 좌표 자동 추천
- OpenCV를 활용한 가구 이미지 합성
- 자연스러운 원근감과 크기 조절

### 5. 스마트 추천
- 사용자 선호도 기반 추천
- 무드 벡터와 위시리스트 데이터 결합
- 실시간 개인화 추천

## 🛠 기술 스택

### Backend Framework
- **FastAPI** - 고성능 비동기 웹 프레임워크
- **Python 3.10+** - 최신 파이썬 기능 활용
- **Uvicorn** - ASGI 서버

### AI & Machine Learning
- **Google Gemini API** - 이미지 분석 및 생성형 AI
- **CLIP (OpenAI)** - 스타일 분류
- **PyTorch** - 딥러닝 모델
- **scikit-learn** - K-Means, 코사인 유사도
- **OpenCV** - 이미지 처리 및 합성
- **rembg** - 배경 제거

### Database & Cache
- **PostgreSQL** - 메인 데이터베이스
- **pgvector** - Vector 유사도 검색
- **Redis** - 캐싱 및 세션 관리

### DevOps
- **Docker & Docker Compose** - 컨테이너화
- **pytest** - 테스트 프레임워크

## 📁 프로젝트 구조

```
kakao_homes_back/
├── app/
│   ├── main.py                    # FastAPI 애플리케이션 엔트리포인트
│   ├── analyzer.py                # 메인 무드 분석기
│   ├── database.py                # DB 연결 설정
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── analyze.py         # 상품 분석 API
│   │       ├── recommend.py       # 무드 기반 추천 API
│   │       ├── smart_recommend.py # 스마트 추천 API
│   │       ├── ai_interior.py     # AI 인테리어 시뮬레이션 API
│   │       └── admin.py           # 관리자 API
│   │
│   ├── core/
│   │   ├── config.py              # 환경 설정
│   │   ├── vector_manager.py      # Vector DB 관리
│   │   ├── image_utils.py         # 이미지 처리 유틸
│   │   ├── clustering.py          # K-Means 클러스터링
│   │   ├── gemini_analyzer.py     # Gemini API 연동
│   │   ├── circle_detector.py     # 원형 마커 감지
│   │   ├── product_loader.py      # 상품 데이터 로더
│   │   └── cache.py               # Redis 캐시
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic 모델
│   │
│   └── services/
│       ├── preprocessors/
│       │   ├── background_processor.py  # 배경 분석
│       │   └── prop_processor.py        # 상품 분석
│       │
│       └── extractors/
│           ├── color_extractor.py       # 색상 추출
│           ├── shape_extractor.py       # 형태 추출
│           ├── texture_extractor.py     # 질감 추출
│           └── style_extractor.py       # 스타일 분류
│
├── scripts/
│   ├── init_db.py                 # DB 초기화
│   ├── load_product_data.py       # 상품 데이터 로드
│   └── add_mood_to_json.py        # 무드 데이터 추가
│
├── tests/
│   ├── test_api.py                # API 테스트
│   ├── test_extractors.py         # Feature Extractor 테스트
│   └── test_vector_manager.py     # Vector DB 테스트
│
├── docker-compose.yml             # Docker 구성
├── Dockerfile                     # Docker 이미지
├── requirements.txt               # Python 의존성
├── .env.example                   # 환경 변수 예시
│
└── docs/
    ├── API_SPECIFICATION.md       # API 상세 명세
    ├── IMPLEMENTATION_GUIDE.md    # 구현 가이드
    ├── QUICKSTART.md              # 빠른 시작 가이드
    ├── DEVELOPMENT.md             # 개발 가이드
    ├── FRONTEND_GUIDE.md          # 프론트엔드 연동 가이드
    ├── GEMINI_IMPLEMENTATION.md   # Gemini API 구현 가이드
    └── REAL_DATA_INTEGRATION.md   # 실제 데이터 연동 가이드
```

## 🚀 빠른 시작

### Docker로 실행 (권장)

```bash
# 1. 저장소 클론
git clone <repository-url>
cd kakao_homes_back

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 설정 (특히 GEMINI_API_KEY)

# 3. Docker Compose로 모든 서비스 실행
docker-compose up -d

# 4. 서버 확인
curl http://localhost:8000/health

# 5. Swagger UI 접속
open http://localhost:8000/docs
```

### 로컬 개발 환경

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. PostgreSQL 및 Redis 실행 (Docker)
docker run -d --name mood-matching-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=mood_matching \
  -p 5432:5432 \
  ankane/pgvector:latest

docker run -d --name mood-matching-redis \
  -p 6379:6379 redis:7-alpine

# 4. DB 초기화
python scripts/init_db.py

# 5. 서버 실행
python app/main.py
# 또는
uvicorn app.main:app --reload
```

서버가 http://localhost:8000 에서 실행됩니다!

## 📡 API 엔드포인트

### 기본

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 서비스 정보 |
| GET | `/health` | 헬스체크 |
| GET | `/docs` | Swagger UI 문서 |

### 상품 분석

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/products/analyze` | 단일 상품 무드 분석 |
| POST | `/api/v1/products/batch-analyze` | 배치 상품 분석 |

### 추천

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/recommend/by-background` | 배경 이미지 기반 추천 |
| POST | `/api/v1/recommend/by-mood-vector` | 무드 벡터 기반 추천 |
| POST | `/api/v1/smart-recommend` | 스마트 추천 (위시리스트 반영) |

### AI 인테리어

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/ai-interior/auto-detect` | 원형 마커 자동 감지 |
| POST | `/api/ai-interior/place-furniture` | 가구 배치 좌표 추천 |
| POST | `/api/ai-interior/simulate` | 시뮬레이션 이미지 생성 |

### 관리자

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/admin/rebuild-clusters` | 클러스터 재구축 |
| GET | `/api/v1/admin/stats` | 시스템 통계 |

상세한 API 명세는 [API_SPECIFICATION.md](./API_SPECIFICATION.md)를 참고하세요.

## 🔧 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 다음 변수들을 설정하세요:

```bash
# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=True

# 데이터베이스
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mood_matching
DB_USER=postgres
DB_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI 모델
GEMINI_API_KEY=your_gemini_api_key_here
CLIP_MODEL=ViT-B/32

# 추천 설정
TOP_K_RECOMMENDATIONS=10
SIMILARITY_THRESHOLD=0.7

# 캐시
CACHE_TTL=3600
ENABLE_CACHE=true
```

**중요**: `GEMINI_API_KEY`는 필수입니다. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다.

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=app --cov-report=html

# 특정 테스트만 실행
pytest tests/test_api.py -v
```

## 🔍 개발 가이드

### 새로운 Feature Extractor 추가

1. `app/services/extractors/` 디렉토리에 새 파일 생성
2. `BaseExtractor` 인터페이스 구현
3. `analyzer.py`에 통합

```python
# app/services/extractors/my_extractor.py
from typing import Dict
import numpy as np

class MyExtractor:
    def extract(self, image: np.ndarray) -> Dict:
        # 구현
        return {
            "feature_name": value
        }
```

### 새로운 API 라우트 추가

1. `app/api/routes/` 디렉토리에 새 파일 생성
2. FastAPI Router 정의
3. `app/main.py`에 라우터 등록

```python
# app/api/routes/my_route.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/my-endpoint")
async def my_endpoint():
    return {"status": "ok"}
```

```python
# app/main.py
from app.api.routes import my_route

app.include_router(my_route.router, prefix="/api/v1", tags=["My Feature"])
```

### 데이터베이스 마이그레이션

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

## 📚 문서

### 핵심 문서
- [**QUICKSTART.md**](./QUICKSTART.md) - 3분 안에 시작하기
- [**API_SPECIFICATION.md**](./API_SPECIFICATION.md) - API 상세 명세서
- [**IMPLEMENTATION_GUIDE.md**](./IMPLEMENTATION_GUIDE.md) - 구현 상세 가이드

### 추가 문서
- [**DEVELOPMENT.md**](./DEVELOPMENT.md) - 개발 환경 설정
- [**FRONTEND_GUIDE.md**](./FRONTEND_GUIDE.md) - 프론트엔드 연동
- [**GEMINI_IMPLEMENTATION.md**](./GEMINI_IMPLEMENTATION.md) - Gemini API 활용
- [**REAL_DATA_INTEGRATION.md**](./REAL_DATA_INTEGRATION.md) - 실제 데이터 연동

## 🎨 무드 분석 시스템

### 4가지 무드 축

#### 1. Color Vector (색상 및 온도)
- K-Means Clustering으로 주조색 추출
- Warm/Cool 온도 점수 계산
- 출력: `[Main_R, Main_G, Main_B, Warmth_Score]`

#### 2. Shape Vector (형태 및 라인)
- Hough Line Transform으로 직선성 측정
- Circularity로 원형도 계산
- 출력: `[Linearity_Score]`

#### 3. Texture Vector (질감 및 복잡도)
- Edge Density로 패턴 복잡도 측정
- Laplacian Variance로 거칠기 측정
- 출력: `[Complexity_Score, Glossiness_Score]`

#### 4. Style Vector (스타일 분류)
- CLIP 모델 기반 14가지 스타일 분류
- 카테고리: Natural & Cozy, Modern & Minimal, Glam & Classic, Unique & Colorful
- 출력: 14차원 확률 벡터

### 14가지 스타일 키워드

**Natural & Cozy**
- natural_wood, white_wood, japandi, cozy

**Modern & Minimal**
- modern, minimalism, mid_century_modern, industrial

**Glam & Classic**
- classic, modern_french, hotel_luxury

**Unique & Colorful**
- vintage, pop_art, planterior

## 🐛 문제 해결

### 포트 충돌
```bash
# 8000번 포트 사용 중인 프로세스 종료
lsof -ti:8000 | xargs kill -9
```

### CLIP 모델 다운로드 느림
- 첫 실행 시 약 350MB 다운로드
- 안정적인 인터넷 연결 필요
- `~/.cache/clip/` 디렉토리에 캐시됨

### PostgreSQL 연결 실패
```bash
# Docker 컨테이너 상태 확인
docker ps
docker logs mood-matching-db

# 연결 테스트
docker exec -it mood-matching-db psql -U postgres -d mood_matching
```

### Redis 연결 실패
```bash
# Redis 컨테이너 확인
docker ps | grep redis
docker logs mood-matching-redis

# Redis CLI 테스트
docker exec -it mood-matching-redis redis-cli ping
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 👥 기여

기여는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

---

**Made with ❤️ by Kakao Homes Team**
