"""
API 테스트 스크립트
"""
import requests
import base64
import json


# FastAPI 서버 URL
BASE_URL = "http://localhost:8000"


def image_to_base64(image_path: str) -> str:
    """이미지 파일을 Base64로 변환"""
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        return base64.b64encode(image_bytes).decode('utf-8')


def test_health_check():
    """헬스체크 테스트"""
    print("\n" + "="*50)
    print("1. Health Check Test")
    print("="*50)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_product_analyze(image_path: str):
    """상품 분석 테스트"""
    print("\n" + "="*50)
    print("2. Product Analysis Test")
    print("="*50)

    # 이미지를 Base64로 변환
    image_base64 = image_to_base64(image_path)

    # API 요청
    payload = {
        "product_id": "test_prod_001",
        "name": "테스트 우드 테이블",
        "category": "furniture",
        "price": 150000,
        "removed_bg_image_base64": image_base64
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/products/analyze",
        json=payload
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nProduct ID: {result['product_id']}")
        print(f"Success: {result['success']}")
        print(f"\n[Colors]")
        print(f"  Dominant Hex: {result['mood_analysis']['colors']['dominant_hex']}")
        print(f"  Warmth Score: {result['mood_analysis']['colors']['warmth_score']:.2f}")
        print(f"\n[Physics]")
        physics = result['mood_analysis']['physics']
        print(f"  Circularity: {physics.get('circularity', 'N/A')}")
        print(f"  Glossiness: {physics['glossiness']:.2f}")
        print(f"  Complexity: {physics['complexity']:.2f}")
        print(f"\n[Style]")
        style = result['mood_analysis']['style']
        print(f"  Primary Keyword: {style['primary_keyword']}")
        print(f"  Primary Score: {style['primary_score']:.2f}")
        print(f"  Category: {style['category']}")
        print(f"\n[Mood Vector] (20-dim)")
        print(f"  {result['mood_vector'][:5]}... (showing first 5)")
    else:
        print(f"Error: {response.json()}")


def test_background_analyze(image_path: str):
    """배경 분석 테스트"""
    print("\n" + "="*50)
    print("3. Background Analysis Test")
    print("="*50)

    # 이미지를 Base64로 변환
    image_base64 = image_to_base64(image_path)

    # API 요청
    payload = {
        "background_image_base64": image_base64
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/analyze/background",
        json=payload
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"\n[Colors]")
        print(f"  Dominant Hex: {result['mood_analysis']['colors']['dominant_hex']}")
        print(f"  Warmth Score: {result['mood_analysis']['colors']['warmth_score']:.2f}")
        print(f"\n[Style]")
        style = result['mood_analysis']['style']
        print(f"  Primary Keyword: {style['primary_keyword']}")
        print(f"  Category: {style['category']}")
    else:
        print(f"Error: {response.json()}")


def test_recommend(image_path: str):
    """추천 테스트"""
    print("\n" + "="*50)
    print("4. Recommendation Test")
    print("="*50)

    # 이미지를 Base64로 변환
    image_base64 = image_to_base64(image_path)

    # API 요청
    payload = {
        "background_image_base64": image_base64,
        "top_k": 3,
        "matching_strategy": "weighted"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/match/recommend",
        json=payload
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n[Background Mood]")
        print(f"  Style: {result['background_mood']['style']['primary_keyword']}")
        print(f"  Warmth: {result['background_mood']['colors']['warmth_score']:.2f}")

        print(f"\n[Recommended Products] (Top {len(result['recommended_products'])})")
        for i, product in enumerate(result['recommended_products'], 1):
            print(f"\n  {i}. {product['name']} (ID: {product['product_id']})")
            print(f"     Category: {product['category']}")
            print(f"     Price: {product['price']:,}원")
            print(f"     Match Score: {product['match_score']:.2f}")
            print(f"     Match Details:")
            print(f"       - Color: {product['match_details']['color_similarity']:.2f}")
            print(f"       - Physics: {product['match_details']['physics_similarity']:.2f}")
            print(f"       - Style: {product['match_details']['style_similarity']:.2f}")
            print(f"       - Overall: {product['match_details']['overall_match']}")

        print(f"\nProcessing Time: {result['processing_time_ms']:.2f}ms")
    else:
        print(f"Error: {response.json()}")


def main():
    """
    메인 테스트 함수

    사용 전에:
    1. FastAPI 서버 실행: python app/main.py
    2. 테스트 이미지 경로 설정
    """
    print("\n" + "="*50)
    print("Interior Mood Matching API - Test Suite")
    print("="*50)

    # 헬스체크
    try:
        test_health_check()
    except Exception as e:
        print(f"Health check failed: {e}")
        print("Make sure the server is running: python app/main.py")
        return

    # 테스트 이미지 경로 (실제 경로로 변경 필요)
    PRODUCT_IMAGE_PATH = "path/to/your/product_image.jpg"
    BACKGROUND_IMAGE_PATH = "path/to/your/background_image.jpg"

    # 상품 분석 테스트
    # try:
    #     test_product_analyze(PRODUCT_IMAGE_PATH)
    # except Exception as e:
    #     print(f"Product analysis failed: {e}")

    # 배경 분석 테스트
    # try:
    #     test_background_analyze(BACKGROUND_IMAGE_PATH)
    # except Exception as e:
    #     print(f"Background analysis failed: {e}")

    # 추천 테스트
    # try:
    #     test_recommend(BACKGROUND_IMAGE_PATH)
    # except Exception as e:
    #     print(f"Recommendation failed: {e}")

    print("\n" + "="*50)
    print("Test Complete!")
    print("="*50)
    print("\n⚠️  To run full tests:")
    print("1. Set PRODUCT_IMAGE_PATH and BACKGROUND_IMAGE_PATH")
    print("2. Uncomment test functions in main()")
    print("3. Run: python test_api.py\n")


if __name__ == "__main__":
    main()
