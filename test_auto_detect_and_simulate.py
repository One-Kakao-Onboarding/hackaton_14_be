"""
빨간색 원 자동 감지 → 상대 좌표 변환 → API 호출 → 시뮬레이션 이미지 생성
"""
import sys
sys.path.insert(0, '.')

import cv2
import numpy as np
import requests
import json
import base64
from PIL import Image
from io import BytesIO
from app.core.circle_detector import CircleDetector


def auto_detect_and_simulate():
    """빨간색 원 자동 감지 후 API 호출"""

    print("=" * 80)
    print("🤖 빨간색 원 자동 감지 & 시뮬레이션")
    print("=" * 80)

    # 1. 이미지 로드
    image_path = "test_image.png"
    print(f"\n📁 Step 1: 이미지 로드 ({image_path})")

    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 이미지를 로드할 수 없습니다: {image_path}")
        return

    image_height, image_width = image.shape[:2]
    print(f"✅ 이미지 크기: {image_width}x{image_height}")

    # 2. 빨간색 원 자동 감지
    print(f"\n🔴 Step 2: 빨간색 원 자동 감지")
    detector = CircleDetector()
    result = detector.detect_red_circle(image)

    if result is None:
        print("❌ 빨간색 원을 감지하지 못했습니다.")
        return

    abs_x, abs_y, abs_r = result
    print(f"✅ 원 감지 성공!")
    print(f"   절대 좌표: ({abs_x}, {abs_y}), 반지름 {abs_r}px")

    # 3. 상대 좌표로 변환
    print(f"\n📐 Step 3: 상대 좌표로 변환")
    print(f"   좌표 시스템: 왼쪽 아래 (0, 0)")

    rel_x = abs_x / image_width
    rel_y = 1.0 - (abs_y / image_height)  # Y축 반전
    rel_r = abs_r / image_width

    print(f"   상대 좌표: ({rel_x:.4f}, {rel_y:.4f}), 반지름 {rel_r:.4f}")
    print(f"   해석:")
    print(f"      X: {rel_x*100:.1f}% 오른쪽")
    print(f"      Y: {rel_y*100:.1f}% 위")
    print(f"      반지름: 이미지 너비의 {rel_r*100:.1f}%")

    # 4. 이미지 파일 읽기
    print(f"\n📤 Step 4: API 호출 준비")
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    # 5. API 호출
    url = "http://localhost:8000/api/ai-interior"
    circles_data = [
        {
            "x": rel_x,
            "y": rel_y,
            "radius": rel_r
        }
    ]

    files = {
        'image': ('test_image.png', image_bytes, 'image/png')
    }
    data = {
        'circles': json.dumps(circles_data)
    }

    print(f"🚀 API 호출: {url}")
    print(f"   전송 데이터: {json.dumps(circles_data, indent=6)}")

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
            print(f"\n🔴 동그라미 영역:")
            print(f"   카테고리: {circle['category'].upper()}")
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

        # 7. 시뮬레이션 이미지 저장
        print(f"\n🖼️  Step 5: 시뮬레이션 이미지 저장")
        products = result.get('recommended_products', [])
        print(f"   추천 상품: {len(products)}개")
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

                    output_path = f"auto_simulated_{i}_{product['product_id']}.png"
                    pil_image.save(output_path)

                    file_size = len(image_data)
                    print(f"   💾 시뮬레이션 이미지: {output_path}")
                    print(f"      크기: {pil_image.size[0]}x{pil_image.size[1]}px")
                    print(f"      용량: {file_size/1024:.1f}KB")

                except Exception as e:
                    print(f"   ⚠️  이미지 저장 실패: {e}")

        # 8. 원본 이미지에 빨간 원 표시 (비교용)
        print(f"\n🎯 Step 6: 비교 이미지 생성")
        comparison = image.copy()

        # 감지된 빨간 원 표시
        cv2.circle(comparison, (abs_x, abs_y), abs_r, (0, 0, 255), 3)
        cv2.circle(comparison, (abs_x, abs_y), 5, (0, 0, 255), -1)

        # 좌표 정보 텍스트
        cv2.putText(
            comparison,
            f"({abs_x}, {abs_y}), r={abs_r}",
            (abs_x - 60, abs_y - abs_r - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2
        )

        cv2.imwrite('auto_detected_circle.png', comparison)
        print(f"   💾 감지된 원 표시: auto_detected_circle.png")

        print("\n" + "=" * 80)
        print("✅ 전체 프로세스 완료!")
        print("=" * 80)

        # 9. 요약
        print(f"\n📈 요약:")
        print(f"   ✅ 빨간색 원 감지: 성공")
        print(f"   ✅ 좌표 변환: ({rel_x:.4f}, {rel_y:.4f})")
        print(f"   ✅ API 호출: 성공")
        print(f"   ✅ 추천 상품: {len(products)}개")
        print(f"   ✅ 시뮬레이션 이미지: {len(products)}개 생성")
        print(f"\n생성된 파일:")
        print(f"   - auto_detected_circle.png (감지된 원 표시)")
        for i, product in enumerate(products, 1):
            print(f"   - auto_simulated_{i}_{product['product_id']}.png")

    except requests.exceptions.ConnectionError:
        print("\n❌ 서버 연결 실패!")
        print("   서버를 먼저 실행해주세요:")
        print("   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    auto_detect_and_simulate()
