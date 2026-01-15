"""
Redis 캐싱 모듈
자주 조회되는 데이터를 캐싱하여 성능 향상
"""
import redis
import json
import pickle
from typing import Any, Optional, Callable
from functools import wraps
from app.core.config import settings


class RedisCache:
    """
    Redis 캐시 관리 클래스
    """

    def __init__(self):
        """Redis 연결 초기화"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False  # Binary 데이터 지원
            )
            # 연결 테스트
            self.redis_client.ping()
            self.enabled = True
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            self.redis_client = None
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 가져오기

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 (없으면 None)
        """
        if not self.enabled:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: Time To Live (초), None이면 기본값 사용
        """
        if not self.enabled:
            return

        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            pickled_value = pickle.dumps(value)
            self.redis_client.setex(key, ttl, pickled_value)
        except Exception as e:
            print(f"Cache set error: {e}")

    def delete(self, key: str):
        """
        캐시에서 값 삭제

        Args:
            key: 캐시 키
        """
        if not self.enabled:
            return

        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")

    def delete_pattern(self, pattern: str):
        """
        패턴에 맞는 모든 키 삭제

        Args:
            pattern: 키 패턴 (예: "product:*")
        """
        if not self.enabled:
            return

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")

    def exists(self, key: str) -> bool:
        """
        캐시에 키가 존재하는지 확인

        Args:
            key: 캐시 키

        Returns:
            존재하면 True, 아니면 False
        """
        if not self.enabled:
            return False

        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    def flush_all(self):
        """모든 캐시 삭제"""
        if not self.enabled:
            return

        try:
            self.redis_client.flushdb()
            print("✅ All cache cleared")
        except Exception as e:
            print(f"Cache flush error: {e}")

    def get_stats(self) -> dict:
        """캐시 통계 정보 반환"""
        if not self.enabled:
            return {'enabled': False}

        try:
            info = self.redis_client.info()
            return {
                'enabled': True,
                'used_memory': info.get('used_memory_human'),
                'keys': self.redis_client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            return {'enabled': True, 'error': str(e)}


# 전역 캐시 인스턴스
cache = RedisCache()


def cached(key_prefix: str, ttl: Optional[int] = None):
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        key_prefix: 캐시 키 접두사
        ttl: Time To Live (초)

    Example:
        @cached("product_analysis", ttl=3600)
        def analyze_product(product_id: str):
            # 무거운 연산
            return result
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 캐시 확인
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 함수 실행
            result = func(*args, **kwargs)

            # 캐시 저장
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# ===== 캐시 키 헬퍼 함수 =====

def get_product_cache_key(product_id: str) -> str:
    """상품 캐시 키 생성"""
    return f"product:{product_id}"


def get_analysis_cache_key(image_hash: str) -> str:
    """분석 결과 캐시 키 생성"""
    return f"analysis:{image_hash}"


def get_recommendation_cache_key(bg_hash: str, top_k: int) -> str:
    """추천 결과 캐시 키 생성"""
    return f"recommend:{bg_hash}:{top_k}"


def get_cluster_cache_key(cluster_id: int) -> str:
    """클러스터 캐시 키 생성"""
    return f"cluster:{cluster_id}"
