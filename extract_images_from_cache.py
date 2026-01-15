"""
캐시에서 상품 이미지 추출 스크립트
product_cache.pkl에서 removed_bg_image_base64를 읽어 PNG 파일로 저장
"""
import pickle
import base64
import os
from io import BytesIO
from PIL import Image


def extract_images_from_cache(cache_file='product_cache.pkl', output_dir='product_images'):
    """
    캐시 파일에서 상품 이미지 추출

    Args:
        cache_file: 캐시 파일 경로
        output_dir: 이미지 저장 디렉토리
    """
    print("="*80)
    print("📦 캐시에서 상품 이미지 추출")
    print("="*80)

    # 1. 캐시 파일 확인
    if not os.path.exists(cache_file):
        print(f"\n❌ 캐시 파일을 찾을 수 없습니다: {cache_file}")
        print("   먼저 API 서버를 실행하여 캐시를 생성하세요.")
        return

    print(f"\n📂 캐시 파일: {cache_file}")
    print(f"   크기: {os.path.getsize(cache_file) / 1024:.1f}KB")

    # 2. 캐시 로드
    print("\n🔄 캐시 로드 중...")
    try:
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)

        furniture_products = cached_data.get('furniture', [])
        prop_products = cached_data.get('prop', [])
        all_products = cached_data.get('all', [])

        print(f"✅ 캐시 로드 완료")
        print(f"   가구: {len(furniture_products)}개")
        print(f"   소품: {len(prop_products)}개")
        print(f"   전체: {len(all_products)}개")

    except Exception as e:
        print(f"\n❌ 캐시 로드 실패: {e}")
        return

    # 3. 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📁 출력 디렉토리: {output_dir}/")

    # 4. 이미지 추출
    print("\n🖼️  이미지 추출 시작...\n")

    success_count = 0
    fail_count = 0

    for product in all_products:
        try:
            product_id = product['product_id']
            category = product['category']
            name = product['name']
            base64_str = product.get('removed_bg_image_base64', '')

            if not base64_str:
                print(f"⚠️  [{product_id}] 이미지 데이터 없음")
                fail_count += 1
                continue

            # data:image/png;base64, 프리픽스 제거
            if ',' in base64_str and base64_str.startswith('data:'):
                base64_str = base64_str.split(',', 1)[1]

            # Base64 디코딩
            image_data = base64.b64decode(base64_str)
            pil_image = Image.open(BytesIO(image_data))

            # 파일명 생성
            filename = f"{product_id}.png"
            filepath = os.path.join(output_dir, filename)

            # 이미지 저장
            pil_image.save(filepath, 'PNG')

            # 통계 출력
            print(f"✅ [{product_id}] {name[:40]}")
            print(f"   파일: {filename}")
            print(f"   크기: {pil_image.size[0]}x{pil_image.size[1]}px")
            print(f"   용량: {len(image_data)/1024:.1f}KB")
            print()

            success_count += 1

        except Exception as e:
            print(f"❌ [{product_id}] 실패: {e}\n")
            fail_count += 1

    # 5. 요약
    print("="*80)
    print("📊 추출 완료")
    print("="*80)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📁 저장 위치: {os.path.abspath(output_dir)}/")
    print("="*80)

    # 6. 카테고리별 통계
    furniture_count = sum(1 for p in all_products if p['category'] == 'furniture')
    prop_count = sum(1 for p in all_products if p['category'] == 'prop')

    print(f"\n📦 카테고리별:")
    print(f"   가구: {furniture_count}개")
    print(f"   소품: {prop_count}개")


def extract_by_category(cache_file='product_cache.pkl', category='furniture', output_dir='product_images'):
    """
    특정 카테고리만 추출

    Args:
        cache_file: 캐시 파일 경로
        category: 'furniture' or 'prop'
        output_dir: 이미지 저장 디렉토리
    """
    print("="*80)
    print(f"📦 캐시에서 {category.upper()} 이미지 추출")
    print("="*80)

    # 캐시 로드
    if not os.path.exists(cache_file):
        print(f"\n❌ 캐시 파일을 찾을 수 없습니다: {cache_file}")
        return

    with open(cache_file, 'rb') as f:
        cached_data = pickle.load(f)

    # 카테고리 선택
    if category == 'furniture':
        products = cached_data.get('furniture', [])
    elif category == 'prop':
        products = cached_data.get('prop', [])
    else:
        print(f"❌ 잘못된 카테고리: {category}")
        return

    print(f"\n✅ {len(products)}개 상품 발견")

    # 출력 디렉토리
    category_dir = os.path.join(output_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    print(f"📁 출력 디렉토리: {category_dir}/\n")

    # 이미지 추출
    for product in products:
        try:
            product_id = product['product_id']
            base64_str = product.get('removed_bg_image_base64', '')

            if not base64_str:
                continue

            # 프리픽스 제거
            if ',' in base64_str and base64_str.startswith('data:'):
                base64_str = base64_str.split(',', 1)[1]

            # 디코딩 & 저장
            image_data = base64.b64decode(base64_str)
            pil_image = Image.open(BytesIO(image_data))

            filename = f"{product_id}.png"
            filepath = os.path.join(category_dir, filename)
            pil_image.save(filepath, 'PNG')

            print(f"✅ {filename} ({pil_image.size[0]}x{pil_image.size[1]}px, {len(image_data)/1024:.1f}KB)")

        except Exception as e:
            print(f"❌ [{product_id}] 실패: {e}")

    print(f"\n✅ 완료: {category_dir}/")


def list_cache_products(cache_file='product_cache.pkl'):
    """
    캐시에 있는 상품 목록 출력
    """
    if not os.path.exists(cache_file):
        print(f"❌ 캐시 파일 없음: {cache_file}")
        return

    with open(cache_file, 'rb') as f:
        cached_data = pickle.load(f)

    all_products = cached_data.get('all', [])

    print("="*80)
    print(f"📦 캐시 상품 목록 ({len(all_products)}개)")
    print("="*80)

    for i, product in enumerate(all_products, 1):
        print(f"\n{i}. {product['product_id']}")
        print(f"   이름: {product['name'][:60]}")
        print(f"   카테고리: {product['category']}")
        print(f"   가격: {product['price']:,}원")
        print(f"   스타일: {product['primary_keyword']}")
        print(f"   색온도: {product['warmth_score']:.2f}")
        print(f"   이미지: {'있음' if product.get('removed_bg_image_base64') else '없음'}")

    print("\n" + "="*80)


if __name__ == "__main__":
    import sys

    # 사용법 출력
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
사용법:

1. 전체 상품 이미지 추출:
   python3 extract_images_from_cache.py

2. 특정 카테고리만 추출:
   python3 extract_images_from_cache.py furniture
   python3 extract_images_from_cache.py prop

3. 상품 목록만 확인:
   python3 extract_images_from_cache.py list

4. 출력 디렉토리 지정:
   python3 extract_images_from_cache.py all my_images/
   python3 extract_images_from_cache.py furniture my_images/
        """)
        sys.exit(0)

    # 명령어 파싱
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            # 목록 출력
            list_cache_products()

        elif command in ['furniture', 'prop']:
            # 카테고리별 추출
            output_dir = sys.argv[2] if len(sys.argv) > 2 else 'product_images'
            extract_by_category(category=command, output_dir=output_dir)

        elif command == 'all':
            # 전체 추출
            output_dir = sys.argv[2] if len(sys.argv) > 2 else 'product_images'
            extract_images_from_cache(output_dir=output_dir)

        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print("사용법: python3 extract_images_from_cache.py [list|all|furniture|prop] [output_dir]")

    else:
        # 기본: 전체 추출
        extract_images_from_cache()
