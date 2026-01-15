"""
parsed JSON 파일에 무드 벡터를 미리 계산해서 추가하는 스크립트

kakao_furniture_data_parsed.json과 kakao_interior_data_parsed.json의
각 상품에 무드 벡터를 계산하여 추가합니다.
"""
import json
import sys
import os
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import cv2
import numpy as np

# Unbuffered output for real-time progress
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


def base64_to_cv_image(base64_str: str) -> np.ndarray:
    """Base64 문자열을 OpenCV 이미지로 변환"""
    if ',' in base64_str and base64_str.startswith('data:'):
        base64_str = base64_str.split(',', 1)[1]

    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return cv_image


def process_json_file(
    input_file: str,
    output_file: str,
    category: str,
    max_items: int = None
):
    """
    JSON 파일을 읽어서 무드 벡터를 계산하고 저장

    Args:
        input_file: 입력 JSON 파일 경로
        output_file: 출력 JSON 파일 경로
        category: 'furniture' 또는 'prop'
        max_items: 처리할 최대 아이템 수 (None이면 전체)
    """
    print(f"\n{'='*60}")
    print(f"🎨 {category.upper()} 데이터 처리 중...")
    print(f"{'='*60}")

    input_path = project_root / input_file
    output_path = project_root / output_file

    # JSON 파일 로드
    print(f"📂 파일 로드 중: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    total = len(products)
    process_count = min(max_items, total) if max_items else total

    print(f"   총 {total}개 중 {process_count}개 처리 예정\n")

    # 분석기 초기화
    mood_analyzer = MoodAnalyzer()
    vector_manager = MoodVectorManager()

    # 각 상품 처리
    processed = 0
    failed = 0

    for idx, product in enumerate(products[:process_count]):
        try:
            # 배경 제거된 이미지가 없으면 스킵
            if 'removed_background_image_base64' not in product:
                print(f"   [{idx+1}/{process_count}] ⚠️  배경 제거 이미지 없음 - 스킵")
                failed += 1
                continue

            # Base64 -> OpenCV 이미지
            cv_image = base64_to_cv_image(product['removed_background_image_base64'])

            # Mood 분석
            product_id = f"{category}_{idx+1:04d}"
            analysis = mood_analyzer.analyze(
                image=cv_image,
                image_type='prop',
                image_id=product_id
            )

            # Mood Vector 생성
            mood_vector = vector_manager.create_mood_vector(
                analysis_result=analysis,
                image_type='prop'
            )

            # NumPy 배열이면 리스트로 변환
            if isinstance(mood_vector, np.ndarray):
                mood_vector = mood_vector.tolist()

            # JSON에 무드 정보 추가
            product['mood_analysis'] = {
                'mood_vector': mood_vector,
                'primary_keyword': analysis['analysis_result']['style']['primary_keyword'],
                'secondary_keywords': analysis['analysis_result']['style']['secondary_keywords'],
                'dominant_colors': analysis['analysis_result']['colors']['dominant_hex'][:3],
                'warmth_score': analysis['analysis_result']['colors']['warmth_score'],
                'brightness': analysis['analysis_result']['colors']['brightness'],
                'saturation': analysis['analysis_result']['colors']['saturation']
            }

            processed += 1

            # 진행 상황 출력 (매 1개마다)
            print(f"   [{idx+1}/{process_count}] ✅ 처리 완료 - {product.get('name', 'Unknown')[:30]}...", flush=True)

        except Exception as e:
            print(f"   [{idx+1}/{process_count}] ❌ 오류: {e}")
            failed += 1
            continue

    # 결과 저장
    print(f"\n💾 결과 저장 중: {output_file}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # 파일 크기 확인
    file_size = output_path.stat().st_size / (1024 * 1024)

    print(f"   ✅ 저장 완료!")
    print(f"   파일 크기: {file_size:.2f} MB")
    print(f"   성공: {processed}개")
    print(f"   실패: {failed}개")


def main():
    """메인 실행 함수"""
    print("\n" + "="*60, flush=True)
    print("🎨 무드 벡터 계산 및 JSON 저장 스크립트", flush=True)
    print("="*60, flush=True)

    # 1. 가구 데이터 처리 (테스트: 5개만)
    process_json_file(
        input_file='kakao_furniture_data_parsed.json',
        output_file='kakao_furniture_data_with_mood.json',
        category='furniture',
        max_items=5  # 테스트용으로 5개만
    )

    # 2. 인테리어 소품 데이터 처리 (테스트: 10개만)
    process_json_file(
        input_file='kakao_interior_data_parsed.json',
        output_file='kakao_interior_data_with_mood.json',
        category='prop',
        max_items=10  # 테스트용으로 10개만
    )

    print("\n" + "="*60)
    print("✅ 모든 작업 완료!")
    print("="*60)
    print("\n생성된 파일:")
    print("  - kakao_furniture_data_with_mood.json")
    print("  - kakao_interior_data_with_mood.json")
    print("\n💡 이제 이 파일들을 사용하면 이미지 분석 없이 무드 벡터를 바로 로드할 수 있습니다!")


if __name__ == "__main__":
    main()
