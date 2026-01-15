"""
JSON 데이터를 분석하여 PostgreSQL DB에 로드하는 스크립트
"""
import sys
import os
sys.path.append('..')

import json
import base64
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from tqdm import tqdm

from app.database import SessionLocal, ProductCRUD, init_db
from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


def base64_to_cv_image(base64_str: str) -> np.ndarray:
    """Base64 문자열을 OpenCV 이미지로 변환"""
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    # PIL RGB -> OpenCV BGR
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return cv_image


def load_products_from_json(json_file: str, category: str):
    """
    JSON 파일에서 상품을 읽어서 분석 후 DB에 저장

    Args:
        json_file: JSON 파일 경로
        category: 'furniture' 또는 'prop'
    """
    print(f"\n{'='*80}")
    print(f"📦 {json_file} 로딩 중... (카테고리: {category})")
    print(f"{'='*80}\n")

    # JSON 로드
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"✅ {len(products)}개 상품 발견\n")

    # 분석기 초기화
    mood_analyzer = MoodAnalyzer()
    vector_manager = MoodVectorManager()

    # DB 세션
    db = SessionLocal()

    success_count = 0
    fail_count = 0

    try:
        for idx, product in enumerate(tqdm(products, desc="상품 분석 및 저장")):
            try:
                # 1. 기본 정보 추출
                product_id = f"{category}_{idx+1:04d}"
                name = product.get('name', 'Unknown')
                brand = product.get('brand', '')
                price = product.get('discount_price') or product.get('original_price', 0)
                image_url = product.get('image_url', '')
                product_url = product.get('product_url', '')
                removed_bg_base64 = product.get('removed_background_image_base64', '')

                # 2. 이미지 분석
                if not removed_bg_base64:
                    print(f"⚠️  [{product_id}] 배경 제거 이미지 없음. 스킵.")
                    fail_count += 1
                    continue

                # Base64 -> OpenCV 이미지
                cv_image = base64_to_cv_image(removed_bg_base64)

                # Mood 분석
                analysis = mood_analyzer.analyze(
                    image=cv_image,
                    image_type='prop',  # 배경 제거된 상품은 모두 prop 분석
                    image_id=product_id
                )

                # Mood Vector 생성
                mood_vector = vector_manager.create_mood_vector(
                    analysis_result=analysis,
                    image_type='prop'
                )

                # 3. DB 저장
                product_data = {
                    'product_id': product_id,
                    'name': f"{brand} {name}" if brand else name,
                    'category': category,
                    'price': int(price) if price else 0,
                    'image_url': image_url,
                    'removed_bg_image_base64': removed_bg_base64,
                    'mood_vector': mood_vector.tolist(),

                    # Color
                    'dominant_hex_1': analysis['analysis_result']['colors']['dominant_hex'][0] if len(analysis['analysis_result']['colors']['dominant_hex']) > 0 else None,
                    'dominant_hex_2': analysis['analysis_result']['colors']['dominant_hex'][1] if len(analysis['analysis_result']['colors']['dominant_hex']) > 1 else None,
                    'warmth_score': analysis['analysis_result']['colors']['warmth_score'],

                    # Physics
                    'circularity': analysis['analysis_result']['physics'].get('circularity', 0.0),
                    'glossiness': analysis['analysis_result']['physics']['glossiness'],
                    'complexity': analysis['analysis_result']['physics']['complexity'],

                    # Style
                    'primary_keyword': analysis['analysis_result']['style']['primary_keyword'],
                    'primary_score': analysis['analysis_result']['style']['primary_score'],
                    'category_style': analysis['analysis_result']['style']['category'],
                    'style_vector': analysis['analysis_result']['style']['vector_breakdown'],

                    # 클러스터는 나중에 별도로 할당
                    'cluster_id': None,
                    'is_active': True
                }

                # DB에 저장
                ProductCRUD.create_product(db, product_data)
                success_count += 1

            except Exception as e:
                print(f"\n❌ [{product_id}] 처리 실패: {e}")
                fail_count += 1
                continue

        print(f"\n{'='*80}")
        print(f"✅ 데이터 로드 완료!")
        print(f"   성공: {success_count}개")
        print(f"   실패: {fail_count}개")
        print(f"{'='*80}\n")

    finally:
        db.close()


def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("🚀 상품 데이터 로드 시작")
    print("="*80)

    # 1. DB 초기화
    print("\n1️⃣  데이터베이스 초기화...")
    try:
        init_db()
        print("✅ DB 초기화 완료\n")
    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")
        sys.exit(1)

    # 2. 가구 데이터 로드
    furniture_file = '../kakao_furniture_data_parsed.json'
    if os.path.exists(furniture_file):
        load_products_from_json(furniture_file, 'furniture')
    else:
        print(f"⚠️  {furniture_file} 파일이 없습니다.")

    # 3. 인테리어 소품 데이터 로드
    interior_file = '../kakao_interior_data_parsed.json'
    if os.path.exists(interior_file):
        load_products_from_json(interior_file, 'prop')
    else:
        print(f"⚠️  {interior_file} 파일이 없습니다.")

    # 4. 통계 출력
    db = SessionLocal()
    try:
        total = ProductCRUD.count_products(db)
        furniture_count = len(ProductCRUD.get_products(db, category='furniture', limit=10000))
        prop_count = len(ProductCRUD.get_products(db, category='prop', limit=10000))

        print("\n" + "="*80)
        print("📊 최종 통계")
        print("="*80)
        print(f"전체 상품: {total}개")
        print(f"  - 가구: {furniture_count}개")
        print(f"  - 소품: {prop_count}개")
        print("="*80 + "\n")

    finally:
        db.close()

    print("\n✅ 모든 작업 완료!")
    print("\n다음 단계:")
    print("1. 클러스터링 실행 (선택사항)")
    print("2. API 서버 시작: python -m uvicorn app.main:app --reload")
    print()


if __name__ == "__main__":
    main()
