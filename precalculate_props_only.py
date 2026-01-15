"""
소품 무드 벡터만 계산하는 스크립트 (메모리 최적화)
"""
import json
import base64
import numpy as np
import cv2
from typing import Dict
import sys
import os
from tqdm import tqdm
import gc

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


def decode_base64_image(base64_string: str) -> np.ndarray:
    """Base64 문자열을 OpenCV 이미지로 디코딩"""
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    image_bytes = base64.b64decode(base64_string)
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    return image


def process_product(product: Dict, analyzer: MoodAnalyzer, vector_manager: MoodVectorManager,
                   product_type: str, index: int) -> Dict:
    """개별 제품의 무드 벡터를 계산"""
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

        # 무드 분석
        product_id = f"{product_type}_{index:04d}"
        analysis_result = analyzer.analyze_prop(image, image_id=product_id)

        # 무드 벡터 생성
        mood_vector = vector_manager.create_mood_vector(analysis_result, image_type='prop')

        # 분석 결과 추출
        colors = analysis_result['analysis_result']['colors']
        physics = analysis_result['analysis_result']['physics']
        style = analysis_result['analysis_result']['style']

        # 새로운 필드 추가
        enriched_product = product.copy()
        enriched_product.update({
            'product_id': product_id,
            'mood_vector': [float(x) for x in mood_vector],
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

        # 메모리 정리
        del image
        del analysis_result

        return enriched_product

    except Exception as e:
        print(f"Error processing {product_type}_{index}: {e}")
        return product


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("소품 무드 벡터 계산")
    print("=" * 60)

    # 파일 경로
    props_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_interior_data_with_mood.json'
    props_output_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_interior_data_with_precalculated_mood.json'

    # Analyzer 초기화
    print("\n1. MoodAnalyzer 초기화 중...")
    analyzer = MoodAnalyzer(clip_model="ViT-B/32", device="cpu")
    vector_manager = MoodVectorManager()
    print("   ✓ 초기화 완료")

    # 소품 데이터 로딩
    print("\n2. 소품 데이터 로딩 중...")
    with open(props_path, 'r', encoding='utf-8') as f:
        props_data = json.load(f)
    print(f"   ✓ {len(props_data)}개 소품 로딩 완료")

    # 소품 무드 벡터 계산
    print("\n3. 소품 무드 벡터 계산 중...")
    props_results = []

    for idx, product in enumerate(tqdm(props_data, desc="소품 처리")):
        enriched_product = process_product(product, analyzer, vector_manager, 'prop', idx)
        props_results.append(enriched_product)

        # 10개마다 메모리 정리
        if (idx + 1) % 10 == 0:
            gc.collect()

        # 50개마다 중간 저장
        if (idx + 1) % 50 == 0:
            temp_path = props_output_path.replace('.json', f'_checkpoint_{idx+1}.json')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(props_results, f, ensure_ascii=False, indent=2)
            print(f"\n   체크포인트 저장: {idx+1}/{len(props_data)}")

    # 최종 저장
    print(f"\n4. 소품 데이터 저장 중: {props_output_path}")
    with open(props_output_path, 'w', encoding='utf-8') as f:
        json.dump(props_results, f, ensure_ascii=False, indent=2)
    print("   ✓ 저장 완료")

    # 통계 출력
    print("\n" + "=" * 60)
    print("처리 완료!")
    print("=" * 60)
    print(f"총 처리 소품 수: {len(props_results)}개")
    print(f"\n출력 파일: {props_output_path}")
    print("=" * 60)

    # 샘플 출력
    if props_results:
        print("\n[샘플] 첫 번째 소품의 무드 벡터 (앞 10차원):")
        sample = props_results[0]
        if 'mood_vector' in sample:
            print(f"  제품명: {sample['name']}")
            print(f"  무드 벡터: {sample.get('mood_vector', [])[:10]}...")
            print(f"  주요 색상: {sample.get('dominant_colors', [])}")
            print(f"  따뜻함: {sample.get('warmth_score', 0):.2f}")
            print(f"  주 스타일: {sample.get('primary_style', 'N/A')}")


if __name__ == "__main__":
    main()
