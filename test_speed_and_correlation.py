"""
API 속도 테스트 및 무드 correlation 분석
"""
import requests
import time
import json
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# API 엔드포인트
API_URL = "http://localhost:8000/api/ai-interior"

# 테스트 이미지
TEST_IMAGE = "test_image.png"

def test_api_speed_and_correlation():
    """API 속도 테스트 및 무드 correlation 분석"""

    if not Path(TEST_IMAGE).exists():
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {TEST_IMAGE}")
        return

    print("=" * 80)
    print("🚀 AI Interior API 속도 및 무드 Correlation 테스트")
    print("=" * 80)

    # 테스트 이미지 로드
    with open(TEST_IMAGE, 'rb') as f:
        image_data = f.read()

    # 동그라미 좌표 (이미지 중앙에 큰 원)
    circles_data = [
        {
            "x": 0.5,  # 중앙 (왼쪽=0, 오른쪽=1)
            "y": 0.5,  # 중앙 (아래=0, 위=1)
            "radius": 0.15  # 반지름 (이미지 너비의 15%)
        }
    ]

    # API 요청 데이터 준비
    files = {
        'image': ('test_image.png', image_data, 'image/png')
    }
    data = {
        'circles': json.dumps(circles_data)
    }

    # 속도 측정 시작
    print(f"\n📤 API 요청 전송 중...")
    print(f"   이미지: {TEST_IMAGE} ({len(image_data)/1024:.1f}KB)")
    print(f"   동그라미: {circles_data[0]}")

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

        # 추천 상품
        products = result.get('recommended_products', [])
        print(f"\n🛍️  추천 상품: {len(products)}개")

        if not products:
            print("   추천 상품이 없습니다.")
            return

        # 무드 Correlation 분석
        print(f"\n📊 무드 Correlation 분석:")
        print("=" * 80)
        print(f"{'순위':<6} {'상품명':<40} {'매칭 점수':<12} {'스타일':<15}")
        print("=" * 80)

        for idx, product in enumerate(products, 1):
            name = product.get('name', 'Unknown')[:38]
            match_score = product.get('match_score', 0)
            primary_keyword = product.get('match_details', {}).get('primary_keyword', 'N/A')

            # 매칭 점수 막대 그래프
            bar_length = int(match_score * 20)
            bar = '█' * bar_length + '░' * (20 - bar_length)

            print(f"{idx:<6} {name:<40} {match_score:.2f} {bar} {primary_keyword:<15}")

            # 상세 매칭 정보 (상위 3개만)
            if idx <= 3:
                details = product.get('match_details', {})
                print(f"       └─ 따뜻함: {details.get('warmth_similarity', 0):.3f} | "
                      f"색상: {details.get('color_harmony', 0):.3f} | "
                      f"스타일: {details.get('style_compatibility', 0):.3f}")

                # 시뮬레이션 이미지 확인
                if product.get('simulated_image_base64'):
                    sim_size = len(product['simulated_image_base64']) / 1024
                    print(f"       └─ 시뮬레이션 이미지: {sim_size:.1f}KB")

        print("=" * 80)

        # 통계 요약
        match_scores = [p.get('match_score', 0) for p in products]
        print(f"\n📈 매칭 점수 통계:")
        print(f"   평균: {np.mean(match_scores):.3f}")
        print(f"   최고: {np.max(match_scores):.3f}")
        print(f"   최저: {np.min(match_scores):.3f}")
        print(f"   표준편차: {np.std(match_scores):.3f}")

        # 스타일 분포
        styles = [p.get('match_details', {}).get('primary_keyword', 'N/A') for p in products]
        style_counts = {}
        for style in styles:
            style_counts[style] = style_counts.get(style, 0) + 1

        print(f"\n🎭 스타일 분포:")
        for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(styles)) * 100
            print(f"   {style:<20} {count}개 ({percentage:.1f}%)")

        # 결과를 파일로 저장
        output_file = "api_test_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # simulated_image_base64는 너무 커서 제외
            result_without_images = {
                'success': result['success'],
                'message': result.get('message'),
                'total_time_ms': total_time,
                'circle_info': result.get('circle_info'),
                'background_mood': result.get('background_mood'),
                'recommended_products': [
                    {k: v for k, v in p.items() if k != 'simulated_image_base64'}
                    for p in products
                ]
            }
            json.dump(result_without_images, f, ensure_ascii=False, indent=2)

        print(f"\n💾 상세 결과 저장: {output_file}")

    except requests.exceptions.Timeout:
        print(f"❌ API 타임아웃 (120초 초과)")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_speed_and_correlation()
