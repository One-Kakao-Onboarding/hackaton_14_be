"""
특정 좌표로 AI Interior API 테스트
"""
import requests
import time
import json
from pathlib import Path
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

# API 엔드포인트
API_URL = "http://localhost:8000/api/ai-interior"

# 테스트 이미지
TEST_IMAGE = "test_image1.jpeg"

# 테스트할 좌표 (바닥 중앙 영역)
TEST_CIRCLE = {
    "x": 0.5,
    "y": 0.25,
    "radius": 0.1
}

def visualize_circle(image_path, circle_data):
    """
    이미지에 동그라미를 그려서 시각화
    """
    # 이미지 읽기
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 이미지를 읽을 수 없습니다: {image_path}")
        return None

    height, width = img.shape[:2]

    # 상대 좌표를 절대 좌표로 변환
    # Frontend: 왼쪽 아래가 (0, 0), 오른쪽 위가 (1, 1)
    # OpenCV: 왼쪽 위가 (0, 0), 오른쪽 아래가 (width, height)
    center_x = int(round(circle_data['x'] * width))
    center_y = int(round((1.0 - circle_data['y']) * height))  # Y축 반전
    radius = int(round(circle_data['radius'] * width))

    print(f"\n📍 동그라미 좌표:")
    print(f"   상대 좌표: x={circle_data['x']:.4f}, y={circle_data['y']:.4f}, r={circle_data['radius']:.4f}")
    print(f"   이미지 크기: {width}x{height}px")
    print(f"   절대 좌표: x={center_x}, y={center_y}, r={radius}px")

    # 동그라미 그리기
    overlay = img.copy()
    cv2.circle(overlay, (center_x, center_y), radius, (0, 255, 255), 3)  # 노란색 테두리
    cv2.circle(overlay, (center_x, center_y), radius, (0, 255, 255), -1)  # 반투명 채우기
    img_with_circle = cv2.addWeighted(overlay, 0.3, img, 0.7, 0)

    # 중심점 표시
    cv2.circle(img_with_circle, (center_x, center_y), 5, (0, 0, 255), -1)

    # 좌표 텍스트 추가
    text = f"({circle_data['x']:.2f}, {circle_data['y']:.2f})"
    cv2.putText(img_with_circle, text, (center_x + 10, center_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # 저장
    output_path = "test_circle_visualization.png"
    cv2.imwrite(output_path, img_with_circle)
    print(f"✅ 동그라미 시각화 저장: {output_path}")

    return output_path

def test_api_with_coordinate():
    """특정 좌표로 API 테스트"""

    if not Path(TEST_IMAGE).exists():
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {TEST_IMAGE}")
        return

    print("=" * 80)
    print("🚀 특정 좌표로 AI Interior API 테스트")
    print("=" * 80)

    # 동그라미 시각화
    visualize_circle(TEST_IMAGE, TEST_CIRCLE)

    # 테스트 이미지 로드
    with open(TEST_IMAGE, 'rb') as f:
        image_data = f.read()

    # API 요청 데이터 준비
    circles_data = [TEST_CIRCLE]

    files = {
        'image': ('test_image.png', image_data, 'image/png')
    }
    data = {
        'circles': json.dumps(circles_data)
    }

    # 속도 측정 시작
    print(f"\n📤 API 요청 전송 중...")
    print(f"   이미지: {TEST_IMAGE} ({len(image_data)/1024:.1f}KB)")
    print(f"   동그라미: x={TEST_CIRCLE['x']:.4f}, y={TEST_CIRCLE['y']:.4f}, r={TEST_CIRCLE['radius']:.4f}")

    start_time = time.time()

    try:
        response = requests.post(API_URL, files=files, data=data, timeout=120)

        # 전체 응답 시간
        total_time = (time.time() - start_time) * 1000

        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return

        result = response.json()

        print(f"\n✅ API 응답 성공!")
        print(f"   전체 소요 시간: {total_time:.0f}ms ({total_time/1000:.2f}초)")

        # 응답 데이터 분석
        if not result.get('success'):
            print(f"❌ API 실패: {result.get('message')}")
            return

        # 배경 무드 정보
        bg_mood = result.get('background_mood', {})
        print(f"\n🎨 배경 무드 분석:")
        print(f"   스타일: {bg_mood.get('primary_style')} ({bg_mood.get('confidence', 0)*100:.1f}%)")
        print(f"   카테고리: {bg_mood.get('category')}")
        print(f"   따뜻함: {bg_mood.get('warmth_score', 0)*100:.0f}/100")
        print(f"   주요 색상: {', '.join(bg_mood.get('dominant_colors', []))}")

        # 동그라미 영역 정보
        circle_info = result.get('circle_info', {})
        print(f"\n📍 동그라미 영역 분석:")
        print(f"   카테고리: {circle_info.get('category')}")
        print(f"   신뢰도: {circle_info.get('confidence', 0)*100:.1f}%")
        print(f"   설명: {circle_info.get('description')}")
        print(f"   Gemini 추천: {', '.join(circle_info.get('gemini_recommendations', []))}")

        # 추천 상품
        products = result.get('recommended_products', [])
        print(f"\n🛍️  추천 상품: {len(products)}개")
        print("=" * 80)

        if not products:
            print("   추천 상품이 없습니다.")
            return

        for idx, product in enumerate(products, 1):
            name = product.get('name', 'Unknown')
            match_score = product.get('match_score', 0)
            price = product.get('price', 0)

            print(f"\n{idx}. {name}")
            print(f"   가격: {price:,}원")
            print(f"   매칭 점수: {match_score:.4f}")

            # 상세 매칭 정보
            details = product.get('match_details', {})
            print(f"   세부 점수:")
            print(f"     - 색상 유사도:   {details.get('color_similarity', 0):.4f}")
            print(f"     - 물리적 유사도: {details.get('physics_similarity', 0):.4f}")
            print(f"     - 스타일 유사도: {details.get('style_similarity', 0):.4f}")

            # 시뮬레이션 이미지 저장
            if product.get('simulated_image_base64'):
                sim_base64 = product['simulated_image_base64']
                sim_size = len(sim_base64) / 1024
                print(f"     - 시뮬레이션 이미지: {sim_size:.1f}KB")

                # Base64 -> 이미지 파일로 저장
                image_data = base64.b64decode(sim_base64)
                output_file = f"simulated_result_{idx}.png"

                with open(output_file, 'wb') as f:
                    f.write(image_data)

                print(f"     - 저장됨: {output_file}")

        print("=" * 80)

        # 결과를 파일로 저장
        output_file = "api_test_result_specific.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # simulated_image_base64는 너무 커서 제외
            result_without_images = {
                'success': result['success'],
                'message': result.get('message'),
                'total_time_ms': total_time,
                'test_circle': TEST_CIRCLE,
                'circle_info': result.get('circle_info'),
                'background_mood': result.get('background_mood'),
                'recommended_products': [
                    {k: v for k, v in p.items() if k != 'simulated_image_base64'}
                    for p in products
                ]
            }
            json.dump(result_without_images, f, ensure_ascii=False, indent=2)

        print(f"\n💾 상세 결과 저장: {output_file}")
        print(f"\n🎉 테스트 완료!")

    except requests.exceptions.Timeout:
        print(f"❌ API 타임아웃 (120초 초과)")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_with_coordinate()
