"""
무드 벡터 미리 계산 스크립트
JSON 파일의 모든 제품 이미지에 대해 무드 벡터를 계산하고 저장
"""
import json
import base64
import numpy as np
import cv2
from typing import Dict, List
import sys
import os
from tqdm import tqdm

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


def decode_base64_image(base64_string: str) -> np.ndarray:
    """
    Base64 문자열을 OpenCV 이미지로 디코딩

    Args:
        base64_string: 'data:image/png;base64,...' 형식의 문자열

    Returns:
        OpenCV 이미지 (BGR)
    """
    # 'data:image/png;base64,' 제거
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    # Base64 디코딩
    image_bytes = base64.b64decode(base64_string)

    # NumPy 배열로 변환
    nparr = np.frombuffer(image_bytes, np.uint8)

    # OpenCV 이미지로 디코딩
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    return image


def process_product(product: Dict, analyzer: MoodAnalyzer, vector_manager: MoodVectorManager,
                   product_type: str, index: int) -> Dict:
    """
    개별 제품의 무드 벡터를 계산하고 추가 필드를 포함한 딕셔너리 반환

    Args:
        product: 제품 데이터 딕셔너리
        analyzer: MoodAnalyzer 인스턴스
        vector_manager: MoodVectorManager 인스턴스
        product_type: 'furniture' 또는 'prop'
        index: 제품 인덱스

    Returns:
        무드 벡터가 추가된 제품 딕셔너리
    """
    try:
        # Base64 이미지 디코딩
        base64_image = product.get('removed_background_image_base64', '')
        if not base64_image:
            print(f"Warning: {product_type}_{index} has no image")
            return product

        image = decode_base64_image(base64_image)

        if image is None:
            print(f"Warning: Failed to decode {product_type}_{index}")
            return product

        # 무드 분석 (prop 타입으로 분석 - 배경이 제거된 가구/소품)
        product_id = f"{product_type}_{index:04d}"
        analysis_result = analyzer.analyze_prop(image, image_id=product_id)

        # 무드 벡터 생성 (20차원)
        mood_vector = vector_manager.create_mood_vector(analysis_result, image_type='prop')

        # 분석 결과에서 필요한 정보 추출
        colors = analysis_result['analysis_result']['colors']
        physics = analysis_result['analysis_result']['physics']
        style = analysis_result['analysis_result']['style']

        # 새로운 필드 추가
        enriched_product = product.copy()
        enriched_product.update({
            'product_id': product_id,
            'mood_vector': [float(x) for x in mood_vector],  # 20차원 벡터
            'dominant_colors': colors['dominant_hex'],
            'warmth_score': float(colors['warmth_score']),
            'circularity': float(physics.get('circularity', 0.0)),
            'glossiness': float(physics['glossiness']),
            'complexity': float(physics['complexity']),
            'primary_style': style['primary_keyword'],
            'primary_style_score': float(style['primary_score']),
            'style_category': style['category'],
            'style_vector': {k: float(v) for k, v in style['vector_breakdown'].items()}
        })

        return enriched_product

    except Exception as e:
        print(f"Error processing {product_type}_{index}: {e}")
        return product


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("무드 벡터 미리 계산 시작")
    print("=" * 60)

    # 파일 경로
    furniture_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_furniture_data_with_mood.json'
    props_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_interior_data_with_mood.json'

    furniture_output_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_furniture_data_with_precalculated_mood.json'
    props_output_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_interior_data_with_precalculated_mood.json'

    # Analyzer 및 VectorManager 초기화
    print("\n1. MoodAnalyzer 초기화 중...")
    analyzer = MoodAnalyzer(clip_model="ViT-B/32", device="cpu")
    vector_manager = MoodVectorManager()
    print("   ✓ 초기화 완료")

    # 가구 데이터 처리
    print("\n2. 가구 데이터 로딩 중...")
    with open(furniture_path, 'r', encoding='utf-8') as f:
        furniture_data = json.load(f)
    print(f"   ✓ {len(furniture_data)}개 가구 로딩 완료")

    print("\n3. 가구 무드 벡터 계산 중...")
    furniture_results = []
    for idx, product in enumerate(tqdm(furniture_data, desc="가구 처리")):
        enriched_product = process_product(product, analyzer, vector_manager, 'furniture', idx)
        furniture_results.append(enriched_product)

    # 가구 데이터 저장
    print(f"\n4. 가구 데이터 저장 중: {furniture_output_path}")
    with open(furniture_output_path, 'w', encoding='utf-8') as f:
        json.dump(furniture_results, f, ensure_ascii=False, indent=2)
    print("   ✓ 저장 완료")

    # 소품 데이터 처리
    print("\n5. 소품 데이터 로딩 중...")
    with open(props_path, 'r', encoding='utf-8') as f:
        props_data = json.load(f)
    print(f"   ✓ {len(props_data)}개 소품 로딩 완료")

    print("\n6. 소품 무드 벡터 계산 중...")
    props_results = []
    for idx, product in enumerate(tqdm(props_data, desc="소품 처리")):
        enriched_product = process_product(product, analyzer, vector_manager, 'prop', idx)
        props_results.append(enriched_product)

    # 소품 데이터 저장
    print(f"\n7. 소품 데이터 저장 중: {props_output_path}")
    with open(props_output_path, 'w', encoding='utf-8') as f:
        json.dump(props_results, f, ensure_ascii=False, indent=2)
    print("   ✓ 저장 완료")

    # 통계 출력
    print("\n" + "=" * 60)
    print("처리 완료!")
    print("=" * 60)
    print(f"총 처리 제품 수: {len(furniture_results) + len(props_results)}개")
    print(f"  - 가구: {len(furniture_results)}개")
    print(f"  - 소품: {len(props_results)}개")
    print("\n출력 파일:")
    print(f"  - {furniture_output_path}")
    print(f"  - {props_output_path}")
    print("=" * 60)

    # 샘플 출력
    if furniture_results:
        print("\n[샘플] 첫 번째 가구의 무드 벡터 (앞 10차원):")
        sample = furniture_results[0]
        print(f"  제품명: {sample['name']}")
        print(f"  무드 벡터: {sample.get('mood_vector', [])[:10]}...")
        print(f"  주요 색상: {sample.get('dominant_colors', [])}")
        print(f"  따뜻함: {sample.get('warmth_score', 0):.2f}")
        print(f"  주 스타일: {sample.get('primary_style', 'N/A')}")


if __name__ == "__main__":
    main()
