# ===== Stage 1: Base =====
FROM python:3.10-slim as base

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


# ===== Stage 2: Dependencies =====
FROM base as dependencies

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ===== Stage 3: Application =====
FROM dependencies as application

# 애플리케이션 코드 복사
COPY ./app /app/app
COPY .env .env

# 모델 디렉토리 생성
RUN mkdir -p /app/models /app/logs

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ===== Stage 4: Development (선택사항) =====
FROM application as development

# 개발 도구 설치
RUN pip install --no-cache-dir pytest pytest-cov ipython

# Hot reload 활성화
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
