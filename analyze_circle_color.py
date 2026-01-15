"""
빨간색 원의 실제 색상 분석
"""
import cv2
import numpy as np


def analyze_red_circle():
    """빨간색 원의 실제 HSV 값 분석"""

    image = cv2.imread("test_image.png")
    if image is None:
        print("이미지를 로드할 수 없습니다.")
        return

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    print("="*70)
    print("🎨 빨간색 원 색상 분석")
    print("="*70)

    # 이미지 크기
    height, width = image.shape[:2]
    print(f"\n이미지 크기: {width}x{height}")

    # 원의 대략적인 위치 (이미지에서 보이는 위치)
    # 왼쪽 아래 침대 영역
    sample_points = [
        (100, 200),   # 원 중심 근처
        (80, 180),    # 원 위쪽
        (120, 220),   # 원 아래쪽
        (90, 190),    # 원 왼쪽
        (110, 210)    # 원 오른쪽
    ]

    print("\n샘플링 포인트:")
    for i, (x, y) in enumerate(sample_points, 1):
        if 0 <= x < width and 0 <= y < height:
            bgr = image[y, x]
            hsv_val = hsv[y, x]
            print(f"{i}. 위치 ({x}, {y})")
            print(f"   BGR: {bgr}")
            print(f"   HSV: {hsv_val}")
        else:
            print(f"{i}. 위치 ({x}, {y}) - 범위 밖")

    # 전체 이미지에서 빨간색 계열 픽셀 찾기
    print("\n🔍 전체 이미지에서 빨간색 계열 픽셀 검색:")

    # 더 넓은 빨간색 범위
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    red_pixels = np.count_nonzero(red_mask)
    total_pixels = width * height

    print(f"빨간색 픽셀: {red_pixels:,} / {total_pixels:,} ({red_pixels/total_pixels*100:.2f}%)")

    if red_pixels > 0:
        # 빨간색 영역 저장
        red_only = cv2.bitwise_and(image, image, mask=red_mask)
        cv2.imwrite("debug_red_mask.png", red_mask)
        cv2.imwrite("debug_red_pixels.png", red_only)
        print(f"\n💾 디버그 이미지 저장:")
        print(f"   - debug_red_mask.png (빨간색 마스크)")
        print(f"   - debug_red_pixels.png (빨간색 픽셀만)")

        # 윤곽선 찾기
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"\n발견된 빨간색 윤곽선: {len(contours)}개")

        if contours:
            # 큰 윤곽선들 분석
            large_contours = [c for c in contours if cv2.contourArea(c) > 100]
            print(f"큰 윤곽선 (면적 > 100px²): {len(large_contours)}개")

            for i, contour in enumerate(large_contours[:5], 1):
                area = cv2.contourArea(contour)
                (x, y), radius = cv2.minEnclosingCircle(contour)
                print(f"   {i}. 면적: {area:.0f}px², 중심: ({int(x)}, {int(y)}), 반지름: {radius:.0f}px")
    else:
        print("⚠️  빨간색 픽셀을 찾지 못했습니다.")
        print("     이미지에 빨간색 원이 없거나, 색상 범위가 다를 수 있습니다.")


if __name__ == "__main__":
    analyze_red_circle()
