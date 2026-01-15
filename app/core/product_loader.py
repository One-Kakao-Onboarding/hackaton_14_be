"""
JSON 파일에서 상품 데이터를 직접 로드하는 모듈 (DB 없이 사용)
"""
import json
import os
import base64
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from typing import List, Dict, Optional
import pickle

from app.analyzer import MoodAnalyzer
from app.core.vector_manager import MoodVectorManager


class ProductLoader:
    """
    JSON 파일에서 상품을 로드하고 분석하는 클래스
    """

    def __init__(self):
        self.furniture_products: List[Dict] = []
        self.prop_products: List[Dict] = []
        self.all_products: List[Dict] = []

        # 분석기 초기화
        self.mood_analyzer = MoodAnalyzer()
        self.vector_manager = MoodVectorManager()

        # 캐시 파일 경로
        self.cache_file = "product_cache.pkl"

    def base64_to_cv_image(self, base64_str: str) -> np.ndarray:
        """Base64 문자열을 OpenCV 이미지로 변환"""
        # data:image/png;base64, 프리픽스 제거
        if ',' in base64_str and base64_str.startswith('data:'):
            base64_str = base64_str.split(',', 1)[1]

        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data))
        # PIL RGB -> OpenCV BGR
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return cv_image

    def analyze_product(self, product: Dict, category: str, product_id: str) -> Optional[Dict]:
        """
        단일 상품 분석

        Args:
            product: 원본 JSON 데이터
            category: 'furniture' or 'prop'
            product_id: 상품 고유 ID

        Returns:
            분석된 상품 정보 딕셔너리
        """
        try:
            # 기본 정보
            name = product.get('name', 'Unknown')
            brand = product.get('brand', '')
            price = product.get('discount_price') or product.get('original_price', 0)
            image_url = product.get('image_url', '')
            removed_bg_base64 = product.get('removed_background_image_base64', '')

            if not removed_bg_base64:
                return None

            # Base64 -> OpenCV 이미지
            cv_image = self.base64_to_cv_image(removed_bg_base64)

            # Mood 분석
            analysis = self.mood_analyzer.analyze(
                image=cv_image,
                image_type='prop',
                image_id=product_id
            )

            # Mood Vector 생성 (이미 리스트로 반환됨)
            mood_vector = self.vector_manager.create_mood_vector(
                analysis_result=analysis,
                image_type='prop'
            )

            return {
                'product_id': product_id,
                'name': f"{brand} {name}" if brand else name,
                'category': category,
                'price': int(price) if price else 0,
                'image_url': image_url,
                'removed_bg_image_base64': removed_bg_base64,
                'mood_vector': mood_vector,  # 이미 리스트임
                'primary_keyword': analysis['analysis_result']['style']['primary_keyword'],
                'dominant_hex': analysis['analysis_result']['colors']['dominant_hex'][:2],
                'warmth_score': analysis['analysis_result']['colors']['warmth_score'],
            }

        except Exception as e:
            print(f"⚠️  [{product_id}] 분석 실패: {e}")
            return None

    def load_from_precalculated(self, item: Dict, category: str) -> Optional[Dict]:
        """
        미리 계산된 무드 벡터를 포함한 상품 데이터 로드

        Args:
            item: JSON에서 로드한 상품 데이터 (mood_vector 포함)
            category: 'furniture' or 'prop'

        Returns:
            표준화된 상품 정보 딕셔너리
        """
        try:
            # 필수 필드 확인
            if 'mood_vector' not in item:
                print(f"⚠️  [{item.get('product_id', 'unknown')}] mood_vector 없음")
                return None

            # 기본 정보
            name = item.get('name', 'Unknown')
            brand = item.get('brand', '')
            price = item.get('discount_price') or item.get('original_price', 0)
            image_url = item.get('image_url', '')
            removed_bg_base64 = item.get('removed_background_image_base64', '')
            product_id = item.get('product_id', 'unknown')

            # 이미 계산된 무드 데이터
            mood_vector = item['mood_vector']
            dominant_colors = item.get('dominant_colors', [])
            warmth_score = item.get('warmth_score', 0.5)
            primary_style = item.get('primary_style', 'unknown')

            return {
                'product_id': product_id,
                'name': f"{brand} {name}" if brand else name,
                'category': category,
                'price': int(price) if price else 0,
                'image_url': image_url,
                'removed_bg_image_base64': removed_bg_base64,
                'mood_vector': mood_vector,
                'primary_keyword': primary_style,
                'dominant_hex': dominant_colors[:2] if len(dominant_colors) >= 2 else dominant_colors,
                'warmth_score': warmth_score,
            }

        except Exception as e:
            print(f"⚠️  [{item.get('product_id', 'unknown')}] 로드 실패: {e}")
            return None

    def load_from_json(self, use_cache: bool = True) -> bool:
        """
        JSON 파일에서 상품을 로드 (미리 계산된 무드 벡터 사용)

        Args:
            use_cache: 캐시 파일이 있으면 사용할지 여부

        Returns:
            성공 여부
        """
        # 캐시 파일이 있으면 로드
        if use_cache and os.path.exists(self.cache_file):
            print(f"📦 캐시 파일 로드 중... ({self.cache_file})")
            try:
                with open(self.cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    self.furniture_products = cached_data['furniture']
                    self.prop_products = cached_data['prop']
                    self.all_products = cached_data['all']
                print(f"✅ 캐시에서 로드 완료: 가구 {len(self.furniture_products)}개, 소품 {len(self.prop_products)}개")
                return True
            except Exception as e:
                print(f"⚠️  캐시 로드 실패: {e}. JSON에서 새로 로드합니다.")

        # JSON 파일 경로 (미리 계산된 무드 벡터 포함)
        furniture_file = 'kakao_furniture_data_with_precalculated_mood.json'
        interior_file = 'kakao_interior_data_with_precalculated_mood.json'

        # 가구 데이터 로드 (미리 계산된 무드 벡터 사용)
        if os.path.exists(furniture_file):
            print(f"\n📦 가구 데이터 로드 중... ({furniture_file})")
            with open(furniture_file, 'r', encoding='utf-8') as f:
                furniture_raw = json.load(f)

            print(f"   총 {len(furniture_raw)}개 가구 발견. 로드 중...")

            for idx, item in enumerate(furniture_raw):
                loaded = self.load_from_precalculated(item, 'furniture')
                if loaded:
                    self.furniture_products.append(loaded)

                # 진행 상황 출력
                if (idx + 1) % 20 == 0:
                    print(f"   진행: {idx+1}/{len(furniture_raw)}")

            print(f"✅ 가구 {len(self.furniture_products)}개 로드 완료\n")

        # 인테리어 소품 데이터 로드 (미리 계산된 무드 벡터 사용)
        if os.path.exists(interior_file):
            print(f"📦 소품 데이터 로드 중... ({interior_file})")
            with open(interior_file, 'r', encoding='utf-8') as f:
                interior_raw = json.load(f)

            print(f"   총 {len(interior_raw)}개 소품 발견. 로드 중...")

            for idx, item in enumerate(interior_raw):
                loaded = self.load_from_precalculated(item, 'prop')
                if loaded:
                    self.prop_products.append(loaded)

                # 진행 상황 출력
                if (idx + 1) % 20 == 0:
                    print(f"   진행: {idx+1}/{len(interior_raw)}")

            print(f"✅ 소품 {len(self.prop_products)}개 로드 완료\n")
        else:
            print(f"⚠️  소품 파일 없음 ({interior_file}). 기존 방식으로 로드 시도...")
            # Fallback: 기존 parsed 파일에서 로드하고 분석
            interior_file_fallback = 'kakao_interior_data_parsed.json'
            if os.path.exists(interior_file_fallback):
                print(f"📦 소품 데이터 로드 중... ({interior_file_fallback})")
                with open(interior_file_fallback, 'r', encoding='utf-8') as f:
                    interior_raw = json.load(f)

                print(f"   총 {len(interior_raw)}개 소품 발견. 분석 시작...")

                # 처음 10개만 분석 (빠른 테스트)
                max_items = min(10, len(interior_raw))
                for idx, item in enumerate(interior_raw[:max_items]):
                    product_id = f"prop_{idx+1:04d}"
                    analyzed = self.analyze_product(item, 'prop', product_id)
                    if analyzed:
                        self.prop_products.append(analyzed)

                    # 진행 상황 출력
                    if (idx + 1) % 10 == 0:
                        print(f"   진행: {idx+1}/{max_items}")

                print(f"✅ 소품 {len(self.prop_products)}개 로드 완료\n")

        # 전체 상품 리스트
        self.all_products = self.furniture_products + self.prop_products

        # 캐시 저장
        print(f"💾 캐시 저장 중... ({self.cache_file})")
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'furniture': self.furniture_products,
                    'prop': self.prop_products,
                    'all': self.all_products
                }, f)
            print(f"✅ 캐시 저장 완료\n")
        except Exception as e:
            print(f"⚠️  캐시 저장 실패: {e}\n")

        return True

    def get_products_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        카테고리별 상품 가져오기

        Args:
            category: 'furniture' or 'prop'
            limit: 최대 개수

        Returns:
            상품 리스트
        """
        if category == 'furniture':
            return self.furniture_products[:limit]
        elif category == 'prop':
            return self.prop_products[:limit]
        else:
            return self.all_products[:limit]

    def search_similar(
        self,
        mood_vector: List[float],
        category: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        무드 벡터 기반 유사 상품 검색

        Args:
            mood_vector: 검색할 무드 벡터
            category: 카테고리 필터 (None이면 전체)
            top_k: 반환할 상품 개수

        Returns:
            유사도 순으로 정렬된 상품 리스트
        """
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        # 검색 대상 상품 선택
        if category == 'furniture':
            candidates = self.furniture_products
        elif category == 'prop':
            candidates = self.prop_products
        else:
            candidates = self.all_products

        if not candidates:
            return []

        # 코사인 유사도 계산
        query_vec = np.array(mood_vector).reshape(1, -1)
        product_vecs = np.array([p['mood_vector'] for p in candidates])

        similarities = cosine_similarity(query_vec, product_vecs)[0]

        # 유사도와 함께 상품 정보 결합
        results = []
        for idx, product in enumerate(candidates):
            results.append({
                **product,
                'similarity': float(similarities[idx])
            })

        # 유사도 내림차순 정렬
        results.sort(key=lambda x: x['similarity'], reverse=True)

        return results[:top_k]


# 전역 인스턴스 (싱글톤)
_product_loader = None


def get_product_loader() -> ProductLoader:
    """전역 ProductLoader 인스턴스 반환 (싱글톤)"""
    global _product_loader
    if _product_loader is None:
        _product_loader = ProductLoader()
        _product_loader.load_from_json(use_cache=True)
    return _product_loader
