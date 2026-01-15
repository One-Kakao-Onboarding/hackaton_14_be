#!/bin/bash

# Gemini API 키와 함께 서버 시작

# 기존 서버 종료
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 2초 대기
sleep 2

# Gemini API 키 설정 및 서버 시작
export GEMINI_API_KEY="AIzaSyAsLpRBd6H8g0HuF2k_jaUUQQR5YMnGqAU"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server_gemini.log 2>&1 &

echo "서버 시작 중... (PID: $!)"
echo "로그 파일: server_gemini.log"
