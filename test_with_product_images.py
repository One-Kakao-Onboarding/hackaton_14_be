"""
product_images 디렉토리의 이미지를 기반으로 API 테스트
추출된 PNG 이미지들을 분석하고 배경 이미지와 매칭 테스트
"""
import os
import cv2
import numpy as np
import base64
import json
from io import BytesIO
from PIL import Image
import requests
from typing import List, Dict

from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


def load_product_images(image_dir='product_images'):
    """
    product_images 디렉토리에서 상품 이미지 로드

    Returns:
        List[Dict]: 상품 정보 리스트
    """
    print("="*80)
    print("📦 상품 이미지 로드")
    print("="*80)

    if not os.path.exists(image_dir):
        print(f"\n❌ 디렉토리 없음: {image_dir}")
        return []

    products = []

    # 모든 PNG 파일 찾기
    image_files = [f for f in os.listdir(image_dir) if f.endswith('.png')]
    image_files.sort()

    print(f"\n📁 디렉토리: {image_dir}/")
    print(f"✅ {len(image_files)}개 이미지 발견\n")

    for filename in image_files:
        try:
            filepath = os.path.join(image_dir, filename)

            # 이미지 로드
            pil_image = Image.open(filepath)
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # product_id 추출 (파일명에서)
            product_id = filename.replace('.png', '')

            # 카테고리 추출
            if product_id.startswith('furniture'):
                category = 'furniture'
            elif product_id.startswith('prop'):
                category = 'prop'
            else:
                category = 'unknown'

            # Base64 인코딩
            _, buffer = cv2.imencode('.png', cv_image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            products.append({
                'product_id': product_id,
                'filename': filename,
                'filepath': filepath,
                'category': category,
                'image': cv_image,
                'image_base64': image_base64,
                'size': pil_image.size
            })

            print(f"✅ {filename} ({pil_image.size[0]}x{pil_image.size[1]}px, {category})")

        except Exception as e:
            print(f"❌ {filename} 로드 실패: {e}")

    print(f"\n📊 로드 완료: {len(products)}개")
    return products


def analyze_products(products: List[Dict]):
    """
    상품들의 Mood Vector 분석

    Args:
        products: 상품 리스트

    Returns:
        List[Dict]: 분석 결과가 추가된 상품 리스트
    """
    print("\n" + "="*80)
    print("🎨 상품 Mood 분석")
    print("="*80 + "\n")

    mood_analyzer = MoodAnalyzer()
    vector_manager = MoodVectorManager()

    for product in products:
        try:
            product_id = product['product_id']

            # Mood 분석
            analysis = mood_analyzer.analyze(
                image=product['image'],
                image_type='prop',
                image_id=product_id
            )

            # Mood Vector 생성
            mood_vector = vector_manager.create_mood_vector(
                analysis_result=analysis,
                image_type='prop'
            )

            # 결과 추가
            product['mood_analysis'] = analysis
            product['mood_vector'] = mood_vector
            product['primary_style'] = analysis['analysis_result']['style']['primary_keyword']
            product['warmth_score'] = analysis['analysis_result']['colors']['warmth_score']

            print(f"✅ [{product_id}]")
            print(f"   스타일: {product['primary_style']}")
            print(f"   색온도: {product['warmth_score']:.2f}")

        except Exception as e:
            print(f"❌ [{product_id}] 분석 실패: {e}")
            product['mood_vector'] = None

    analyzed_count = sum(1 for p in products if p.get('mood_vector') is not None)
    print(f"\n📊 분석 완료: {analyzed_count}/{len(products)}개")

    return products


def match_with_background(products: List[Dict], background_image_path='test_image.png'):
    """
    배경 이미지와 상품 매칭

    Args:
        products: 분석된 상품 리스트
        background_image_path: 배경 이미지 경로

    Returns:
        List[Dict]: 매칭 점수가 추가된 상품 리스트
    """
    print("\n" + "="*80)
    print("🔍 배경 이미지와 매칭")
    print("="*80)

    # 배경 이미지 로드
    print(f"\n📁 배경 이미지: {background_image_path}")
    bg_image = cv2.imread(background_image_path)
    if bg_image is None:
        print(f"❌ 배경 이미지 로드 실패")
        return products

    print(f"✅ 배경 이미지 로드 ({bg_image.shape[1]}x{bg_image.shape[0]}px)")

    # 배경 분석
    print("\n🎨 배경 무드 분석 중...")
    mood_analyzer = MoodAnalyzer()
    vector_manager = MoodVectorManager()

    bg_analysis = mood_analyzer.analyze(
        image=bg_image,
        image_type='background',
        image_id='test_background'
    )

    bg_mood_vector = vector_manager.create_mood_vector(
        analysis_result=bg_analysis,
        image_type='background'
    )

    bg_style = bg_analysis['analysis_result']['style']
    print(f"✅ 배경 스타일: {bg_style['primary_keyword']} ({bg_style['primary_score']:.2%})")

    # 상품과 매칭
    print("\n📊 상품 매칭 중...\n")

    valid_products = [p for p in products if p.get('mood_vector') is not None]

    ranked_products = vector_manager.rank_products(
        background_vector=bg_mood_vector,
        product_vectors=valid_products,
        top_k=len(valid_products),
        method='weighted'
    )

    # 매칭 점수 출력
    print("🏆 매칭 결과 (Top 10):")
    print("-" * 80)
    for i, product in enumerate(ranked_products[:10], 1):
        score = product['match_score']
        if score >= 0.8:
            grade = "⭐⭐⭐ Excellent"
        elif score >= 0.7:
            grade = "⭐⭐ Good"
        else:
            grade = "⭐ Fair"

        print(f"{i:2d}. [{product['product_id']}] {score:.2%} {grade}")
        print(f"    스타일: {product['primary_style']}, 색온도: {product['warmth_score']:.2f}")

    print("\n" + "="*80)

    return ranked_products


def generate_simulations(products: List[Dict], background_image_path='test_image.png', top_k=5):
    """
    Gemini Nano Banana로 시뮬레이션 이미지 생성

    Args:
        products: 매칭된 상품 리스트
        background_image_path: 배경 이미지 경로
        top_k: 생성할 이미지 개수
    """
    print("\n" + "="*80)
    print(f"🎨 시뮬레이션 이미지 생성 (Top {top_k})")
    print("="*80)

    # Gemini API 키 확인
    import os
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n⚠️  GEMINI_API_KEY 없음. Mock 시뮬레이션 사용")
        return

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        print("\n✅ Gemini API 초기화 완료")
    except ImportError:
        print("\n⚠️  google.genai 패키지 없음. 스킵.")
        return
    except Exception as e:
        print(f"\n⚠️  Gemini 초기화 실패: {e}")
        return

    # 배경 이미지 로드
    bg_image = cv2.imread(background_image_path)
    if bg_image is None:
        print(f"❌ 배경 이미지 로드 실패")
        return

    rgb_image = cv2.cvtColor(bg_image, cv2.COLOR_BGR2RGB)
    pil_bg = Image.fromarray(rgb_image)

    print(f"\n📁 배경 이미지: {background_image_path}")
    print(f"   크기: {pil_bg.size[0]}x{pil_bg.size[1]}px\n")

    # 동그라미 위치 (중앙 왼쪽)
    img_height, img_width = bg_image.shape[:2]
    circle_x = int(img_width * 0.22)
    circle_y = int(img_height * 0.40)
    circle_radius = int(img_width * 0.23)

    # 상대 위치 계산
    rel_x = (circle_x / img_width) * 100
    rel_y = (circle_y / img_height) * 100
    rel_size = (circle_radius * 2 / img_width) * 100

    # 위치 설명
    location_desc = "left side, middle"

    # Top K 상품 시뮬레이션
    for i, product in enumerate(products[:top_k], 1):
        try:
            product_id = product['product_id']

            print(f"{i}. [{product_id}] 생성 중...")

            # 상품 이미지 로드
            product_image = product['image']
            product_rgb = cv2.cvtColor(product_image, cv2.COLOR_BGR2RGB)
            pil_product = Image.fromarray(product_rgb)

            # 프롬프트 생성 (무드 위주, API와 동일)
            prompt = f"""You are a creative Art Director and professional Retoucher specializing in high-end lifestyle product photography.

TASK:
Seamlessly integrate a product into an interior space to create a cohesive, mood-driven lifestyle image.

INPUTS:
1. BASE IMAGE (Interior Room): The atmospheric setting.
2. PRODUCT IMAGE (Item): The object to be placed.

CORE INSTRUCTION:
Place the product in the {location_desc} of the room.
**CRITICAL:** Do not just "paste" the image. You must simulate how light and air interact with the object in this specific environment.

EXECUTION STEPS:

1. [ENVIRONMENTAL ANALYSIS]
   - Analyze the room's lighting source (direction, intensity, color temperature).
   - Identify the mood (e.g., cozy warm, stark modern, morning sunlight).
   - Determine the surface texture where the product will sit.

2. [INTELLIGENT COMPOSITING]
   - Place the product at approximately ({rel_x:.1f}%, {rel_y:.1f}%) position.
   - **RELIGHT THE PRODUCT:** Adjust the product's highlights and shadows to match the room's lighting exactly. If the room has warm sunset light, the product must reflect that warmth.
   - **CAST REALISTIC SHADOWS:** Generate natural contact shadows (occlusion shadows) where the product touches the surface, and cast shadows (directional shadows) based on the room's light source.
   - **REFLECTIONS & COLOR BLEED:** If the surface is reflective (e.g., wood, marble), create a subtle reflection. Allow the colors of the room to subtly tint the edges of the product (global illumination) for better blending.

3. [FINAL POLISH]
   - Match the grain, noise, and focus (depth of field) of the product to the background room.
   - Ensure the perspective aligns perfectly with the room's camera angle.

OUTPUT GOAL:
A photorealistic, emotional lifestyle shot where the product looks like it was originally photographed in that room. No floating objects. No harsh cutouts."""

            # Gemini API 호출 (배경 + 상품 이미지 모두 제공)
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, pil_bg, pil_product]
            )

            # 이미지 추출
            if response and hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]

                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data

                        # PIL Image로 변환
                        generated_image = Image.open(BytesIO(image_data))

                        # 저장
                        output_path = f"simulation_{i}_{product_id}.png"
                        generated_image.save(output_path)

                        print(f"   ✅ 저장: {output_path}")
                        print(f"   크기: {generated_image.size[0]}x{generated_image.size[1]}px")
                        print(f"   용량: {len(image_data)/1024:.1f}KB\n")
                        break
            else:
                print(f"   ⚠️  이미지 생성 실패\n")

        except Exception as e:
            print(f"   ❌ 에러: {e}\n")

    print("="*80)
    print("✅ 시뮬레이션 완료")
    print("="*80)


def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("🧪 Product Images 기반 테스트")
    print("="*80)

    # 1. 상품 이미지 로드
    products = load_product_images('product_images')

    if not products:
        print("\n❌ 상품 이미지가 없습니다.")
        print("   먼저 extract_images_from_cache.py를 실행하세요.")
        return

    # 2. 상품 분석
    products = analyze_products(products)

    # 3. 배경과 매칭
    ranked_products = match_with_background(products, 'test_image.png')

    # 4. 시뮬레이션 이미지 생성 (Top 5)
    print("\n📸 시뮬레이션 이미지를 생성하시겠습니까? (Top 5)")
    print("   이 작업은 약 50-60초가 소요됩니다.")

    # 자동 실행 (사용자 입력 없이)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--simulate':
        generate_simulations(ranked_products, 'test_image.png', top_k=5)
    else:
        print("\n   시뮬레이션을 실행하려면:")
        print("   python3 test_with_product_images.py --simulate")

    # 5. 요약
    print("\n" + "="*80)
    print("📊 최종 요약")
    print("="*80)
    print(f"✅ 상품 이미지: {len(products)}개")
    print(f"✅ 분석 완료: {sum(1 for p in products if p.get('mood_vector'))}개")
    print(f"✅ 매칭 점수 범위: {ranked_products[0]['match_score']:.2%} ~ {ranked_products[-1]['match_score']:.2%}")

    # Top 3 출력
    print(f"\n🏆 Top 3 추천:")
    for i, p in enumerate(ranked_products[:3], 1):
        print(f"   {i}. {p['product_id']} - {p['match_score']:.2%} ({p['primary_style']})")

    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
