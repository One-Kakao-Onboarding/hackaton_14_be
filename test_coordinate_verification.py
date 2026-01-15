"""
좌표 변환 검증 스크립트
Frontend 좌표계 vs OpenCV 좌표계
"""
import cv2
import numpy as np

# 테스트 이미지
image_path = "test_image2.png"

# 사용자가 준 좌표 (Frontend 좌표계)
x_relative = 0.7215782000661312
y_relative = 0.44191157878357606
radius_relative = 0.09512911389498678

# 이미지 읽기
img = cv2.imread(image_path)
if img is None:
    print(f"❌ 이미지를 읽을 수 없습니다: {image_path}")
    exit(1)

height, width = img.shape[:2]
print(f"📐 이미지 크기: {width}x{height}")
print()

# 좌표 변환
center_x = int(round(x_relative * width))
center_y = int(round((1.0 - y_relative) * height))  # Y축 반전
radius = int(round(radius_relative * width))

print(f"📍 Frontend 좌표계 (왼쪽 아래가 원점):")
print(f"   x = {x_relative:.4f} (왼쪽=0, 오른쪽=1)")
print(f"   y = {y_relative:.4f} (아래=0, 위=1)")
print(f"   r = {radius_relative:.4f}")
print()

print(f"🔄 OpenCV 좌표계로 변환 (왼쪽 위가 원점):")
print(f"   center_x = {center_x}px (왼쪽에서 {center_x}px = {center_x/width*100:.1f}%)")
print(f"   center_y = {center_y}px (위에서 {center_y}px = {center_y/height*100:.1f}%)")
print(f"   radius = {radius}px")
print()

# Frontend 관점에서 y 위치 확인
print(f"🧭 Frontend 관점:")
print(f"   y={y_relative:.4f} → 아래에서 {y_relative*100:.1f}% 위치")
print(f"   즉, 위에서는 {(1-y_relative)*100:.1f}% 위치")
print()

print(f"🧭 OpenCV 관점:")
print(f"   center_y={center_y} → 위에서 {center_y}px = {center_y/height*100:.1f}%")
print()

# 시각화 1: OpenCV 좌표계
img_opencv = img.copy()
cv2.circle(img_opencv, (center_x, center_y), radius, (0, 255, 255), 3)
cv2.circle(img_opencv, (center_x, center_y), 5, (0, 0, 255), -1)
cv2.putText(img_opencv, f"OpenCV: ({center_x}, {center_y})",
            (center_x + 10, center_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
cv2.imwrite("coordinate_check_opencv.png", img_opencv)
print("✅ OpenCV 좌표계 시각화 저장: coordinate_check_opencv.png")

# 시각화 2: 이미지에 격자 추가 (위치 파악용)
img_grid = img.copy()
# 수직선 (10% 간격)
for i in range(11):
    x = int(i * width / 10)
    cv2.line(img_grid, (x, 0), (x, height), (200, 200, 200), 1)
    cv2.putText(img_grid, f"{i*10}%", (x+5, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

# 수평선 (10% 간격)
for i in range(11):
    y = int(i * height / 10)
    cv2.line(img_grid, (0, y), (width, y), (200, 200, 200), 1)
    cv2.putText(img_grid, f"{i*10}%", (10, y-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

# 동그라미 표시
cv2.circle(img_grid, (center_x, center_y), radius, (0, 255, 255), 3)
cv2.circle(img_grid, (center_x, center_y), 5, (0, 0, 255), -1)
cv2.putText(img_grid, f"({center_x/width*100:.1f}%, {center_y/height*100:.1f}%)",
            (center_x + 10, center_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

cv2.imwrite("coordinate_check_grid.png", img_grid)
print("✅ 격자 시각화 저장: coordinate_check_grid.png")

# 주요 위치 표시 (참고용)
print()
print("📌 주요 랜드마크 (대략적인 위치):")
print("   - 안경 쓴 사람 그림: 왼쪽 중앙 벽 (~25%, ~40%)")
print("   - 파란색 수납장: 오른쪽 중앙 (~70-80%, ~50-60%)")
print("   - 핑크색 콘솔: 왼쪽 (~20%, ~40%)")
print()
print(f"👉 당신이 지정한 위치: ({center_x/width*100:.1f}%, {center_y/height*100:.1f}%)")
print(f"   이것은 파란색 수납장 영역입니다." if 65 < center_x/width*100 < 85 else "")
