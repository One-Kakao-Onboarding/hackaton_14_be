"""
상대 좌표 시스템 테스트
왼쪽 아래를 (0, 0)으로 하는 상대 좌표 (0.0 ~ 1.0)
"""
import requests
import json
import base64
from PIL import Image
from io import BytesIO


def test_relative_coordinates():
    """상대 좌표로 API 테스트"""

    print("=" * 80)
    print("🧪 상대 좌표 시스템 테스트")
    print("=" * 80)

    # 1. 테스트 이미지 로드
    image_path = "test_image.png"
    print(f"\n📁 이미지 로드: {image_path}")

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"✅ 이미지 로드 성공 ({len(image_bytes):,} bytes)")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return

    # 2. 이미지 크기 확인
    import cv2
    import numpy as np
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_height, image_width = img.shape[:2]
    print(f"   이미지 크기: {image_width}x{image_height}")

    # 3. 원래 빨간 원의 절대 좌표를 상대 좌표로 변환
    # 절대 좌표 (OpenCV 기준: 왼쪽 위가 원점)
    abs_x, abs_y, abs_r = 310, 212, 116

    # 상대 좌표로 변환 (왼쪽 아래가 원점)
    rel_x = abs_x / image_width  # 0.0 (왼쪽) ~ 1.0 (오른쪽)
    rel_y = 1.0 - (abs_y / image_height)  # 0.0 (아래) ~ 1.0 (위), Y축 반전
    rel_r = abs_r / image_width  # 이미지 너비 기준

    print(f"\n🔴 원래 빨간 원:")
    print(f"   절대 좌표: ({abs_x}, {abs_y}), 반지름 {abs_r}px")
    print(f"   상대 좌표: ({rel_x:.4f}, {rel_y:.4f}), 반지름 {rel_r:.4f}")

    # 4. 동그라미 데이터 (상대 좌표)
    circles_data = [
        {
            "x": rel_x,
            "y": rel_y,
            "radius": rel_r
        }
    ]
    circles_json = json.dumps(circles_data)

    print(f"\n📤 전송할 데이터:")
    print(f"   좌표 시스템: 상대 좌표 (0.0 ~ 1.0)")
    print(f"   원점: 왼쪽 아래 (0, 0)")
    print(f"   x: {rel_x:.4f} (0=왼쪽, 1=오른쪽)")
    print(f"   y: {rel_y:.4f} (0=아래, 1=위)")
    print(f"   radius: {rel_r:.4f} (이미지 너비 기준)")

    # 5. API 호출
    url = "http://localhost:8000/api/ai-interior"

    files = {
        'image': ('test_image.png', image_bytes, 'image/png')
    }
    data = {
        'circles': circles_json
    }

    print(f"\n🚀 API 호출: {url}")

    try:
        response = requests.post(url, files=files, data=data, timeout=120)
        print(f"\n📡 응답 상태: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ 에러: {response.text}")
            return

        result = response.json()

        # 6. 결과 출력
        print("\n" + "=" * 80)
        print("📊 분석 결과")
        print("=" * 80)

        print(f"\n✅ 처리 성공: {result['success']}")
        print(f"💬 메시지: {result['message']}")

        # 동그라미 영역 정보
        if result.get('circle_info'):
            circle = result['circle_info']
            print(f"\n🔴 동그라미 영역 분석:")
            print(f"   입력 (상대): ({rel_x:.4f}, {rel_y:.4f}), r={rel_r:.4f}")
            print(f"   처리 (절대): ({circle['center_x']}, {circle['center_y']}), r={circle['radius']}px")
            print(f"   예상 (절대): ({abs_x}, {abs_y}), r={abs_r}px")

            # 정확도 확인
            x_error = abs(circle['center_x'] - abs_x)
            y_error = abs(circle['center_y'] - abs_y)
            r_error = abs(circle['radius'] - abs_r)

            print(f"\n   정확도:")
            print(f"      X 오차: {x_error}px")
            print(f"      Y 오차: {y_error}px")
            print(f"      반지름 오차: {r_error}px")

            if x_error <= 1 and y_error <= 1 and r_error <= 1:
                print(f"      ✅ 좌표 변환 정확!")
            else:
                print(f"      ⚠️  좌표 오차 있음")

            print(f"\n   카테고리: {circle['category'].upper()}")
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
            print(f"   색온도: {mood['warmth_score']:.2f}")
            print(f"   주조색: {', '.join(mood['dominant_colors'])}")

        # 추천 상품
        products = result.get('recommended_products', [])
        print(f"\n🛍️  추천 상품 ({len(products)}개):")
        print("-" * 80)

        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   매칭: {product['match_score']:.2%}")

            # 시뮬레이션 이미지 저장
            if product.get('simulated_image_base64'):
                try:
                    image_data = base64.b64decode(product['simulated_image_base64'])
                    pil_image = Image.open(BytesIO(image_data))
                    output_path = f"relative_simulated_{product['product_id']}.png"
                    pil_image.save(output_path)
                    print(f"   💾 시뮬레이션: {output_path}")
                except Exception as e:
                    print(f"   ⚠️  이미지 저장 실패: {e}")

        print("\n" + "=" * 80)
        print("✅ 상대 좌표 테스트 완료!")
        print("=" * 80)

        # 7. 결과 저장
        output_file = "relative_coordinates_result.json"
        result_summary = result.copy()
        if 'recommended_products' in result_summary:
            for product in result_summary['recommended_products']:
                if 'simulated_image_base64' in product:
                    product['simulated_image_base64'] = f"[BASE64 - {len(product['simulated_image_base64'])} chars]"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과 저장: {output_file}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버 연결 실패!")
        print("   서버를 먼저 실행해주세요:")
        print("   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_relative_coordinates()
