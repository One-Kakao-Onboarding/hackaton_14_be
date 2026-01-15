"""
AI 인테리어 API 테스트 스크립트
"""
import requests
import json
import base64
from PIL import Image
from io import BytesIO


def test_ai_interior_api():
    """AI 인테리어 API 테스트"""

    print("=" * 70)
    print("🧪 AI 인테리어 API 테스트")
    print("=" * 70)

    # 1. 테스트 이미지 로드
    image_path = "test_image.png"
    print(f"\n📁 이미지 로드: {image_path}")

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"✅ 이미지 로드 성공 ({len(image_bytes)} bytes)")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return

    # 2. API 요청 준비
    url = "http://localhost:8000/api/ai-interior"

    # 동그라미 정보 (test_image.png의 빨간색 원 위치)
    circles_data = [
        {
            "x": 310,
            "y": 212,
            "radius": 116
        }
    ]

    # FormData 구성
    files = {
        'image': ('test_image.png', image_bytes, 'image/png')
    }
    data = {
        'circles': json.dumps(circles_data)
    }

    print(f"\n🚀 API 호출: {url}")
    print(f"   동그라미: x={circles_data[0]['x']}, y={circles_data[0]['y']}, radius={circles_data[0]['radius']}")

    # 3. API 호출
    try:
        response = requests.post(url, files=files, data=data, timeout=120)
        print(f"\n📡 응답 상태: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ 에러: {response.text}")
            return

        result = response.json()

        # 4. 결과 출력
        print("\n" + "=" * 70)
        print("📊 분석 결과")
        print("=" * 70)

        print(f"\n✅ 처리 성공: {result['success']}")
        print(f"💬 메시지: {result['message']}")

        # 동그라미 영역 정보
        if result.get('circle_info'):
            circle = result['circle_info']
            print(f"\n🔴 동그라미 영역:")
            print(f"   위치: ({circle['center_x']}, {circle['center_y']})")
            print(f"   반지름: {circle['radius']}px")
            print(f"   카테고리: {circle['category'].upper()}")
            print(f"   확신도: {circle['confidence']:.2%}")
            print(f"   설명: {circle['description']}")
            print(f"   Gemini 추천:")
            for i, rec in enumerate(circle['gemini_recommendations'], 1):
                print(f"      {i}. {rec}")

        # 배경 무드
        if result.get('background_mood'):
            mood = result['background_mood']
            print(f"\n🎨 배경 무드:")
            print(f"   스타일: {mood['primary_style']} ({mood['category']})")
            print(f"   확신도: {mood['confidence']:.2%}")
            print(f"   색온도: {mood['warmth_score']:.2f} (0=Cool, 1=Warm)")
            print(f"   주조색: {', '.join(mood['dominant_colors'])}")

        # 추천 상품
        products = result.get('recommended_products', [])
        print(f"\n🛍️  추천 상품 ({len(products)}개):")
        print("-" * 70)

        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name']} (ID: {product['product_id']})")
            print(f"   카테고리: {product['category']}")
            print(f"   가격: {product['price']:,}원")
            print(f"   매칭 점수: {product['match_score']:.2%}")
            print(f"   상세:")
            print(f"      - 색상 유사도: {product['match_details']['color_similarity']:.2%}")
            print(f"      - 물리 유사도: {product['match_details']['physics_similarity']:.2%}")
            print(f"      - 스타일 유사도: {product['match_details']['style_similarity']:.2%}")

            # 시뮬레이션 이미지 저장
            if product.get('simulated_image_base64'):
                try:
                    image_data = base64.b64decode(product['simulated_image_base64'])
                    pil_image = Image.open(BytesIO(image_data))
                    output_path = f"simulated_{product['product_id']}.png"
                    pil_image.save(output_path)
                    print(f"      💾 시뮬레이션 이미지 저장: {output_path}")
                except Exception as e:
                    print(f"      ⚠️  시뮬레이션 이미지 디코딩 실패: {e}")

        print("\n" + "=" * 70)
        print("✅ 테스트 완료!")
        print("=" * 70)

        # 5. JSON 파일로 저장
        output_file = "ai_interior_result.json"

        # base64 이미지는 너무 크므로 제외
        result_without_images = result.copy()
        if 'recommended_products' in result_without_images:
            for product in result_without_images['recommended_products']:
                if 'simulated_image_base64' in product:
                    product['simulated_image_base64'] = f"<base64 데이터 ({len(product['simulated_image_base64'])} chars)>"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_without_images, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과 저장됨: {output_file}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버 연결 실패!")
        print("   서버가 실행 중인지 확인하세요:")
        print("   python app/main.py")
    except requests.exceptions.Timeout:
        print("\n❌ 요청 시간 초과 (120초)")
        print("   이미지 처리가 너무 오래 걸립니다.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ai_interior_api()
