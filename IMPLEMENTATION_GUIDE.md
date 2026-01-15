# removed_background_image_base64 기반 Clustering DB 구현 가이드

## 전체 시스템 플로우 요약

```
[Phase 1: 상품 DB 구축]
JSON {removed_background_image_base64}
  ↓ Base64 → OpenCV Image (image_utils.py)
  ↓ Prop Analyzer (analyzer.py)
  ↓ Mood Vector 생성 (vector_manager.py)
  ↓ PostgreSQL + pgvector 저장
  ↓ K-Means Clustering (clustering.py)
  ↓ cluster_id 할당
[상품 무드 DB 완성]

[Phase 2: 실시간 추천]
배경 이미지 입력
  ↓ Background Analyzer
  ↓ Mood Vector 생성
  ↓ Vector DB 유사도 검색 (Cosine Similarity)
  ↓ Clustering 기반 빠른 검색
  ↓ Top-K 상품 선택
[추천 상품 리스트 반환]
```

---

## 구현 완료 항목

### ✅ 1. Core 모듈
- **app/core/image_utils.py**: Base64 ↔ OpenCV Image 변환
- **app/core/vector_manager.py**: Mood Vector 생성 및 유사도 계산 (20차원)
- **app/core/clustering.py**: K-Means Clustering 및 Cluster 관리

### ✅ 2. API 엔드포인트
- **POST /api/v1/products/analyze**: 단일 상품 무드 분석
- **POST /api/v1/products/batch-analyze**: 배치 상품 분석 (최대 100개)
- **POST /api/v1/analyze/background**: 배경 무드 분석
- **POST /api/v1/match/recommend**: 배경 기반 상품 추천 (핵심 기능)
- **POST /api/v1/admin/rebuild-clusters**: 클러스터 재생성
- **GET /api/v1/admin/cluster-stats**: 클러스터 통계 조회

### ✅ 3. 데이터 스키마
- **app/models/schemas.py**: 모든 Request/Response Pydantic 스키마 정의

### ✅ 4. 기존 분석 모듈 (1-3단계)
- Background/Prop Processor
- Color/Shape/Texture/Style Extractor
- 통합 Analyzer

---

## Mood Vector 구조 (20차원)

```python
mood_vector = [
    # Color Features (3차원)
    warmth_score,          # [0] 0.0=Cool ~ 1.0=Warm
    dominant_h,            # [1] HSV의 H (0~1)
    dominant_s,            # [2] HSV의 S (0~1)

    # Physics Features (3차원)
    linearity/circularity, # [3] Background: linearity, Prop: circularity
    glossiness,            # [4] 0.0=Matte ~ 1.0=Glossy
    complexity,            # [5] 0.0=Simple ~ 1.0=Complex

    # Style Features (14차원)
    [6] natural_wood,
    [7] white_wood,
    [8] japandi,
    [9] cozy,
    [10] modern,
    [11] minimalism,
    [12] mid_century_modern,
    [13] industrial,
    [14] classic,
    [15] modern_french,
    [16] hotel_luxury,
    [17] vintage,
    [18] pop_art,
    [19] planterior
]
```

---

## 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. FastAPI 서버 실행
```bash
python app/main.py

# 또는
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. API 테스트
```bash
# 헬스체크
curl http://localhost:8000/health

# Swagger UI 접속
open http://localhost:8000/docs
```

### 4. Python으로 테스트
```bash
# test_api.py 수정 후 실행
python test_api.py
```

---

## 사용 예시

### 1. 상품 무드 분석 (removed_background_image_base64)

```python
import requests
import base64

# 이미지를 Base64로 변환
with open('product_image.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# API 호출
response = requests.post(
    'http://localhost:8000/api/v1/products/analyze',
    json={
        "product_id": "prod_001",
        "name": "우드 원형 테이블",
        "category": "furniture",
        "removed_bg_image_base64": image_base64
    }
)

result = response.json()
print(f"Mood Vector: {result['mood_vector']}")
print(f"Primary Style: {result['mood_analysis']['style']['primary_keyword']}")
```

### 2. 배경 기반 상품 추천

```python
# 배경 이미지를 Base64로 변환
with open('room_image.jpg', 'rb') as f:
    bg_image_base64 = base64.b64encode(f.read()).decode('utf-8')

# 추천 API 호출
response = requests.post(
    'http://localhost:8000/api/v1/match/recommend',
    json={
        "background_image_base64": bg_image_base64,
        "top_k": 10,
        "filters": {
            "categories": ["furniture", "decor"],
            "min_score": 0.7
        },
        "matching_strategy": "weighted"
    }
)

result = response.json()

# 배경 무드 확인
print(f"Background Style: {result['background_mood']['style']['primary_keyword']}")

# 추천 상품 확인
for product in result['recommended_products']:
    print(f"\n{product['name']}")
    print(f"  Match Score: {product['match_score']:.2f}")
    print(f"  Color Similarity: {product['match_details']['color_similarity']:.2f}")
    print(f"  Style Similarity: {product['match_details']['style_similarity']:.2f}")
```

### 3. 배치 처리 (여러 상품 한 번에)

```python
products = []
for i in range(10):
    with open(f'product_{i}.jpg', 'rb') as f:
        products.append({
            "product_id": f"prod_{i:03d}",
            "name": f"상품 {i}",
            "category": "furniture",
            "removed_bg_image_base64": base64.b64encode(f.read()).decode('utf-8')
        })

response = requests.post(
    'http://localhost:8000/api/v1/products/batch-analyze',
    json={"products": products}
)

result = response.json()
print(f"Success: {result['success_count']}/{result['total_count']}")
```

---

## 다음 구현 단계

### 🔴 필수 (현재 TODO)

1. **데이터베이스 연동**
   - PostgreSQL + pgvector Extension 설치
   - `products` 테이블 생성 (API_SPECIFICATION.md 참고)
   - CRUD 함수 작성 (`app/database.py`)

2. **Clustering 통합**
   - 상품 분석 후 자동 Clustering
   - Cluster 기반 빠른 검색 구현
   - Cluster 모델 저장/로드 (`models/kmeans_cluster.pkl`)

3. **추천 API 완성**
   - Mock 데이터 제거
   - 실제 DB 검색 연동
   - Filter 로직 DB 쿼리로 변경

### 🟡 중요 (향후 개선)

4. **성능 최적화**
   - Redis 캐싱 (자주 조회되는 상품)
   - Celery + Redis Queue (배치 처리)
   - Image 리사이징 (처리 속도 향상)

5. **고급 기능**
   - A/B 테스트 (가중치 조정)
   - 사용자 피드백 기반 재학습
   - 실시간 클러스터 업데이트

### 🟢 추가 기능

6. **배포 및 모니터링**
   - Docker 컨테이너화
   - Kubernetes 배포
   - Logging & Monitoring (Prometheus, Grafana)

---

## PostgreSQL + pgvector 설치

### macOS
```bash
# PostgreSQL 설치
brew install postgresql

# pgvector Extension 설치
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install

# PostgreSQL 시작
brew services start postgresql
```

### Docker (권장)
```bash
# pgvector가 포함된 PostgreSQL 이미지 실행
docker run -d \
  --name mood-matching-db \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=mood_matching \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### 테이블 생성
```sql
-- Extension 활성화
CREATE EXTENSION vector;

-- products 테이블 생성
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    category VARCHAR(100),
    price INTEGER,
    image_url TEXT,
    removed_bg_image_base64 TEXT,

    -- Mood Vector (pgvector)
    mood_vector VECTOR(20),

    -- Color Features
    dominant_hex_1 VARCHAR(7),
    dominant_hex_2 VARCHAR(7),
    warmth_score FLOAT,

    -- Physics Features
    circularity FLOAT,
    glossiness FLOAT,
    complexity FLOAT,

    -- Style Features
    primary_keyword VARCHAR(50),
    primary_score FLOAT,
    category_style VARCHAR(50),
    style_vector JSONB,

    -- Clustering
    cluster_id INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector 유사도 검색 인덱스
CREATE INDEX ON products USING ivfflat (mood_vector vector_cosine_ops)
WITH (lists = 100);

-- 일반 인덱스
CREATE INDEX idx_cluster_id ON products(cluster_id);
CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_primary_keyword ON products(primary_keyword);
```

---

## 유사도 검색 예시 (PostgreSQL)

```sql
-- 특정 mood_vector와 가장 유사한 상품 10개 찾기
SELECT
    product_id,
    name,
    category,
    1 - (mood_vector <=> '[0.72, 0.58, 0.45, ...]') AS similarity
FROM products
WHERE cluster_id = 3  -- Cluster 필터링으로 성능 향상
ORDER BY mood_vector <=> '[0.72, 0.58, 0.45, ...]'
LIMIT 10;
```

---

## 프로젝트 구조 (최종)

```
kakao_homes_back/
├── app/
│   ├── main.py                        # FastAPI 앱
│   ├── analyzer.py                    # 통합 분석기
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── analyze.py             # 분석 API
│   │       ├── recommend.py           # 추천 API
│   │       └── admin.py               # 관리 API
│   │
│   ├── core/
│   │   ├── image_utils.py             # Base64 변환
│   │   ├── vector_manager.py          # Vector 생성/유사도 계산
│   │   └── clustering.py              # K-Means Clustering
│   │
│   ├── models/
│   │   └── schemas.py                 # Pydantic 스키마
│   │
│   └── services/
│       ├── preprocessors/             # 전처리
│       │   ├── background_processor.py
│       │   └── prop_processor.py
│       └── extractors/                # 특징 추출
│           ├── color_extractor.py
│           ├── shape_extractor.py
│           ├── texture_extractor.py
│           └── style_extractor.py
│
├── requirements.txt
├── test_api.py                        # API 테스트
├── readme.md                          # 프로젝트 명세
├── API_SPECIFICATION.md               # API 상세 명세
├── DEVELOPMENT.md                     # 개발 가이드
└── IMPLEMENTATION_GUIDE.md            # 이 파일
```

---

## FAQ

### Q1: removed_background_image_base64가 이미 누끼 제거된 이미지인가요?
**A**: 네, 이미 배경이 제거된 상태입니다. `PropProcessor`의 `remove()` 함수는 추가로 실행할 필요가 없을 수 있습니다. 하지만 안전하게 한 번 더 처리해도 무방합니다.

### Q2: 상품이 10만개 이상이면 어떻게 하나요?
**A**: pgvector 대신 **Faiss** 또는 **Milvus**를 사용하세요. 대규모 벡터 검색에 최적화되어 있습니다.

### Q3: Clustering은 언제 다시 실행하나요?
**A**:
- 상품이 대량으로 추가/삭제될 때
- 추천 품질이 떨어질 때
- 주기적으로 (예: 매주 1회)

### Q4: 가중치는 어떻게 조정하나요?
**A**: `vector_manager.py`의 `weights` 딕셔너리를 수정하세요. A/B 테스트를 통해 최적값을 찾으세요.

---

## 참고 문서

- **readme.md**: 프로젝트 전체 명세
- **API_SPECIFICATION.md**: API 상세 명세 및 DB 설계
- **DEVELOPMENT.md**: 1-3단계 개발 가이드
- **test_api.py**: API 사용 예시

---

## 문의

구현 중 문제가 발생하면:
1. Swagger UI 확인: http://localhost:8000/docs
2. 로그 확인: 터미널 출력
3. DB 연결 상태 확인
4. Style Prompts 작성 여부 확인

**핵심**: `removed_background_image_base64` → `base64_to_opencv()` → `analyzer.analyze()` → `vector_manager.create_mood_vector()` → DB 저장 → Clustering → 유사도 검색
