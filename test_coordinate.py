"""
test_image2.png를 특정 좌표로 AI Interior API 테스트
"""
import requests
import json
import os
import base64
from io import BytesIO
from PIL import Image

# API 설정
API_URL = "http://localhost:8000/api/ai-interior"

# 테스트 이미지 경로
IMAGE_PATH = "test_image2.png"

# 테스트 좌표 (상대 좌표 0~1 범위)
circles = [
    {
        "x": 0.7215782000661312,
        "y": 0.56,
        "radius": 0.09512911389498678
    }
]

def test_ai_interior():
    """AI Interior API 테스트"""

    # 이미지 파일 확인
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {IMAGE_PATH}")
        return

    print(f"📸 이미지 로드: {IMAGE_PATH}")

    # 이미지 파일 열기
    with open(IMAGE_PATH, 'rb') as f:
        image_data = f.read()

    print(f"📏 이미지 크기: {len(image_data) / 1024:.1f}KB")
    print(f"📍 테스트 좌표: {circles[0]}")
    print(f"\n🚀 API 호출 중: {API_URL}")
    print("-" * 60)

    try:
        # API 호출
        response = requests.post(
            API_URL,
            files={
                'image': ('test_image2.png', image_data, 'image/png')
            },
            data={
                'circles': json.dumps(circles)
            },
            timeout=120  # 2분 타임아웃
        )

        # 응답 확인
        if response.status_code == 200:
            result = response.json()

            print("\n✅ API 호출 성공!")
            print("=" * 60)

            # Circle Info
            if 'circle_info' in result:
                circle_info = result['circle_info']
                print("\n📍 동그라미 영역 분석:")
                print(f"   절대 좌표: ({circle_info['center_x']}, {circle_info['center_y']})")
                print(f"   반지름: {circle_info['radius']}px")
                print(f"   카테고리: {circle_info['category']}")
                print(f"   신뢰도: {circle_info['confidence']:.2f}")
                print(f"   설명: {circle_info['description']}")
                print(f"   공간 유형: {circle_info.get('placement_surface', 'N/A')}")
                if circle_info.get('gemini_recommendations'):
                    print(f"   Gemini 추천: {', '.join(circle_info['gemini_recommendations'])}")

            # Background Mood
            if 'background_mood' in result:
                bg_mood = result['background_mood']
                print("\n🎨 배경 무드 분석:")
                print(f"   스타일: {bg_mood['primary_style']}")
                print(f"   카테고리: {bg_mood['category']}")
                print(f"   신뢰도: {bg_mood['confidence']:.2f}")
                print(f"   따뜻함 점수: {bg_mood['warmth_score']:.2f}")
                print(f"   주요 색상: {', '.join(bg_mood['dominant_colors'])}")

            # Recommended Products
            if 'recommended_products' in result:
                products = result['recommended_products']
                print(f"\n🛍️ 추천 상품 ({len(products)}개):")
                print("=" * 60)

                for idx, product in enumerate(products, 1):
                    print(f"\n[{idx}] {product['name']}")
                    print(f"   상품 ID: {product['product_id']}")
                    print(f"   카테고리: {product.get('category', 'N/A')}")
                    print(f"   가격: {product.get('price', 0):,}원")
                    print(f"   매칭 점수: {product['match_score']:.4f}")

                    # Match Details
                    if 'match_details' in product:
                        details = product['match_details']
                        print(f"   무드 점수: {details.get('original_mood_score', 0):.4f}")
                        print(f"   키워드 점수: {details.get('keyword_match_score', 0):.4f}")
                        print(f"   공간 적합성: {details.get('spatial_suitability_score', 0):.4f}")
                        print(f"   배치 유형: {details.get('product_placement_type', 'N/A')}")

                    # 시뮬레이션 이미지 저장
                    if 'simulated_image_base64' in product and product['simulated_image_base64']:
                        output_filename = f"simulation_result_{idx}.png"

                        # Base64 디코딩 후 저장
                        image_data = base64.b64decode(product['simulated_image_base64'])
                        with open(output_filename, 'wb') as f:
                            f.write(image_data)

                        print(f"   ✅ 시뮬레이션 이미지 저장: {output_filename}")

            # 메시지
            if 'message' in result:
                print(f"\n💬 {result['message']}")

            print("\n" + "=" * 60)

        else:
            print(f"\n❌ API 호출 실패: HTTP {response.status_code}")
            print(f"응답: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("API 서버가 실행 중인지 확인해주세요:")
        print("  python -m uvicorn app.main:app --reload")

    except requests.exceptions.Timeout:
        print("\n❌ 요청 시간 초과 (120초)")
        print("이미지가 너무 크거나 서버 응답이 느릴 수 있습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ai_interior()
