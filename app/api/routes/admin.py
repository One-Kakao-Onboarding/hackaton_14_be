"""
관리자 API 라우트 (Clustering, 통계)
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ClusterRebuildRequest,
    ClusterRebuildResponse,
    ClusterStatsResponse,
    ClusterStats,
    ErrorResponse
)
from app.core.clustering import ProductClusterManager
import time

router = APIRouter()

# 전역 Cluster Manager
# TODO: 실제 환경에서는 모델 파일 경로 지정
cluster_manager = ProductClusterManager(n_clusters=20)


@router.post(
    "/rebuild-clusters",
    response_model=ClusterRebuildResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def rebuild_clusters(request: ClusterRebuildRequest):
    """
    상품 클러스터 재생성

    모든 상품의 mood_vector를 기반으로 K-Means Clustering을 수행합니다.
    """
    try:
        start_time = time.time()

        # TODO: DB에서 모든 상품의 mood_vector 가져오기
        # 현재는 Mock 데이터
        mock_products = [
            {
                'product_id': f'prod_{i:03d}',
                'mood_vector': [0.5 + (i % 10) * 0.05] * 20,
                'primary_keyword': 'natural_wood'
            }
            for i in range(100)
        ]

        # Clustering 수행
        cluster_manager.n_clusters = request.n_clusters
        clustering_result = cluster_manager.fit(mock_products)

        # TODO: DB에 cluster_id 업데이트
        # for product in mock_products:
        #     update_product_cluster_id(product['product_id'], product['cluster_id'])

        # 클러스터 모델 저장
        # cluster_manager.save_model('models/kmeans_cluster.pkl')

        processing_time = time.time() - start_time

        return ClusterRebuildResponse(
            success=True,
            total_products=clustering_result['total_products'],
            clusters_created=clustering_result['n_clusters'],
            avg_cluster_size=clustering_result['total_products'] / clustering_result['n_clusters'],
            clustering_time_seconds=round(processing_time, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")


@router.get(
    "/cluster-stats",
    response_model=ClusterStatsResponse,
    responses={500: {"model": ErrorResponse}}
)
async def get_cluster_stats():
    """
    클러스터 분포 통계 조회

    각 클러스터의 상품 개수, 주요 스타일, 평균 warmth 등을 반환합니다.
    """
    try:
        # Cluster Manager가 초기화되지 않은 경우
        if cluster_manager.kmeans is None:
            return ClusterStatsResponse(
                success=True,
                total_clusters=0,
                cluster_distribution=[]
            )

        # 클러스터 통계 가져오기
        stats = cluster_manager.get_all_cluster_stats()

        cluster_distribution = [
            ClusterStats(
                cluster_id=s['cluster_id'],
                product_count=s['product_count'],
                dominant_style=s['dominant_style'],
                avg_warmth=s['avg_warmth']
            )
            for s in stats
        ]

        return ClusterStatsResponse(
            success=True,
            total_clusters=len(stats),
            cluster_distribution=cluster_distribution
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get(
    "/cluster/{cluster_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_cluster_info(cluster_id: int):
    """
    특정 클러스터의 상세 정보 조회

    TODO: DB 연동 후 구현
    """
    if cluster_manager.kmeans is None:
        raise HTTPException(status_code=404, detail="Clustering not initialized")

    if cluster_id < 0 or cluster_id >= cluster_manager.n_clusters:
        raise HTTPException(status_code=404, detail="Cluster not found")

    info = cluster_manager.get_cluster_info(cluster_id)

    return {
        "success": True,
        "cluster_id": cluster_id,
        "cluster_info": info,
        "message": "TODO: Add product list from DB"
    }
