#!/bin/bash
# FastAPI 서버 실행 스크립트

echo "🚀 Starting Interior Mood Matching API..."

# 가상환경 활성화 (선택사항)
# source venv/bin/activate

# 환경 변수 로드
export $(cat .env | grep -v '^#' | xargs)

# FastAPI 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 또는
# python app/main.py
