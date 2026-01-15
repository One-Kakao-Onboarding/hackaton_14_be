"""
동그라미 위치 디버깅
"""
import cv2
import numpy as np

# 이미지 로드
image = cv2.imread('test_image.png')
height, width = image.shape[:2]

print("=" * 70)
print("🔍 동그라미 위치 분석")
print("=" * 70)
print(f"\n이미지 크기: {width}x{height}")

# 1. 원래 빨간색 원 (자동 감지된 위치)
red_x, red_y, red_r = 310, 212, 116
print(f"\n🔴 원래 빨간색 원 (자동 감지):")
print(f"   위치: ({red_x}, {red_y})")
print(f"   반지름: {red_r}px")

# 2. Frontend가 보낸 좌표
frontend_x, frontend_y, frontend_r = 243, 386, 140
print(f"\n🟢 Frontend 좌표:")
print(f"   위치: ({frontend_x}, {frontend_y})")
print(f"   반지름: {frontend_r}px")

# 3. 차이 분석
print(f"\n📊 차이:")
print(f"   X 차이: {abs(red_x - frontend_x)}px")
print(f"   Y 차이: {abs(red_y - frontend_y)}px")
print(f"   반지름 차이: {abs(red_r - frontend_r)}px")

# 4. 가능한 원인 분석
print(f"\n🤔 가능한 원인:")

# 원인 1: Y축 반전?
if abs(red_y - (height - frontend_y)) < 50:
    print(f"   ⚠️  Y축이 반전되었을 가능성 (OpenGL 스타일)")
    print(f"       Y 반전 시: {height - frontend_y}")

# 원인 2: 이미지 크기 스케일링?
scales = [0.5, 0.75, 1.5, 2.0]
for scale in scales:
    scaled_x = int(frontend_x * scale)
    scaled_y = int(frontend_y * scale)
    if abs(red_x - scaled_x) < 30 and abs(red_y - scaled_y) < 30:
        print(f"   ⚠️  {scale}배 스케일링되었을 가능성")
        print(f"       스케일 적용 시: ({scaled_x}, {scaled_y})")

# 원인 3: Frontend에서 다른 이미지 크기 사용?
common_sizes = [
    (640, 480), (800, 600), (1024, 768),
    (1280, 960), (1920, 1440)
]
for orig_w, orig_h in common_sizes:
    # Frontend 좌표를 원본 이미지 크기로 변환
    scale_x = width / orig_w
    scale_y = height / orig_h
    converted_x = int(frontend_x * scale_x)
    converted_y = int(frontend_y * scale_y)

    if abs(red_x - converted_x) < 30 and abs(red_y - converted_y) < 30:
        print(f"   ⚠️  Frontend가 {orig_w}x{orig_h} 크기를 사용했을 가능성")
        print(f"       변환 후: ({converted_x}, {converted_y})")

# 5. 시각화
result = image.copy()

# 빨간색 원 (원래 위치)
cv2.circle(result, (red_x, red_y), red_r, (0, 0, 255), 3)  # 빨간색
cv2.circle(result, (red_x, red_y), 5, (0, 0, 255), -1)
cv2.putText(result, "Original Red", (red_x - 50, red_y - red_r - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

# 초록색 원 (Frontend 좌표)
# Y 좌표가 이미지 밖인지 확인
if frontend_y < height:
    cv2.circle(result, (frontend_x, frontend_y), frontend_r, (0, 255, 0), 3)  # 초록색
    cv2.circle(result, (frontend_x, frontend_y), 5, (0, 255, 0), -1)
    cv2.putText(result, "Frontend", (frontend_x - 40, frontend_y - frontend_r - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
else:
    print(f"\n❌ Frontend Y 좌표({frontend_y})가 이미지 높이({height})를 벗어남!")

# 저장
cv2.imwrite('debug_circle_comparison.png', result)
print(f"\n💾 비교 이미지 저장: debug_circle_comparison.png")

# 6. 결론
print(f"\n" + "=" * 70)
print("📌 결론:")
print("=" * 70)

if frontend_y >= height:
    print("❌ Frontend 좌표가 이미지 밖에 있습니다!")
    print("\n가능한 원인:")
    print("1. Frontend가 다른 크기의 이미지를 사용 중")
    print("2. 좌표계가 잘못 변환됨")
    print("3. Canvas 크기와 실제 이미지 크기가 다름")
    print("\n해결 방법:")
    print("- Frontend에서 좌표를 보내기 전에 실제 이미지 크기로 변환 필요")
    print("- 예: (canvas_x / canvas_width) * image_width")
else:
    print("✅ 좌표는 이미지 안에 있지만 위치가 다릅니다.")
    print("\n가능한 원인:")
    print("1. Frontend에서 사용자가 다른 위치에 동그라미를 그림")
    print("2. 이미지 크기 스케일링 문제")
    print("3. 좌표 변환 오류")
