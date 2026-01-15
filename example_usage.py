"""
인테리어 무드 매칭 시스템 사용 예제
3단계까지 구현된 모듈 테스트 코드
"""
import cv2
from app.analyzer import MoodAnalyzer


def main():
    """
    사용 예제
    """
    # 1. Analyzer 초기화
    # GPU가 있으면 자동으로 사용, 없으면 CPU 사용
    analyzer = MoodAnalyzer(clip_model="ViT-B/32", device=None)

    # 2. 배경(Background) 이미지 분석 예제
    print("=" * 50)
    print("Background Image Analysis")
    print("=" * 50)

    # 이미지 로드
    bg_image_path = "path/to/your/background_image.jpg"
    bg_image = cv2.imread(bg_image_path)

    if bg_image is not None:
        # 분석 실행
        bg_result = analyzer.analyze_background(
            image=bg_image,
            image_id="bg_001"
        )

        # 결과 출력
        print(f"Type: {bg_result['type']}")
        print(f"ID: {bg_result['id']}")
        print(f"\n[Colors]")
        print(f"  Dominant Hex: {bg_result['analysis_result']['colors']['dominant_hex']}")
        print(f"  Warmth Score: {bg_result['analysis_result']['colors']['warmth_score']:.2f}")
        print(f"\n[Physics]")
        print(f"  Linearity: {bg_result['analysis_result']['physics']['linearity']:.2f}")
        print(f"  Glossiness: {bg_result['analysis_result']['physics']['glossiness']:.2f}")
        print(f"  Complexity: {bg_result['analysis_result']['physics']['complexity']:.2f}")
        print(f"\n[Style]")
        print(f"  Primary Keyword: {bg_result['analysis_result']['style']['primary_keyword']}")
        print(f"  Primary Score: {bg_result['analysis_result']['style']['primary_score']:.2f}")
        print(f"  Category: {bg_result['analysis_result']['style']['category']}")
    else:
        print(f"Failed to load image: {bg_image_path}")

    print("\n")

    # 3. 소품(Prop) 이미지 분석 예제
    print("=" * 50)
    print("Prop Image Analysis")
    print("=" * 50)

    # 이미지 로드
    prop_image_path = "path/to/your/prop_image.jpg"
    prop_image = cv2.imread(prop_image_path)

    if prop_image is not None:
        # 분석 실행
        prop_result = analyzer.analyze_prop(
            image=prop_image,
            image_id="prop_001"
        )

        # 결과 출력
        print(f"Type: {prop_result['type']}")
        print(f"ID: {prop_result['id']}")
        print(f"\n[Colors]")
        print(f"  Dominant Hex: {prop_result['analysis_result']['colors']['dominant_hex']}")
        print(f"  Warmth Score: {prop_result['analysis_result']['colors']['warmth_score']:.2f}")
        print(f"\n[Physics]")
        print(f"  Circularity: {prop_result['analysis_result']['physics']['circularity']:.2f}")
        print(f"  Glossiness: {prop_result['analysis_result']['physics']['glossiness']:.2f}")
        print(f"  Complexity: {prop_result['analysis_result']['physics']['complexity']:.2f}")
        print(f"\n[Style]")
        print(f"  Primary Keyword: {prop_result['analysis_result']['style']['primary_keyword']}")
        print(f"  Primary Score: {prop_result['analysis_result']['style']['primary_score']:.2f}")
        print(f"  Category: {prop_result['analysis_result']['style']['category']}")
    else:
        print(f"Failed to load image: {prop_image_path}")

    print("\n")

    # 4. 통합 analyze 함수 사용 예제
    print("=" * 50)
    print("Using Unified analyze() Function")
    print("=" * 50)

    if bg_image is not None:
        result = analyzer.analyze(
            image=bg_image,
            image_type='background',
            image_id='test_001'
        )
        print(f"Analysis completed for {result['type']} image (ID: {result['id']})")


if __name__ == "__main__":
    # NOTE: 실제 실행 전에 다음을 확인하세요:
    # 1. requirements.txt의 라이브러리 설치: pip install -r requirements.txt
    # 2. style_extractor.py의 STYLE_PROMPTS를 채워넣기 (readme.md 참고)
    # 3. 테스트 이미지 경로를 실제 경로로 변경

    print("\n⚠️  실행 전 확인사항:")
    print("1. pip install -r requirements.txt 실행")
    print("2. app/services/extractors/style_extractor.py의 STYLE_PROMPTS 작성")
    print("3. example_usage.py의 이미지 경로 수정\n")

    # main()  # 준비가 되면 주석 해제
