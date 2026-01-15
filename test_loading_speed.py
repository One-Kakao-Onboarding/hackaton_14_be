"""
ProductLoader의 로딩 속도 테스트
"""
import time
import os

# 기존 캐시 삭제
if os.path.exists('product_cache.pkl'):
    os.remove('product_cache.pkl')
    print("✅ 기존 캐시 삭제")

print("=" * 80)
print("🚀 ProductLoader 로딩 속도 테스트")
print("=" * 80)

# 로딩 시작
print("\n📦 데이터 로드 시작...")
start_time = time.time()

from app.core.product_loader import ProductLoader

loader = ProductLoader()
loader.load_from_json(use_cache=False)

loading_time = time.time() - start_time

print(f"\n✅ 로딩 완료!")
print(f"   소요 시간: {loading_time:.2f}초")
print(f"   가구: {len(loader.furniture_products)}개")
print(f"   소품: {len(loader.prop_products)}개")
print(f"   전체: {len(loader.all_products)}개")

# 캐시에서 다시 로드 테스트
print("\n" + "=" * 80)
print("📦 캐시에서 재로드 테스트...")
start_time = time.time()

loader2 = ProductLoader()
loader2.load_from_json(use_cache=True)

cache_loading_time = time.time() - start_time

print(f"\n✅ 캐시 로딩 완료!")
print(f"   소요 시간: {cache_loading_time:.2f}초")
print(f"   속도 향상: {loading_time / cache_loading_time:.1f}배")

# 첫 번째 가구 확인
if loader.furniture_products:
    print(f"\n📊 첫 번째 가구 데이터 샘플:")
    product = loader.furniture_products[0]
    print(f"   ID: {product['product_id']}")
    print(f"   이름: {product['name']}")
    print(f"   가격: {product['price']:,}원")
    print(f"   스타일: {product['primary_keyword']}")
    print(f"   따뜻함: {product['warmth_score']:.2f}")
    print(f"   무드 벡터 길이: {len(product['mood_vector'])}")
    print(f"   무드 벡터 샘플: {product['mood_vector'][:5]}")
