# 🚀 Quick Start Guide

## 빠른 시작 (3분 안에!)

### Docker로 실행 (권장)

```bash
# 1. Docker Compose로 모든 서비스 실행
docker-compose up -d

# 2. Swagger UI 접속
open http://localhost:8000/docs

# 3. 헬스체크
curl http://localhost:8000/health
```

끝! 이제 API를 사용할 수 있습니다.

---

## 로컬 개발 환경 설정

### 1. 사전 준비

```bash
# Python 3.10+ 설치 확인
python --version

# Git 클론
git clone <repository-url>
cd kakao_homes_back
```

### 2. 가상환경 및 의존성

```bash
# 가상환경 생성
python -m venv venv

# 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

**Option A: Docker (권장)**
```bash
# PostgreSQL + pgvector
docker run -d \
  --name mood-matching-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=mood_matching \
  -p 5432:5432 \
  ankane/pgvector:latest

# Redis
docker run -d \
  --name mood-matching-redis \
  -p 6379:6379 \
  redis:7-alpine
```

**Option B: 로컬 설치**
```bash
# macOS
brew install postgresql
brew install redis

# Ubuntu
sudo apt install postgresql postgresql-contrib
sudo apt install redis-server
```

### 4. DB 초기화

```bash
python scripts/init_db.py
```

### 5. 서버 실행

```bash
# 방법 1
python app/main.py

# 방법 2
uvicorn app.main:app --reload

# 방법 3
bash scripts/run.sh
```

서버가 http://localhost:8000 에서 실행됩니다!

---

## 첫 API 호출

### Python으로 테스트

```python
import requests
import base64

# 1. 헬스체크
response = requests.get('http://localhost:8000/health')
print(response.json())  # {'status': 'healthy'}

# 2. 상품 분석 (테스트용 더미 이미지)
with open('test_product.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    'http://localhost:8000/api/v1/products/analyze',
    json={
        "product_id": "test_001",
        "name": "테스트 상품",
        "category": "furniture",
        "removed_bg_image_base64": image_base64
    }
)

print(response.json())
```

### curl로 테스트

```bash
# 헬스체크
curl http://localhost:8000/health

# Swagger UI에서 테스트 (추천)
open http://localhost:8000/docs
```

---

## 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 또는
bash scripts/run_tests.sh
```

---

## 다음 단계

1. **API 문서 확인**: http://localhost:8000/docs
2. **상세 가이드 읽기**:
   - `API_SPECIFICATION.md` - API 명세
   - `IMPLEMENTATION_GUIDE.md` - 구현 가이드
   - `readme.md` - 기술 상세

3. **실제 데이터로 테스트**:
   - 상품 이미지 분석 API 호출
   - 배경 이미지로 추천 받기

---

## 문제 해결

### 포트가 이미 사용 중
```bash
# 8000번 포트 사용 중인 프로세스 확인
lsof -ti:8000 | xargs kill -9
```

### CLIP 모델 다운로드 느림
```bash
# 첫 실행 시 CLIP 모델 다운로드 (~350MB)
# 인터넷 연결 확인 및 기다리기
```

### PostgreSQL 연결 실패
```bash
# Docker 컨테이너 확인
docker ps
docker logs mood-matching-db

# .env 파일의 DB 설정 확인
cat .env | grep DB_
```

---

## 유용한 명령어

```bash
# Docker 전체 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f app

# DB 접속
docker exec -it mood-matching-db psql -U postgres -d mood_matching

# Redis CLI
docker exec -it mood-matching-redis redis-cli

# 테스트 (커버리지 포함)
pytest tests/ --cov=app --cov-report=html
```

---

## 더 자세한 정보

- **상세 명세**: `readme.md`
- **API 문서**: `API_SPECIFICATION.md`
- **구현 가이드**: `IMPLEMENTATION_GUIDE.md`
- **개발 가이드**: `DEVELOPMENT.md`

Happy Coding! 🎉
