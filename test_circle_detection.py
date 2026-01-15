"""
빨간색 원 감지 독립 테스트
FastAPI 서버 없이 직접 테스트
"""
import sys
sys.path.insert(0, '.')

import cv2
import numpy as np
from app.core.circle_detector import CircleDetector


def test_circle_detection():
    """빨간색 원 감지 테스트"""

    print("="*70)
    print("🔴 빨간색 원 감지 테스트")
    print("="*70)

    # 1. 이미지 로드
    image_path = "test_image.png"
    print(f"\n📁 이미지 로드: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 이미지를 로드할 수 없습니다: {image_path}")
        return

    print(f"✅ 이미지 크기: {image.shape[1]}x{image.shape[0]}")

    # 2. 빨간색 원 감지
    detector = CircleDetector()
    print("\n🔍 빨간색 원 감지 중...")

    result = detector.detect_red_circle(image)

    if result is None:
        print("❌ 빨간색 원을 감지하지 못했습니다.")
        return

    center_x, center_y, radius = result
    print(f"✅ 빨간색 원 감지 성공!")
    print(f"   중심: ({center_x}, {center_y})")
    print(f"   반지름: {radius}px")

    # 3. 원 영역 추출
    print("\n✂️  원 영역 추출 중...")
    region = detector.extract_circle_region(image, center_x, center_y, radius)
    print(f"✅ 추출된 영역 크기: {region.shape[1]}x{region.shape[0]}")

    # 4. 빨간색 원 제거 (배경용)
    print("\n🧹 빨간색 원 제거 중...")
    clean_bg = detector.remove_red_circle(image)
    print(f"✅ 원 제거 완료")

    # 5. 시각화
    print("\n🎨 결과 시각화 중...")
    visualized = detector.visualize_detection(image, center_x, center_y, radius)

    # 결과 저장
    cv2.imwrite("result_detected_circle.png", visualized)
    cv2.imwrite("result_extracted_region.png", region)
    cv2.imwrite("result_clean_background.png", clean_bg)

    print(f"\n💾 결과 저장됨:")
    print(f"   - result_detected_circle.png (감지된 원 표시)")
    print(f"   - result_extracted_region.png (추출된 영역)")
    print(f"   - result_clean_background.png (원 제거된 배경)")

    print("\n" + "="*70)
    print("✅ 테스트 완료!")
    print("="*70)

    # 6. 영역 크기 기반 간단한 분류
    region_area = region.shape[0] * region.shape[1]
    print(f"\n🤖 간단한 분류:")
    print(f"   영역 면적: {region_area:,}px²")

    if region_area > 100000:
        category = "가구 (furniture)"
        print(f"   → 큰 영역이므로 '{category}'로 추정됩니다.")
        print(f"   추천: 침대, 소파, 옷장, 책상 등")
    else:
        category = "소품 (prop)"
        print(f"   → 작은 영역이므로 '{category}'로 추정됩니다.")
        print(f"   추천: 사이드 테이블, 조명, 화분, 쿠션 등")


if __name__ == "__main__":
    try:
        test_circle_detection()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
