"""
상품 Clustering 모듈
K-Means를 사용하여 유사한 무드의 상품들을 그룹화
"""
import numpy as np
from typing import List, Dict, Optional
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os


class ProductClusterManager:
    """
    상품 무드 벡터 Clustering 관리 클래스
    """

    def __init__(
        self,
        n_clusters: int = 20,
        random_state: int = 42,
        model_path: Optional[str] = None
    ):
        """
        Args:
            n_clusters: 클러스터 개수
            random_state: 랜덤 시드
            model_path: 저장된 모델 경로 (없으면 새로 학습)
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model_path = model_path

        self.kmeans = None
        self.scaler = StandardScaler()
        self.cluster_info = {}

        # 저장된 모델이 있으면 로드
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def fit(self, product_vectors: List[Dict]) -> Dict:
        """
        상품 벡터들로 K-Means 클러스터링 수행

        Args:
            product_vectors: 상품 데이터 리스트
                [{'product_id': 'prod_001', 'mood_vector': [...], ...}, ...]

        Returns:
            클러스터링 결과 정보
        """
        if not product_vectors:
            raise ValueError("product_vectors is empty")

        # Mood Vector 추출
        vectors = np.array([p['mood_vector'] for p in product_vectors])

        # 정규화
        vectors_scaled = self.scaler.fit_transform(vectors)

        # K-Means 학습
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )

        cluster_labels = self.kmeans.fit_predict(vectors_scaled)

        # 각 상품에 cluster_id 할당
        for i, product in enumerate(product_vectors):
            product['cluster_id'] = int(cluster_labels[i])

        # 클러스터 정보 계산
        self.cluster_info = self._calculate_cluster_info(product_vectors)

        return {
            'total_products': len(product_vectors),
            'n_clusters': self.n_clusters,
            'cluster_distribution': self.cluster_info,
            'inertia': float(self.kmeans.inertia_)
        }

    def predict(self, mood_vector: List[float]) -> int:
        """
        주어진 무드 벡터가 속할 클러스터 예측

        Args:
            mood_vector: 20차원 mood vector

        Returns:
            cluster_id (0 ~ n_clusters-1)
        """
        if self.kmeans is None:
            raise ValueError("Model is not fitted yet. Call fit() first.")

        vector = np.array(mood_vector).reshape(1, -1)
        vector_scaled = self.scaler.transform(vector)
        cluster_id = self.kmeans.predict(vector_scaled)[0]

        return int(cluster_id)

    def get_nearest_clusters(
        self,
        mood_vector: List[float],
        top_k: int = 3
    ) -> List[int]:
        """
        주어진 무드 벡터와 가장 가까운 K개의 클러스터 반환

        Args:
            mood_vector: 20차원 mood vector
            top_k: 반환할 클러스터 개수

        Returns:
            가까운 순서대로 정렬된 cluster_id 리스트
        """
        if self.kmeans is None:
            raise ValueError("Model is not fitted yet. Call fit() first.")

        vector = np.array(mood_vector).reshape(1, -1)
        vector_scaled = self.scaler.transform(vector)

        # 각 클러스터 중심까지의 거리 계산
        distances = self.kmeans.transform(vector_scaled)[0]

        # 거리 순으로 정렬된 클러스터 ID
        nearest_cluster_ids = np.argsort(distances)[:top_k]

        return [int(cid) for cid in nearest_cluster_ids]

    def _calculate_cluster_info(self, product_vectors: List[Dict]) -> Dict:
        """
        각 클러스터의 통계 정보 계산

        Args:
            product_vectors: cluster_id가 할당된 상품 리스트

        Returns:
            클러스터별 정보 딕셔너리
        """
        cluster_info = {}

        for cluster_id in range(self.n_clusters):
            # 해당 클러스터의 상품들 필터링
            cluster_products = [
                p for p in product_vectors
                if p.get('cluster_id') == cluster_id
            ]

            if not cluster_products:
                cluster_info[cluster_id] = {
                    'product_count': 0,
                    'dominant_style': 'unknown',
                    'avg_warmth': 0.0
                }
                continue

            # 스타일 빈도 계산 (가장 많은 스타일)
            styles = [p.get('primary_keyword', 'unknown') for p in cluster_products]
            dominant_style = max(set(styles), key=styles.count)

            # 평균 warmth 계산
            warmth_scores = [p['mood_vector'][0] for p in cluster_products]  # 첫 번째 차원이 warmth
            avg_warmth = np.mean(warmth_scores)

            cluster_info[cluster_id] = {
                'product_count': len(cluster_products),
                'dominant_style': dominant_style,
                'avg_warmth': float(avg_warmth)
            }

        return cluster_info

    def get_cluster_info(self, cluster_id: int) -> Dict:
        """
        특정 클러스터의 정보 반환

        Args:
            cluster_id: 클러스터 ID

        Returns:
            클러스터 정보 딕셔너리
        """
        return self.cluster_info.get(cluster_id, {})

    def save_model(self, save_path: str):
        """
        학습된 모델 저장

        Args:
            save_path: 저장 경로 (.pkl 파일)
        """
        if self.kmeans is None:
            raise ValueError("Model is not fitted yet. Call fit() first.")

        model_data = {
            'kmeans': self.kmeans,
            'scaler': self.scaler,
            'cluster_info': self.cluster_info,
            'n_clusters': self.n_clusters
        }

        joblib.dump(model_data, save_path)
        print(f"Model saved to {save_path}")

    def load_model(self, load_path: str):
        """
        저장된 모델 로드

        Args:
            load_path: 모델 파일 경로
        """
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Model file not found: {load_path}")

        model_data = joblib.load(load_path)

        self.kmeans = model_data['kmeans']
        self.scaler = model_data['scaler']
        self.cluster_info = model_data['cluster_info']
        self.n_clusters = model_data['n_clusters']

        print(f"Model loaded from {load_path}")

    def get_all_cluster_stats(self) -> List[Dict]:
        """
        모든 클러스터의 통계 정보 반환

        Returns:
            클러스터 정보 리스트
        """
        stats = []

        for cluster_id in range(self.n_clusters):
            info = self.cluster_info.get(cluster_id, {})
            stats.append({
                'cluster_id': cluster_id,
                **info
            })

        return stats
