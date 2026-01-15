"""
미리 계산된 무드 벡터를 사용하는 ProductLoader 테스트
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.product_loader import ProductLoader

def main():
    print("=" * 60)
    print("ProductLoader 테스트 (미리 계산된 무드 벡터 사용)")
    print("=" * 60)

    # 로딩 시간 측정
    start_time = time.time()

    # ProductLoader 초기화 및 데이터 로드
    loader = ProductLoader()
    success = loader.load_from_json(use_cache=False)  # 캐시 사용 안 함

    load_time = time.time() - start_time

    if not success:
        print("❌ 데이터 로드 실패")
        return

    print(f"\n⏱️  로딩 시간: {load_time:.2f}초")
    print(f"✅ 총 제품 수: {len(loader.all_products)}개")
    print(f"   - 가구: {len(loader.furniture_products)}개")
    print(f"   - 소품: {len(loader.prop_products)}개")

    # 첫 번째 가구 샘플 확인
    if loader.furniture_products:
        print("\n" + "=" * 60)
        print("🪑 가구 샘플 데이터")
        print("=" * 60)
        sample = loader.furniture_products[0]
        print(f"  제품 ID: {sample['product_id']}")
        print(f"  제품명: {sample['name']}")
        print(f"  카테고리: {sample['category']}")
        print(f"  가격: {sample['price']:,}원")
        print(f"  무드 벡터 차원: {len(sample['mood_vector'])}D")
        print(f"  무드 벡터 (앞 5개): {[round(x, 3) for x in sample['mood_vector'][:5]]}")
        print(f"  주요 색상: {sample['dominant_hex']}")
        print(f"  따뜻함 점수: {sample['warmth_score']:.3f}")
        print(f"  주 스타일: {sample['primary_keyword']}")

    # 첫 번째 소품 샘플 확인
    if loader.prop_products:
        print("\n" + "=" * 60)
        print("🎨 소품 샘플 데이터")
        print("=" * 60)
        sample = loader.prop_products[0]
        print(f"  제품 ID: {sample['product_id']}")
        print(f"  제품명: {sample['name'][:50]}...")
        print(f"  카테고리: {sample['category']}")
        print(f"  가격: {sample['price']:,}원")
        print(f"  무드 벡터 차원: {len(sample['mood_vector'])}D")
        print(f"  무드 벡터 (앞 5개): {[round(x, 3) for x in sample['mood_vector'][:5]]}")
        print(f"  주요 색상: {sample['dominant_hex']}")
        print(f"  따뜻함 점수: {sample['warmth_score']:.3f}")
        print(f"  주 스타일: {sample['primary_keyword']}")

    # 유사 제품 검색 테스트
    print("\n" + "=" * 60)
    print("🔍 유사 제품 검색 테스트")
    print("=" * 60)

    if loader.furniture_products:
        # 첫 번째 가구의 무드 벡터로 유사 제품 검색
        test_vector = loader.furniture_products[0]['mood_vector']
        print(f"  기준 제품: {loader.furniture_products[0]['name']}")

        search_start = time.time()
        similar_products = loader.search_similar(
            mood_vector=test_vector,
            category='furniture',
            top_k=5
        )
        search_time = time.time() - search_start

        print(f"  검색 시간: {search_time*1000:.2f}ms")
        print(f"\n  유사 제품 Top 5:")
        for idx, product in enumerate(similar_products, 1):
            similarity_score = product.get('similarity', 0) * 100
            print(f"    {idx}. {product['name'][:40]}... (유사도: {similarity_score:.1f}%)")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
