#!/bin/bash
# 테스트 실행 스크립트

echo "🧪 Running tests..."

# 가상환경 활성화 (선택사항)
# source venv/bin/activate

# 전체 테스트 실행
pytest tests/ -v

# 또는 특정 테스트만 실행
# pytest tests/test_extractors.py -v

# 코드 커버리지 포함
# pytest tests/ -v --cov=app --cov-report=html --cov-report=term

echo ""
echo "✅ Tests completed!"
