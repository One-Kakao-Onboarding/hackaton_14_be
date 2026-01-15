"""
사용자 지정 좌표로 테스트
"""
import requests
import json
import base64
from PIL import Image
from io import BytesIO


def test_custom_coordinates():
    """사용자 지정 좌표로 API 테스트"""

    print("=" * 80)
    print("🧪 사용자 지정 좌표 테스트")
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

    # 3. 사용자 지정 상대 좌표
    rel_x = 0.22157278227645405
    rel_y = 0.6070377451072398
    rel_r = 0.23062696408494462

    print(f"\n🔴 입력 좌표 (상대 좌표):")
    print(f"   x: {rel_x:.4f} ({rel_x*100:.1f}% 오른쪽)")
    print(f"   y: {rel_y:.4f} ({rel_y*100:.1f}% 위)")
    print(f"   radius: {rel_r:.4f} ({rel_r*100:.1f}% 너비)")

    # 4. 절대 좌표로 변환 (미리보기)
    abs_x = int(round(rel_x * image_width))
    abs_y = int(round((1.0 - rel_y) * image_height))
    abs_r = int(round(rel_r * image_width))

    print(f"\n📐 예상 절대 좌표:")
    print(f"   x: {abs_x}px")
    print(f"   y: {abs_y}px")
    print(f"   radius: {abs_r}px")

    # 5. 동그라미 데이터
    circles_data = [
        {
            "x": rel_x,
            "y": rel_y,
            "radius": rel_r
        }
    ]
    circles_json = json.dumps(circles_data)

    # 6. API 호출
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

        # 7. 결과 출력
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
            print(f"\n   카테고리: {circle['category'].upper()}")
            print(f"   확신도: {circle['confidence']:.2%}")
            print(f"   설명: {circle['description']}")
            print(f"\n   Gemini 추천:")
            for i, rec in enumerate(circle['gemini_recommendations'], 1):
                print(f"      {i}. {rec}")

        # 배경 무드
        if result.get('background_mood'):
            mood = result['background_mood']
            print(f"\n🎨 배경 무드:")
            print(f"   스타일: {mood['primary_style']} ({mood['category']})")
            print(f"   확신도: {mood['confidence']:.2%}")
            print(f"   색온도: {mood['warmth_score']:.2f} (0=Cool, 1=Warm)")
            print(f"   주조색: {', '.join(mood['dominant_colors'][:3])}")

        # 추천 상품
        products = result.get('recommended_products', [])
        print(f"\n🛍️  추천 상품 ({len(products)}개):")
        print("-" * 80)

        for i, product in enumerate(products, 1):
            match_score = product['match_score']
            if match_score >= 0.8:
                grade = "⭐⭐⭐"
            elif match_score >= 0.6:
                grade = "⭐⭐"
            else:
                grade = "⭐"

            print(f"\n{i}. {product['name']}")
            print(f"   ID: {product['product_id']}")
            print(f"   카테고리: {product['category']}")
            print(f"   가격: {product['price']:,}원")
            print(f"   매칭 점수: {match_score:.2%} {grade}")

            # 시뮬레이션 이미지 저장
            if product.get('simulated_image_base64'):
                try:
                    image_data = base64.b64decode(product['simulated_image_base64'])
                    pil_image = Image.open(BytesIO(image_data))

                    output_path = f"custom_simulated_{i}_{product['product_id']}.png"
                    pil_image.save(output_path)

                    file_size = len(image_data)
                    print(f"   💾 시뮬레이션: {output_path}")
                    print(f"      크기: {pil_image.size[0]}x{pil_image.size[1]}px")
                    print(f"      용량: {file_size/1024:.1f}KB")

                except Exception as e:
                    print(f"   ⚠️  이미지 저장 실패: {e}")

        # 8. 비교 이미지 생성 (입력 좌표 표시)
        print(f"\n🎯 비교 이미지 생성")
        comparison = img.copy()

        # 입력된 동그라미 위치 표시
        cv2.circle(comparison, (abs_x, abs_y), abs_r, (255, 0, 0), 3)  # 파란색
        cv2.circle(comparison, (abs_x, abs_y), 5, (255, 0, 0), -1)

        # 좌표 정보 텍스트
        cv2.putText(
            comparison,
            f"({abs_x}, {abs_y}), r={abs_r}",
            (abs_x - 60, abs_y - abs_r - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            2
        )

        cv2.imwrite('custom_circle_position.png', comparison)
        print(f"   💾 좌표 표시: custom_circle_position.png")

        print("\n" + "=" * 80)
        print("✅ 테스트 완료!")
        print("=" * 80)

        # 9. 요약
        print(f"\n📈 요약:")
        print(f"   ✅ 입력 좌표: ({rel_x:.4f}, {rel_y:.4f})")
        print(f"   ✅ 절대 좌표: ({abs_x}, {abs_y}), r={abs_r}px")
        print(f"   ✅ 카테고리: {circle['category'].upper()}")
        print(f"   ✅ 추천 상품: {len(products)}개")
        print(f"   ✅ 시뮬레이션 이미지: {len(products)}개 생성")
        print(f"\n생성된 파일:")
        print(f"   - custom_circle_position.png (입력 좌표 표시)")
        for i, product in enumerate(products, 1):
            print(f"   - custom_simulated_{i}_{product['product_id']}.png")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버 연결 실패!")
        print("   서버를 먼저 실행해주세요:")
        print("   ./start_server_with_gemini.sh")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_custom_coordinates()
