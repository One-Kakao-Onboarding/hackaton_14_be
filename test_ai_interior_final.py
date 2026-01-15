"""
AI 인테리어 API 최종 테스트
Frontend와 동일한 형식으로 테스트
"""
import requests
import json
import base64
from PIL import Image
from io import BytesIO


def test_ai_interior_final():
    """AI 인테리어 API 최종 테스트 - Frontend 형식"""

    print("=" * 80)
    print("🧪 AI 인테리어 API 최종 테스트 (Frontend 형식)")
    print("=" * 80)

    # 1. 테스트 이미지 로드 (Binary)
    image_path = "test_image.png"
    print(f"\n📁 이미지 로드: {image_path}")

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"✅ 이미지 로드 성공 ({len(image_bytes):,} bytes)")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return

    # 2. 동그라미 좌표 (Frontend에서 제공하는 실제 좌표)
    circles_data = [
        {
            "x": 243.17211744078804,
            "y": 385.745104526196,
            "radius": 139.55590459787004
        }
    ]
    circles_json = json.dumps(circles_data)

    print(f"\n🔴 동그라미 좌표:")
    print(f"   x: {circles_data[0]['x']:.2f}")
    print(f"   y: {circles_data[0]['y']:.2f}")
    print(f"   radius: {circles_data[0]['radius']:.2f}")

    # 3. API 호출 (multipart/form-data)
    url = "http://localhost:8000/api/ai-interior"

    # FormData 구성
    files = {
        'image': ('test_image.png', image_bytes, 'image/png')
    }
    data = {
        'circles': circles_json  # JSON 문자열
    }

    print(f"\n🚀 API 호출: {url}")
    print(f"   Content-Type: multipart/form-data")
    print(f"   - image: binary ({len(image_bytes):,} bytes)")
    print(f"   - circles: {circles_json}")

    # 4. API 호출
    try:
        response = requests.post(url, files=files, data=data, timeout=120)
        print(f"\n📡 응답 상태: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ 에러: {response.text}")
            return

        result = response.json()

        # 5. 결과 출력
        print("\n" + "=" * 80)
        print("📊 분석 결과")
        print("=" * 80)

        print(f"\n✅ 처리 성공: {result['success']}")
        print(f"💬 메시지: {result['message']}")

        # 동그라미 영역 정보
        if result.get('circle_info'):
            circle = result['circle_info']
            print(f"\n🔴 동그라미 영역 분석:")
            print(f"   입력 좌표: ({circles_data[0]['x']:.2f}, {circles_data[0]['y']:.2f})")
            print(f"   처리 좌표: ({circle['center_x']}, {circle['center_y']})")
            print(f"   반지름: {circle['radius']}px")
            print(f"   카테고리: {circle['category'].upper()}")
            print(f"   확신도: {circle['confidence']:.2%}")
            print(f"   설명: {circle['description']}")
            print(f"\n   Gemini 추천:")
            for i, rec in enumerate(circle['gemini_recommendations'], 1):
                print(f"      {i}. {rec}")

        # 배경 무드
        if result.get('background_mood'):
            mood = result['background_mood']
            print(f"\n🎨 배경 무드 분석:")
            print(f"   스타일: {mood['primary_style']} ({mood['category']})")
            print(f"   확신도: {mood['confidence']:.2%}")
            print(f"   색온도: {mood['warmth_score']:.2f} (0=Cool, 1=Warm)")
            print(f"   주조색: {', '.join(mood['dominant_colors'])}")

        # 추천 상품
        products = result.get('recommended_products', [])
        print(f"\n🛍️  추천 상품 ({len(products)}개):")
        print("-" * 80)

        for i, product in enumerate(products, 1):
            match_score = product['match_score']
            if match_score >= 0.8:
                grade = "⭐⭐⭐ (Excellent)"
            elif match_score >= 0.6:
                grade = "⭐⭐ (Good)"
            else:
                grade = "⭐ (Fair)"

            print(f"\n{i}. {product['name']}")
            print(f"   ID: {product['product_id']}")
            print(f"   카테고리: {product['category']}")
            print(f"   가격: {product['price']:,}원")
            print(f"   매칭 점수: {match_score:.2%} {grade}")
            print(f"   상세:")
            print(f"      - 색상 유사도: {product['match_details']['color_similarity']:.2%}")
            print(f"      - 물리 유사도: {product['match_details']['physics_similarity']:.2%}")
            print(f"      - 스타일 유사도: {product['match_details']['style_similarity']:.2%}")

            # 시뮬레이션 이미지 저장
            if product.get('simulated_image_base64'):
                try:
                    image_data = base64.b64decode(product['simulated_image_base64'])
                    pil_image = Image.open(BytesIO(image_data))
                    output_path = f"final_simulated_{product['product_id']}.png"
                    pil_image.save(output_path)

                    # 이미지 크기 정보
                    print(f"      💾 시뮬레이션 이미지: {output_path}")
                    print(f"         크기: {pil_image.size[0]}x{pil_image.size[1]}px")
                    print(f"         파일: {len(image_data):,} bytes")
                except Exception as e:
                    print(f"      ⚠️  시뮬레이션 이미지 디코딩 실패: {e}")

        print("\n" + "=" * 80)
        print("✅ 최종 테스트 완료!")
        print("=" * 80)

        # 6. JSON 파일로 저장
        output_file = "final_api_result.json"

        # base64 이미지는 너무 크므로 요약
        result_summary = result.copy()
        if 'recommended_products' in result_summary:
            for product in result_summary['recommended_products']:
                if 'simulated_image_base64' in product:
                    base64_len = len(product['simulated_image_base64'])
                    product['simulated_image_base64'] = f"[BASE64 IMAGE DATA - {base64_len:,} chars]"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과 저장됨: {output_file}")

        # 통계 요약
        print(f"\n📈 통계:")
        print(f"   - 분석된 영역: 1개")
        print(f"   - 추천 상품: {len(products)}개")
        print(f"   - 시뮬레이션 이미지: {len(products)}개")
        print(f"   - 최고 매칭 점수: {max([p['match_score'] for p in products]):.2%}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버 연결 실패!")
        print("   서버를 먼저 실행해주세요:")
        print("   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except requests.exceptions.Timeout:
        print("\n❌ 요청 시간 초과 (120초)")
        print("   이미지 처리가 너무 오래 걸립니다.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ai_interior_final()
