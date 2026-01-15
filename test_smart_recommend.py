"""
스마트 추천 API 테스트 스크립트
test_image.png를 사용하여 실제 테스트
"""
import requests
import base64
import json


def test_smart_recommend():
    """스마트 추천 API 테스트"""

    print("="*70)
    print("🧪 스마트 추천 API 테스트")
    print("="*70)

    # 1. test_image.png 로드
    image_path = "test_image.png"
    print(f"\n📁 이미지 로드: {image_path}")

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        print(f"✅ 이미지 로드 성공 ({len(image_bytes)} bytes)")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return

    # 2. API 호출
    url = "http://localhost:8000/api/v1/smart-recommend"
    payload = {
        "image_base64": image_base64,
        "top_k": 5,
        "matching_strategy": "weighted"
    }

    print(f"\n🚀 API 호출: {url}")
    print(f"   Top-K: {payload['top_k']}")
    print(f"   Strategy: {payload['matching_strategy']}")

    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"\n📡 응답 상태: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ 에러: {response.text}")
            return

        result = response.json()

        # 3. 결과 출력
        print("\n" + "="*70)
        print("📊 분석 결과")
        print("="*70)

        print(f"\n✅ 처리 성공: {result['success']}")
        print(f"⏱️  처리 시간: {result['processing_time_ms']:.2f}ms")
        print(f"💬 메시지: {result['message']}")

        # 빨간색 원 감지 결과
        if result['circle_detected']:
            circle = result['circle_info']
            print(f"\n🔴 빨간색 원 감지됨:")
            print(f"   위치: ({circle['center_x']}, {circle['center_y']})")
            print(f"   반지름: {circle['radius']}px")
            print(f"   카테고리: {circle['category'].upper()}")
            print(f"   확신도: {circle['confidence']:.2%}")
            print(f"   설명: {circle['description']}")
            print(f"\n   Gemini 추천:")
            for i, rec in enumerate(circle['gemini_recommendations'], 1):
                print(f"      {i}. {rec}")
        else:
            print("\n⚠️  빨간색 원이 감지되지 않았습니다.")

        # 배경 무드 분석 결과
        if result['background_mood']:
            mood = result['background_mood']
            print(f"\n🎨 배경 무드:")
            print(f"   스타일: {mood['primary_style']}")
            print(f"   색온도: {mood['warmth_score']:.2f} (0=Cool, 1=Warm)")
            print(f"   주조색: {', '.join(mood['dominant_colors'])}")

        # 추천 상품
        products = result['recommended_products']
        print(f"\n🛍️  추천 상품 ({len(products)}개):")
        print("-"*70)

        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name']} (ID: {product['product_id']})")
            print(f"   카테고리: {product['category']}")
            print(f"   가격: {product['price']:,}원")
            print(f"   매칭 점수: {product['match_score']:.2%} ({product['match_details']['overall_match']})")
            print(f"   상세:")
            print(f"      - 색상 유사도: {product['match_details']['color_similarity']:.2%}")
            print(f"      - 물리 유사도: {product['match_details']['physics_similarity']:.2%}")
            print(f"      - 스타일 유사도: {product['match_details']['style_similarity']:.2%}")

        print("\n" + "="*70)
        print("✅ 테스트 완료!")
        print("="*70)

        # 4. JSON 파일로 저장
        output_file = "smart_recommend_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과 저장됨: {output_file}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버 연결 실패!")
        print("   서버가 실행 중인지 확인하세요:")
        print("   python app/main.py")
    except requests.exceptions.Timeout:
        print("\n❌ 요청 시간 초과 (60초)")
        print("   이미지 처리가 너무 오래 걸립니다.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")


if __name__ == "__main__":
    test_smart_recommend()
