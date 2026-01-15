"""
무드 벡터 미리 계산 스크립트 (최적화 버전)
병렬 처리 및 배치 처리로 속도 향상
"""
import json
import base64
import numpy as np
import cv2
from typing import Dict, List
import sys
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


# 전역 변수로 analyzer 초기화 (각 프로세스마다 한 번만)
analyzer = None
vector_manager = None


def init_worker():
    """워커 프로세스 초기화"""
    global analyzer, vector_manager
    analyzer = MoodAnalyzer(clip_model="ViT-B/32", device="cpu")
    vector_manager = MoodVectorManager()


def decode_base64_image(base64_string: str) -> np.ndarray:
    """Base64 문자열을 OpenCV 이미지로 디코딩"""
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    image_bytes = base64.b64decode(base64_string)
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    return image


def process_product(args):
    """
    개별 제품의 무드 벡터를 계산

    Args:
        args: (product, product_type, index) 튜플

    Returns:
        무드 벡터가 추가된 제품 딕셔너리
    """
    global analyzer, vector_manager

    product, product_type, index = args

    try:
        # Base64 이미지 디코딩
        base64_image = product.get('removed_background_image_base64', '')
        if not base64_image:
            return product

        image = decode_base64_image(base64_image)
        if image is None:
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

        return enriched_product

    except Exception as e:
        print(f"\nError processing {product_type}_{index}: {e}")
        return product


def process_batch_parallel(products: List[Dict], product_type: str, num_workers: int = None):
    """
    제품 리스트를 병렬로 처리

    Args:
        products: 제품 리스트
        product_type: 'furniture' 또는 'prop'
        num_workers: 워커 프로세스 수 (None이면 CPU 코어 수)

    Returns:
        처리된 제품 리스트
    """
    if num_workers is None:
        num_workers = min(multiprocessing.cpu_count(), 4)  # 최대 4개 프로세스

    # (product, product_type, index) 튜플 리스트 생성
    args_list = [(product, product_type, idx) for idx, product in enumerate(products)]

    results = [None] * len(products)

    with ProcessPoolExecutor(max_workers=num_workers, initializer=init_worker) as executor:
        # 작업 제출
        future_to_idx = {executor.submit(process_product, args): idx
                        for idx, args in enumerate(args_list)}

        # 진행 상황 표시
        for future in tqdm(as_completed(future_to_idx),
                          total=len(future_to_idx),
                          desc=f"{product_type} 처리"):
            idx = future_to_idx[future]
            try:
                result = future.result()
                results[idx] = result
            except Exception as e:
                print(f"\nError in future {idx}: {e}")
                results[idx] = products[idx]

    return results


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("무드 벡터 미리 계산 (병렬 처리 버전)")
    print("=" * 60)

    # 파일 경로
    furniture_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_furniture_data_with_mood.json'
    props_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_interior_data_with_mood.json'

    furniture_output_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_furniture_data_with_precalculated_mood.json'
    props_output_path = '/Users/theo.cha/Desktop/kakao_homes_back/kakao_interior_data_with_precalculated_mood.json'

    # CPU 코어 수 확인
    num_cores = multiprocessing.cpu_count()
    num_workers = min(num_cores, 4)  # 최대 4개 워커
    print(f"\nCPU 코어: {num_cores}개, 사용 워커: {num_workers}개")

    # 가구 데이터 처리
    print("\n1. 가구 데이터 로딩 중...")
    with open(furniture_path, 'r', encoding='utf-8') as f:
        furniture_data = json.load(f)
    print(f"   ✓ {len(furniture_data)}개 가구 로딩 완료")

    print("\n2. 가구 무드 벡터 계산 중 (병렬 처리)...")
    furniture_results = process_batch_parallel(furniture_data, 'furniture', num_workers)

    print(f"\n3. 가구 데이터 저장 중: {furniture_output_path}")
    with open(furniture_output_path, 'w', encoding='utf-8') as f:
        json.dump(furniture_results, f, ensure_ascii=False, indent=2)
    print("   ✓ 저장 완료")

    # 소품 데이터 처리
    print("\n4. 소품 데이터 로딩 중...")
    with open(props_path, 'r', encoding='utf-8') as f:
        props_data = json.load(f)
    print(f"   ✓ {len(props_data)}개 소품 로딩 완료")

    print("\n5. 소품 무드 벡터 계산 중 (병렬 처리)...")
    props_results = process_batch_parallel(props_data, 'prop', num_workers)

    print(f"\n6. 소품 데이터 저장 중: {props_output_path}")
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
        if 'mood_vector' in sample:
            print(f"  제품명: {sample['name']}")
            print(f"  무드 벡터: {sample.get('mood_vector', [])[:10]}...")
            print(f"  주요 색상: {sample.get('dominant_colors', [])}")
            print(f"  따뜻함: {sample.get('warmth_score', 0):.2f}")
            print(f"  주 스타일: {sample.get('primary_style', 'N/A')}")


if __name__ == "__main__":
    # macOS에서 multiprocessing 오류 방지
    multiprocessing.set_start_method('spawn', force=True)
    main()
