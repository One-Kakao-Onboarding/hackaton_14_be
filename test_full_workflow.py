"""
전체 워크플로우 통합 테스트
빨간색 원 감지 → Gemini 분석 (Mock) → 배경 무드 분석 → 상품 추천
"""
import sys
sys.path.insert(0, '.')

import cv2
import json
from app.core.circle_detector import CircleDetector
from app.core.gemini_analyzer import GeminiAnalyzer
from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


# Mock 상품 데이터
MOCK_FURNITURE_PRODUCTS = [
    {
        'product_id': 'furn_001',
        'name': '우드 침대 프레임 (킹 사이즈)',
        'category': 'furniture',
        'price': 450000,
        'image_url': 'https://example.com/bed1.jpg',
        'mood_vector': [0.75, 0.60, 0.50, 0.85, 0.20, 0.30] + [0.80, 0.10, 0.05, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.00],
        'primary_keyword': 'natural_wood',
    },
    {
        'product_id': 'furn_002',
        'name': '화이트 옷장 (3도어)',
        'category': 'furniture',
        'price': 680000,
        'image_url': 'https://example.com/closet1.jpg',
        'mood_vector': [0.70, 0.55, 0.45, 0.90, 0.15, 0.25] + [0.15, 0.85, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        'primary_keyword': 'white_wood',
    },
]

MOCK_PROP_PRODUCTS = [
    {
        'product_id': 'prop_001',
        'name': '우드 사이드 테이블',
        'category': 'decor',
        'price': 85000,
        'image_url': 'https://example.com/table1.jpg',
        'mood_vector': [0.78, 0.62, 0.48, 0.88, 0.18, 0.28] + [0.82, 0.08, 0.04, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.01],
        'primary_keyword': 'natural_wood',
    },
    {
        'product_id': 'prop_002',
        'name': '미니멀 스탠드 조명',
        'category': 'lighting',
        'price': 65000,
        'image_url': 'https://example.com/lamp1.jpg',
        'mood_vector': [0.72, 0.58, 0.45, 0.85, 0.22, 0.30] + [0.25, 0.65, 0.05, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01],
        'primary_keyword': 'white_wood',
    },
    {
        'product_id': 'prop_003',
        'name': '패브릭 쿠션 세트 (베이지)',
        'category': 'textile',
        'price': 45000,
        'image_url': 'https://example.com/cushion1.jpg',
        'mood_vector': [0.80, 0.60, 0.50, 0.95, 0.10, 0.20] + [0.40, 0.30, 0.10, 0.15, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.00, 0.01],
        'primary_keyword': 'cozy',
    },
]


def test_full_workflow():
    """전체 워크플로우 테스트"""

    print("="*80)
    print("🚀 전체 워크플로우 통합 테스트")
    print("="*80)

    # 1. 이미지 로드
    image_path = "test_image.png"
    print(f"\n📁 Step 1: 이미지 로드 ({image_path})")
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ 이미지를 로드할 수 없습니다: {image_path}")
        return

    print(f"✅ 이미지 크기: {image.shape[1]}x{image.shape[0]}")

    # 2. 빨간색 원 감지
    print(f"\n🔴 Step 2: 빨간색 원 감지")
    circle_detector = CircleDetector()
    circle_result = circle_detector.detect_red_circle(image)

    if not circle_result:
        print("❌ 빨간색 원을 감지하지 못했습니다.")
        return

    center_x, center_y, radius = circle_result
    print(f"✅ 원 감지 성공!")
    print(f"   중심: ({center_x}, {center_y})")
    print(f"   반지름: {radius}px")

    # 3. 원 영역 추출
    region_image = circle_detector.extract_circle_region(image, center_x, center_y, radius)
    region_area = region_image.shape[0] * region_image.shape[1]
    print(f"   영역 크기: {region_image.shape[1]}x{region_image.shape[0]} ({region_area:,}px²)")

    # 4. Gemini 분석 (Mock)
    print(f"\n🤖 Step 3: Gemini로 영역 분석 (Mock)")
    gemini_analyzer = GeminiAnalyzer()  # API 키 없으면 자동으로 Mock
    gemini_result = gemini_analyzer.analyze_region(region_image)

    print(f"✅ 분석 완료!")
    print(f"   카테고리: {gemini_result['category'].upper()}")
    print(f"   확신도: {gemini_result['confidence']:.2%}")
    print(f"   설명: {gemini_result['description']}")
    print(f"   Gemini 추천:")
    for i, rec in enumerate(gemini_result['recommendations'], 1):
        print(f"      {i}. {rec}")

    # 5. 배경 무드 분석 (빨간색 원 제거)
    print(f"\n🎨 Step 4: 배경 무드 분석")
    clean_bg = circle_detector.remove_red_circle(image)
    mood_analyzer = MoodAnalyzer()

    print(f"   분석 중... (CLIP 모델 로딩에 시간이 걸릴 수 있습니다)")
    bg_analysis = mood_analyzer.analyze(
        image=clean_bg,
        image_type='background',
        image_id='test_workflow'
    )

    bg_style = bg_analysis['analysis_result']['style']
    bg_colors = bg_analysis['analysis_result']['colors']
    bg_physics = bg_analysis['analysis_result']['physics']

    print(f"✅ 배경 무드 분석 완료!")
    print(f"   스타일: {bg_style['primary_keyword']} ({bg_style['category']})")
    print(f"   확신도: {bg_style['primary_score']:.2%}")
    print(f"   색온도: {bg_colors['warmth_score']:.2f} (0=Cool, 1=Warm)")
    print(f"   주조색: {', '.join(bg_colors['dominant_hex'][:2])}")
    print(f"   직선성: {bg_physics.get('linearity', 0):.2f}")
    print(f"   광택도: {bg_physics['glossiness']:.2f}")

    # 6. Mood Vector 생성
    print(f"\n🧮 Step 5: Mood Vector 생성 (20차원)")
    vector_manager = MoodVectorManager()
    bg_mood_vector = vector_manager.create_mood_vector(bg_analysis, image_type='background')
    print(f"✅ Vector: [{', '.join([f'{v:.2f}' for v in bg_mood_vector[:5]])}...]")

    # 7. 상품 추천
    print(f"\n🛍️  Step 6: 상품 추천")

    # 카테고리에 따라 후보 선택
    if gemini_result['category'] == 'furniture':
        candidates = MOCK_FURNITURE_PRODUCTS
        print(f"   카테고리: 가구 (Furniture)")
    else:
        candidates = MOCK_PROP_PRODUCTS
        print(f"   카테고리: 소품 (Prop)")

    # 유사도 계산 및 랭킹
    ranked_products = vector_manager.rank_products(
        background_vector=bg_mood_vector,
        product_vectors=candidates,
        top_k=5,
        method='weighted'
    )

    print(f"✅ 추천 상품 {len(ranked_products)}개")
    print(f"\n" + "-"*80)

    for i, product in enumerate(ranked_products, 1):
        match_score = product['match_score']
        if match_score >= 0.8:
            match_grade = "⭐⭐⭐ (Excellent)"
        elif match_score >= 0.6:
            match_grade = "⭐⭐ (Good)"
        else:
            match_grade = "⭐ (Fair)"

        print(f"\n{i}. {product['name']}")
        print(f"   ID: {product['product_id']}")
        print(f"   가격: {product['price']:,}원")
        print(f"   매칭 점수: {match_score:.2%} {match_grade}")
        print(f"   상세:")
        print(f"      - 색상 유사도: {product['match_details']['color_similarity']:.2%}")
        print(f"      - 물리 유사도: {product['match_details']['physics_similarity']:.2%}")
        print(f"      - 스타일 유사도: {product['match_details']['style_similarity']:.2%}")

    print(f"\n" + "="*80)
    print(f"✅ 전체 워크플로우 완료!")
    print(f"="*80)

    # 8. 결과 JSON 저장
    result = {
        'circle_detected': True,
        'circle_info': {
            'center_x': center_x,
            'center_y': center_y,
            'radius': radius,
            'category': gemini_result['category'],
            'confidence': gemini_result['confidence'],
            'description': gemini_result['description'],
            'gemini_recommendations': gemini_result['recommendations']
        },
        'background_mood': {
            'primary_style': bg_style['primary_keyword'],
            'category': bg_style['category'],
            'warmth_score': bg_colors['warmth_score'],
            'dominant_colors': bg_colors['dominant_hex']
        },
        'recommended_products': [
            {
                'product_id': p['product_id'],
                'name': p['name'],
                'category': p.get('category'),
                'price': p.get('price'),
                'match_score': p['match_score'],
                'match_details': p['match_details']
            }
            for p in ranked_products
        ]
    }

    with open('workflow_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장: workflow_result.json")


if __name__ == "__main__":
    try:
        test_full_workflow()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
