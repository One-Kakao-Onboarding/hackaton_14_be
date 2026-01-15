"""
Style Vector Extraction Module
CLIP 모델을 사용한 14가지 스타일 분류
"""
import cv2
import numpy as np
import torch
import clip
from typing import Dict, List
from PIL import Image


class StyleExtractor:
    """
    스타일 특징 추출 클래스
    CLIP 모델을 사용하여 이미지와 14개 스타일 키워드의 유사도 계산
    """

    # TODO: 사용자가 14개 스타일 프롬프트를 작성해야 함
    # readme.md의 [Defined Style Dictionary] 참고
    STYLE_PROMPTS = {
        # ---------------------------------------------------------
        # Category 1: Natural & Cozy (자연 & 편안함)
        # [Core Logic]: Biophilic Design (자연 요소) + Hygge (심리적 안정)
        # ---------------------------------------------------------
        "natural_wood": (
            "Interior photography of a space with raw timber and natural wood materials. "
            "Biophilic design elements, abundant natural daylight, beige and earth tones. "
            "Matte wooden textures, rattan furniture, plants, organic atmosphere, airy and breathable space."
        ),
        
        "white_wood": (
            "A bright minimalist interior combining clean white walls with warm oak wood flooring. "
            "High-key lighting, spacious and neat atmosphere. "
            "Korean modern apartment style, simple wood furniture points, creamy white palette, clutter-free and balanced."
        ),
        
        "japandi": (
            "Japandi interior style, a hybrid of Japanese rustic minimalism and Scandinavian functionality. "
            "Low-profile furniture, muted neutral colors, intentional negative space, clean lines. "
            "Wabi-sabi aesthetics, natural fibers, stone and unfinished wood, calm and zen-like stillness."
        ),
        
        "cozy": (
            "A cozy and intimate room with warm ambient lighting (2700K). "
            "Soft tactile textures like knitted blankets, fabric sofas, and fluffy rugs. "
            "Enclosed and snug atmosphere, pastel and warm neutral colors, comfortable and homelike feeling, hygge style."
        ),

        # ---------------------------------------------------------
        # Category 2: Modern & Minimal (모던 & 미니멀)
        # [Core Logic]: Bauhaus (형태는 기능을 따름) + Gestalt (단순성)
        # ---------------------------------------------------------
        "modern": (
            "Contemporary modern interior design. Monochromatic color scheme (black, white, grey). "
            "Sleek polished surfaces, glass and steel materials. "
            "Sharp orthogonal lines, geometric forms, urban city vibe, cool color temperature, sophisticated and clean."
        ),
        
        "minimalism": (
            "Extreme minimalist interior, aesthetics of reduction and emptiness. "
            "Vast white negative space, absence of decorative ornaments. "
            "Hidden storage, seamless surfaces, monolithic furniture forms, austere and pure atmosphere, essentialism."
        ),
        
        "mid_century_modern": (
            "Mid-century modern interior (1950s style). Iconic furniture with tapered legs and organic curves. "
            "Teak and walnut wood mixed with vibrant accent colors (mustard yellow, olive green). "
            "Functional yet artistic, geometric patterns, retro aesthetic, plywood and plastic shell chairs."
        ),
        
        "industrial": (
            "Industrial loft style interior. Architectural brutalism with exposed concrete, red brick walls, and ductwork. "
            "Raw materials including rusted metal, black steel, and distressed leather. "
            "High ceilings, open floor plan, factory-converted aesthetic, masculine and rough textures."
        ),

        # ---------------------------------------------------------
        # Category 3: Glam & Classic (화려함 & 클래식)
        # [Core Logic]: Ornamentation (장식성) + Symmetry (대칭성)
        # ---------------------------------------------------------
        "classic": (
            "Traditional classic interior design. Heavy visual weight with ornate moldings and wainscoting. "
            "Antique wooden furniture, rich velvet fabrics, crystal chandeliers. "
            "Symmetrical layout, deep colors (burgundy, navy, gold), aristocratic and dignified atmosphere."
        ),
        
        "modern_french": (
            "Parisian modern french apartment style. Wall paneling (boiserie) paired with contemporary furniture. "
            "Herringbone parquet flooring, soft pastel and cream tones. "
            "Elegant curves, romantic mood, sophisticated mix of old architecture and new decor."
        ),
        
        "hotel_luxury": (
            "High-end luxury hotel suite interior. Premium materials like polished marble, brass, and dark wood. "
            "Architectural indirect lighting (cove lighting), perfect symmetry and balance. "
            "Plush bedding, glossy surfaces, grand and expensive atmosphere, boutique hotel vibe."
        ),

        # ---------------------------------------------------------
        # Category 4: Unique & Colorful (개성 & 컬러풀)
        # [Core Logic]: Color Psychology (색채 심리) + Narrative (서사성)
        # ---------------------------------------------------------
        "vintage": (
            "Vintage eclectic interior. A collected space with retro props and secondhand furniture. "
            "Visible signs of wear and patina, faded colors, floral or geometric wallpapers. "
            "Nostalgic atmosphere, grandma-chic, warm and clustered arrangement, storytelling objects."
        ),
        
        "pop_art": (
            "Pop art inspired interior design. High saturation color blocking (primary colors). "
            "Glossy plastic materials, bold graphic prints, and sculptural furniture. "
            "Playful, kitsch, and energetic mood, artistic expression, memphis design influence."
        ),
        
        "planterior": (
            "Planterior style space, urban indoor jungle. "
            "High density of green foliage, hanging plants, and large potted trees. "
            "Natural light filtering through leaves, botanical patterns, terra cotta pots. "
            "Fresh, lively, and oxygen-filled atmosphere, nature immersion."
        )
    }

    # 카테고리 매핑
    CATEGORY_MAP = {
        "natural_wood": "Natural & Cozy",
        "white_wood": "Natural & Cozy",
        "japandi": "Natural & Cozy",
        "cozy": "Natural & Cozy",

        "modern": "Modern & Minimal",
        "minimalism": "Modern & Minimal",
        "mid_century_modern": "Modern & Minimal",
        "industrial": "Modern & Minimal",

        "classic": "Glam & Classic",
        "modern_french": "Glam & Classic",
        "hotel_luxury": "Glam & Classic",

        "vintage": "Unique & Colorful",
        "pop_art": "Unique & Colorful",
        "planterior": "Unique & Colorful"
    }

    def __init__(self, model_name: str = "ViT-B/32", device: str = None):
        """
        Args:
            model_name: CLIP 모델 이름 (기본 ViT-B/32)
            device: 디바이스 ('cuda', 'cpu', None=auto)
        """
        # 디바이스 설정
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # CLIP 모델 로드
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()

        # 텍스트 프롬프트 인코딩 (캐싱)
        self._encode_text_prompts()

    def _encode_text_prompts(self):
        """
        14개 스타일 프롬프트를 미리 인코딩하여 캐싱
        """
        style_keys = list(self.STYLE_PROMPTS.keys())
        prompts = [self.STYLE_PROMPTS[key] for key in style_keys]

        # 빈 프롬프트 체크
        if not any(prompts) or all(p == "" for p in prompts):
            print("Warning: All style prompts are empty. Please fill STYLE_PROMPTS.")
            self.text_features = None
            self.style_keys = style_keys
            return

        # 텍스트 토큰화
        text_tokens = clip.tokenize(prompts).to(self.device)

        # 텍스트 인코딩
        with torch.no_grad():
            self.text_features = self.model.encode_text(text_tokens)
            self.text_features /= self.text_features.norm(dim=-1, keepdim=True)  # 정규화

        self.style_keys = style_keys

    def extract(self, image: np.ndarray) -> Dict:
        """
        이미지에서 스타일 특징 추출

        Args:
            image: OpenCV 형식의 이미지 (BGR)

        Returns:
            Dict containing:
                - 'primary_keyword': 1순위 스타일 키워드
                - 'primary_score': 1순위 확신도 (0.0~1.0)
                - 'category': 상위 카테고리
                - 'vector_breakdown': 14개 스타일별 확률 분포
                - 'style_vector': 14차원 벡터 (리스트)
        """
        # 프롬프트가 비어있으면 더미 결과 반환
        if self.text_features is None:
            return self._empty_result()

        # BGR -> RGB 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # 이미지 전처리
        image_input = self.preprocess(pil_image).unsqueeze(0).to(self.device)

        # 이미지 인코딩
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)  # 정규화

            # 코사인 유사도 계산
            similarity = (image_features @ self.text_features.T).squeeze(0)

            # Softmax로 확률 변환
            probabilities = torch.nn.functional.softmax(similarity * 100, dim=0)

        # CPU로 이동 및 numpy 변환
        probabilities = probabilities.cpu().numpy()

        # 결과 생성
        style_vector = probabilities.tolist()
        vector_breakdown = {key: float(prob) for key, prob in zip(self.style_keys, probabilities)}

        # 1순위 스타일
        primary_idx = np.argmax(probabilities)
        primary_keyword = self.style_keys[primary_idx]
        primary_score = float(probabilities[primary_idx])
        category = self.CATEGORY_MAP[primary_keyword]

        return {
            'primary_keyword': primary_keyword,
            'primary_score': primary_score,
            'category': category,
            'vector_breakdown': vector_breakdown,
            'style_vector': style_vector
        }

    def _empty_result(self) -> Dict:
        """
        프롬프트가 비어있을 때 더미 결과 반환
        """
        n_styles = len(self.STYLE_PROMPTS)
        uniform_prob = 1.0 / n_styles

        return {
            'primary_keyword': 'unknown',
            'primary_score': uniform_prob,
            'category': 'Unknown',
            'vector_breakdown': {key: uniform_prob for key in self.style_keys},
            'style_vector': [uniform_prob] * n_styles
        }
