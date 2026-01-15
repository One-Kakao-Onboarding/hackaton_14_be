# Frontend 통합 가이드

## API 엔드포인트

```
POST http://localhost:8000/api/ai-interior
```

## 좌표 시스템

### 상대 좌표 (0.0 ~ 1.0)
- **원점**: 왼쪽 아래 (0, 0)
- **X축**: 0.0 (왼쪽) → 1.0 (오른쪽)
- **Y축**: 0.0 (아래) → 1.0 (위)
- **반지름**: 이미지 너비 기준으로 0.0 ~ 1.0

### 좌표 변환 예시

```javascript
// Canvas에서 사용자가 그린 동그라미 좌표
const canvasX = 300;  // Canvas X 좌표
const canvasY = 150;  // Canvas Y 좌표 (위에서부터)
const canvasRadius = 80;

// Canvas 크기
const canvasWidth = 800;
const canvasHeight = 600;

// 상대 좌표로 변환 (왼쪽 아래 기준)
const relativeX = canvasX / canvasWidth;  // 0.0 ~ 1.0
const relativeY = 1.0 - (canvasY / canvasHeight);  // Y축 반전! (위->아래를 아래->위로)
const relativeRadius = canvasRadius / canvasWidth;

// 전송할 데이터
const circles = [
  {
    x: relativeX,      // 예: 0.375
    y: relativeY,      // 예: 0.75
    radius: relativeRadius  // 예: 0.1
  }
];
```

## API 요청 예시

### JavaScript (Fetch API)

```javascript
async function analyzeInterior(imageFile, circleX, circleY, circleRadius) {
  // FormData 생성
  const formData = new FormData();

  // 1. 이미지 파일 추가
  formData.append('image', imageFile);

  // 2. 동그라미 좌표 추가 (JSON 문자열)
  const circles = [
    {
      x: circleX,        // 0.0 ~ 1.0 (왼쪽=0, 오른쪽=1)
      y: circleY,        // 0.0 ~ 1.0 (아래=0, 위=1)
      radius: circleRadius  // 0.0 ~ 1.0 (이미지 너비 기준)
    }
  ];
  formData.append('circles', JSON.stringify(circles));

  // 3. API 호출
  try {
    const response = await fetch('http://localhost:8000/api/ai-interior', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;

  } catch (error) {
    console.error('API 호출 실패:', error);
    throw error;
  }
}
```

### 전체 예시 (Canvas에서 동그라미 그리기)

```javascript
// Canvas 설정
const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');
const img = new Image();

img.onload = function() {
  // Canvas 크기를 이미지 크기에 맞춤
  canvas.width = img.width;
  canvas.height = img.height;
  ctx.drawImage(img, 0, 0);
};
img.src = 'room-image.png';

// 사용자가 동그라미를 그릴 때
let circleData = null;

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const startX = e.clientX - rect.left;
  const startY = e.clientY - rect.top;

  // ... 동그라미 그리기 로직 ...

  // 동그라미 완성 후
  circleData = {
    canvasX: startX,
    canvasY: startY,
    canvasRadius: radius
  };
});

// API 호출 버튼 클릭
document.getElementById('analyzeBtn').addEventListener('click', async () => {
  if (!circleData) {
    alert('동그라미를 먼저 그려주세요!');
    return;
  }

  // 상대 좌표로 변환
  const relativeX = circleData.canvasX / canvas.width;
  const relativeY = 1.0 - (circleData.canvasY / canvas.height);  // Y축 반전!
  const relativeRadius = circleData.canvasRadius / canvas.width;

  console.log('상대 좌표:', {
    x: relativeX,
    y: relativeY,
    radius: relativeRadius
  });

  // 이미지 파일 가져오기
  const blob = await fetch(img.src).then(r => r.blob());
  const file = new File([blob], 'room-image.png', { type: 'image/png' });

  // API 호출
  try {
    const result = await analyzeInterior(file, relativeX, relativeY, relativeRadius);
    console.log('분석 결과:', result);

    // 결과 처리
    displayResults(result);

  } catch (error) {
    console.error('분석 실패:', error);
    alert('분석 중 오류가 발생했습니다.');
  }
});
```

## API 응답 구조

```typescript
interface AIInteriorResponse {
  success: boolean;
  message: string;

  // 동그라미 영역 분석
  circle_info: {
    center_x: number;        // 절대 좌표 X (px)
    center_y: number;        // 절대 좌표 Y (px)
    radius: number;          // 절대 반지름 (px)
    category: "furniture" | "prop";  // 카테고리
    confidence: number;      // 확신도 (0.0 ~ 1.0)
    description: string;     // 설명
    gemini_recommendations: string[];  // Gemini 추천 아이템
  };

  // 배경 무드 분석
  background_mood: {
    primary_style: string;   // 스타일 키워드 (예: "white_wood")
    category: string;        // 카테고리 (예: "Natural & Cozy")
    confidence: number;      // 확신도 (0.0 ~ 1.0)
    warmth_score: number;    // 색온도 (0=Cool, 1=Warm)
    dominant_colors: string[];  // 주조색 (Hex 코드)
  };

  // 추천 상품 목록
  recommended_products: Array<{
    product_id: string;
    name: string;
    category: string;
    price: number;
    image_url: string;
    match_score: number;     // 매칭 점수 (0.0 ~ 1.0)
    match_details: {
      color_similarity: number;
      physics_similarity: number;
      style_similarity: number;
    };
    simulated_image_base64: string;  // 시뮬레이션 이미지 (base64)
  }>;
}
```

## 시뮬레이션 이미지 표시

```javascript
function displayResults(result) {
  const container = document.getElementById('productsContainer');
  container.innerHTML = '';

  result.recommended_products.forEach(product => {
    // 시뮬레이션 이미지 표시
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${product.simulated_image_base64}`;
    img.alt = product.name;

    // 상품 정보
    const info = document.createElement('div');
    info.innerHTML = `
      <h3>${product.name}</h3>
      <p>가격: ${product.price.toLocaleString()}원</p>
      <p>매칭: ${(product.match_score * 100).toFixed(1)}%</p>
    `;

    const productCard = document.createElement('div');
    productCard.className = 'product-card';
    productCard.appendChild(img);
    productCard.appendChild(info);

    container.appendChild(productCard);
  });
}
```

## 오류 처리

```javascript
try {
  const result = await analyzeInterior(file, x, y, radius);

  if (!result.success) {
    console.error('분석 실패:', result.message);
    return;
  }

  // 성공 처리

} catch (error) {
  if (error.response) {
    // HTTP 오류
    switch (error.response.status) {
      case 400:
        alert('잘못된 요청입니다. 좌표 값을 확인해주세요.');
        break;
      case 413:
        alert('이미지 파일이 너무 큽니다. (최대 10MB)');
        break;
      case 415:
        alert('지원하지 않는 이미지 형식입니다. (PNG, JPEG만 지원)');
        break;
      case 500:
        alert('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
        break;
    }
  } else {
    alert('네트워크 오류가 발생했습니다.');
  }
}
```

## 좌표 검증

```javascript
function validateCoordinates(x, y, radius) {
  // 0.0 ~ 1.0 범위 검증
  if (x < 0.0 || x > 1.0) {
    throw new Error('X 좌표는 0.0과 1.0 사이여야 합니다.');
  }
  if (y < 0.0 || y > 1.0) {
    throw new Error('Y 좌표는 0.0과 1.0 사이여야 합니다.');
  }
  if (radius < 0.0 || radius > 1.0) {
    throw new Error('반지름은 0.0과 1.0 사이여야 합니다.');
  }

  return true;
}

// 사용
try {
  validateCoordinates(relativeX, relativeY, relativeRadius);
  const result = await analyzeInterior(file, relativeX, relativeY, relativeRadius);
} catch (error) {
  console.error('검증 실패:', error.message);
}
```

## 주의사항

### ⚠️ 중요: Y축 반전

Canvas의 Y축과 API의 Y축은 반대입니다!

- **Canvas**: 위에서 아래로 (0 = 상단, height = 하단)
- **API**: 아래에서 위로 (0 = 하단, 1 = 상단)

**반드시 Y축을 반전시켜야 합니다:**

```javascript
// ❌ 잘못된 예시
const relativeY = canvasY / canvasHeight;

// ✅ 올바른 예시
const relativeY = 1.0 - (canvasY / canvasHeight);
```

### 이미지 크기

- **최대 파일 크기**: 10MB
- **권장 크기**: 2048x2048px 이하
- **지원 형식**: PNG, JPEG

### 처리 시간

- **평균 처리 시간**: 3~5초
- **타임아웃**: 120초
- CLIP 모델 로딩 시 첫 요청은 더 오래 걸릴 수 있습니다.

## 테스트

```bash
# 서버 실행
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 테스트 스크립트
python3 test_relative_coordinates.py
```
