# API 작동 방식 상세 명세서

## 전체 시스템 플로우

### Phase 1: 상품 DB 구축 (사전 작업 - Batch Processing)

```
[JSON 데이터: removed_background_image_base64]
  ↓
  Base64 → Image 디코딩
  ↓
  Prop Analyzer로 무드 분석 (4가지 축)
  ↓
  Mood Vector 생성 (20차원)
  ↓
  PostgreSQL + pgvector 저장
  ↓
  K-Means Clustering (상품 그룹화)
  ↓
[상품 무드 DB 완성]
```

### Phase 2: 실시간 추천 (Runtime - Real-time API)

```
[사용자: 배경 이미지 업로드]
  ↓
  Background Analyzer로 무드 분석
  ↓
  Mood Vector 생성
  ↓
  Vector DB 유사도 검색 (Cosine Similarity)
  ↓
  Top-K 상품 선택
  ↓
[추천 상품 리스트 반환]
```

---

## 1. 상품 무드 DB 구축 API

### 1.1 단일 상품 분석 및 저장

**POST /api/v1/products/analyze**

#### Request Body
```json
{
  "product_id": "prod_12345",
  "name": "우드 원형 테이블",
  "category": "furniture",
  "price": 150000,
  "removed_bg_image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

#### Response
```json
{
  "success": true,
  "product_id": "prod_12345",
  "mood_analysis": {
    "colors": {
      "dominant_hex": ["#D2B48C", "#8B7355"],
      "warmth_score": 0.78
    },
    "physics": {
      "circularity": 0.92,
      "glossiness": 0.15,
      "complexity": 0.28
    },
    "style": {
      "primary_keyword": "natural_wood",
      "primary_score": 0.85,
      "category": "Natural & Cozy",
      "vector_breakdown": {
        "natural_wood": 0.85,
        "japandi": 0.08,
        "minimalism": 0.04,
        "others": 0.03
      }
    },
    "mood_vector": [0.78, 0.65, 0.42, 0.92, 0.15, 0.28, 0.85, 0.08, ...],
    "cluster_id": 3
  }
}
```

### 1.2 배치 상품 분석 (대량 처리)

**POST /api/v1/products/batch-analyze**

#### Request Body
```json
{
  "products": [
    {
      "product_id": "prod_001",
      "name": "우드 원형 테이블",
      "category": "furniture",
      "removed_bg_image_base64": "iVBORw0KGgo..."
    },
    {
      "product_id": "prod_002",
      "name": "화이트 쿠션",
      "category": "decor",
      "removed_bg_image_base64": "iVBORw0KGgo..."
    }
    // ... 최대 100개
  ]
}
```

#### Response
```json
{
  "success": true,
  "total_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "results": [
    {
      "product_id": "prod_001",
      "status": "success",
      "cluster_id": 3
    },
    {
      "product_id": "prod_002",
      "status": "success",
      "cluster_id": 7
    }
  ],
  "processing_time_seconds": 2.5
}
```

---

## 2. 배경 무드 분석 및 상품 추천 API

### 2.1 배경 분석 + 상품 추천 (통합 API)

**POST /api/v1/match/recommend**

#### Request Body
```json
{
  "background_image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "top_k": 10,
  "filters": {
    "categories": ["furniture", "decor"],  // 선택적
    "min_score": 0.6,                      // 최소 유사도 (0~1)
    "price_range": {                       // 선택적
      "min": 50000,
      "max": 500000
    },
    "styles": ["natural_wood", "white_wood"]  // 특정 스타일만
  },
  "matching_strategy": "weighted"  // "cosine", "euclidean", "weighted"
}
```

#### Response
```json
{
  "success": true,
  "background_mood": {
    "colors": {
      "dominant_hex": ["#FFFFFF", "#D2B48C"],
      "warmth_score": 0.72
    },
    "physics": {
      "linearity": 0.85,
      "glossiness": 0.12,
      "complexity": 0.25
    },
    "style": {
      "primary_keyword": "white_wood",
      "primary_score": 0.88,
      "category": "Natural & Cozy"
    }
  },
  "recommended_products": [
    {
      "product_id": "prod_001",
      "name": "우드 원형 테이블",
      "category": "furniture",
      "price": 150000,
      "image_url": "https://cdn.example.com/prod_001.jpg",
      "match_score": 0.94,
      "match_details": {
        "color_similarity": 0.92,
        "physics_similarity": 0.89,
        "style_similarity": 0.98,
        "overall_match": "excellent"
      },
      "cluster_id": 3
    },
    {
      "product_id": "prod_042",
      "name": "화이트 오크 수납장",
      "category": "furniture",
      "price": 280000,
      "image_url": "https://cdn.example.com/prod_042.jpg",
      "match_score": 0.91,
      "match_details": {
        "color_similarity": 0.95,
        "physics_similarity": 0.84,
        "style_similarity": 0.94,
        "overall_match": "excellent"
      },
      "cluster_id": 3
    }
    // ... 나머지 8개
  ],
  "processing_time_ms": 450
}
```

### 2.2 배경 분석만 (무드 추출)

**POST /api/v1/analyze/background**

#### Request Body
```json
{
  "background_image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

#### Response
```json
{
  "success": true,
  "mood_analysis": {
    "colors": {...},
    "physics": {...},
    "style": {...},
    "mood_vector": [0.72, 0.58, 0.45, ...]
  }
}
```

---

## 3. 유사 상품 검색 API

### 3.1 특정 상품과 유사한 상품 찾기

**GET /api/v1/products/{product_id}/similar**

#### Query Parameters
```
?top_k=5&category=furniture
```

#### Response
```json
{
  "success": true,
  "reference_product": {
    "product_id": "prod_001",
    "name": "우드 원형 테이블"
  },
  "similar_products": [
    {
      "product_id": "prod_089",
      "name": "오크 라운드 테이블",
      "similarity_score": 0.96
    }
    // ... 4개 더
  ]
}
```

---

## 4. Clustering 관리 API

### 4.1 클러스터 재생성

**POST /api/v1/admin/rebuild-clusters**

#### Request Body
```json
{
  "n_clusters": 20,
  "algorithm": "kmeans"  // "kmeans", "dbscan", "hierarchical"
}
```

#### Response
```json
{
  "success": true,
  "total_products": 1500,
  "clusters_created": 20,
  "avg_cluster_size": 75,
  "clustering_time_seconds": 12.3
}
```

### 4.2 클러스터 분포 조회

**GET /api/v1/admin/cluster-stats**

#### Response
```json
{
  "success": true,
  "total_clusters": 20,
  "cluster_distribution": [
    {
      "cluster_id": 0,
      "product_count": 85,
      "dominant_style": "natural_wood",
      "avg_warmth": 0.75
    },
    {
      "cluster_id": 1,
      "product_count": 92,
      "dominant_style": "modern",
      "avg_warmth": 0.32
    }
    // ... 18개 더
  ]
}
```

---

## 5. 데이터베이스 스키마

### 5.1 products 테이블

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
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
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Vector 유사도 검색 인덱스
CREATE INDEX idx_mood_vector ON products
USING ivfflat (mood_vector vector_cosine_ops)
WITH (lists = 100);

-- 일반 인덱스
CREATE INDEX idx_cluster_id ON products(cluster_id);
CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_primary_keyword ON products(primary_keyword);
```

### 5.2 clusters 테이블

```sql
CREATE TABLE clusters (
    id SERIAL PRIMARY KEY,
    cluster_id INTEGER UNIQUE NOT NULL,
    centroid_vector VECTOR(20),
    product_count INTEGER DEFAULT 0,
    dominant_style VARCHAR(50),
    avg_warmth_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 6. Mood Vector 구조 (20차원)

```python
mood_vector = [
    # === Color Features (3차원) ===
    warmth_score,              # [0] 0.0=Cool ~ 1.0=Warm
    dominant_color_h,          # [1] HSV의 H 정규화 (0~1)
    dominant_color_s,          # [2] HSV의 S 정규화 (0~1)

    # === Physics Features (3차원) ===
    linearity_or_circularity,  # [3] 배경: linearity, 소품: circularity
    glossiness,                # [4] 0.0=Matte ~ 1.0=Glossy
    complexity,                # [5] 0.0=Simple ~ 1.0=Complex

    # === Style Features (14차원) ===
    style_natural_wood,        # [6] CLIP 확률
    style_white_wood,          # [7]
    style_japandi,             # [8]
    style_cozy,                # [9]
    style_modern,              # [10]
    style_minimalism,          # [11]
    style_mid_century_modern,  # [12]
    style_industrial,          # [13]
    style_classic,             # [14]
    style_modern_french,       # [15]
    style_hotel_luxury,        # [16]
    style_vintage,             # [17]
    style_pop_art,             # [18]
    style_planterior           # [19]
]
```

---

## 7. 매칭 전략

### 7.1 Cosine Similarity (기본 추천)

```python
from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity([bg_vector], [prod_vector])[0][0]
# 결과: -1.0 ~ 1.0 (1.0에 가까울수록 유사)
```

### 7.2 Weighted Matching (고급 추천)

```python
weights = {
    'color': 0.25,      # 색상 일치도
    'physics': 0.20,    # 물리적 특성 일치도
    'style': 0.55       # 스타일 일치도
}

# 각 축별로 따로 유사도 계산
color_sim = cosine_similarity([bg_color], [prod_color])[0][0]
physics_sim = cosine_similarity([bg_physics], [prod_physics])[0][0]
style_sim = cosine_similarity([bg_style], [prod_style])[0][0]

final_score = (
    color_sim * weights['color'] +
    physics_sim * weights['physics'] +
    style_sim * weights['style']
)
```

### 7.3 Cluster-based Search (성능 최적화)

```python
# 1단계: 배경 벡터와 가장 가까운 클러스터 찾기 (빠름)
nearest_cluster = find_nearest_cluster(bg_vector)

# 2단계: 해당 클러스터 내에서만 상세 검색 (정확)
candidate_products = get_products_in_cluster(nearest_cluster)
ranked_products = rank_by_similarity(bg_vector, candidate_products)

# 결과: 전체 검색 대비 10~20배 빠름
```

---

## 8. removed_background_image_base64 처리 예시

### 8.1 Base64 → OpenCV Image

```python
import base64
import numpy as np
import cv2
from PIL import Image
import io

def base64_to_opencv(base64_string: str) -> np.ndarray:
    """
    Base64 문자열을 OpenCV 이미지(numpy array)로 변환
    """
    # Base64 디코딩
    image_bytes = base64.b64decode(base64_string)

    # PIL Image로 로드
    image_pil = Image.open(io.BytesIO(image_bytes))

    # numpy array로 변환
    image_array = np.array(image_pil)

    # RGBA → BGR 변환 (OpenCV 형식)
    if image_array.shape[2] == 4:
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
    else:
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    return image_bgr
```

### 8.2 상품 JSON → DB 저장 플로우

```python
from app.analyzer import MoodAnalyzer

analyzer = MoodAnalyzer()

# JSON 데이터 처리
product_data = {
    "product_id": "prod_001",
    "name": "우드 원형 테이블",
    "removed_bg_image_base64": "iVBORw0KGgo..."
}

# 1. Base64 → Image
image = base64_to_opencv(product_data['removed_bg_image_base64'])

# 2. 무드 분석
result = analyzer.analyze(
    image=image,
    image_type='prop',
    image_id=product_data['product_id']
)

# 3. Mood Vector 생성
mood_vector = create_mood_vector(result)

# 4. DB 저장
save_to_database({
    'product_id': product_data['product_id'],
    'name': product_data['name'],
    'mood_vector': mood_vector,
    'colors': result['analysis_result']['colors'],
    'physics': result['analysis_result']['physics'],
    'style': result['analysis_result']['style']
})
```

---

## 9. 성능 고려사항

### 9.1 처리 속도 예상치

| 작업 | 예상 시간 | 비고 |
|------|----------|------|
| 단일 상품 분석 | 0.5~1초 | GPU 사용 시 |
| 배치 100개 분석 | 30~60초 | 병렬 처리 시 |
| 배경 분석 | 0.8~1.5초 | Segmentation 포함 |
| Vector 검색 (10K 상품) | 10~50ms | pgvector 인덱스 사용 |
| Cluster 기반 검색 | 5~15ms | 클러스터 크기 50~100 |

### 9.2 확장성 전략

1. **상품이 10만개 이상일 때**: Faiss 또는 Milvus 사용
2. **실시간 추천 응답 속도**: Redis 캐싱 추가
3. **배치 처리**: Celery + Redis Queue 사용
4. **이미지 저장**: S3 + CloudFront CDN

---

## 10. 다음 구현 단계

1. **Vector 생성 로직** 구현
2. **DB 스키마** 생성 (PostgreSQL + pgvector)
3. **Batch API** 구현 (/api/v1/products/batch-analyze)
4. **추천 API** 구현 (/api/v1/match/recommend)
5. **Clustering 로직** 구현
6. **성능 테스트** 및 최적화
