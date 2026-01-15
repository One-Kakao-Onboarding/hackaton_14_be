"""
데이터베이스 연동 모듈
PostgreSQL + pgvector를 사용한 상품 데이터 관리
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, TIMESTAMP, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings

# SQLAlchemy Base
Base = declarative_base()


# ============================================================
# Models
# ============================================================

class Product(Base):
    """
    상품 테이블 모델
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), index=True)
    price = Column(Integer)
    image_url = Column(Text)
    removed_bg_image_base64 = Column(Text)

    # Mood Vector (pgvector)
    mood_vector = Column(Vector(20))

    # Color Features
    dominant_hex_1 = Column(String(7))
    dominant_hex_2 = Column(String(7))
    warmth_score = Column(Float)

    # Physics Features
    circularity = Column(Float)
    glossiness = Column(Float)
    complexity = Column(Float)

    # Style Features
    primary_keyword = Column(String(50), index=True)
    primary_score = Column(Float)
    category_style = Column(String(50))
    style_vector = Column(JSON)

    # Clustering
    cluster_id = Column(Integer, index=True)

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class Cluster(Base):
    """
    클러스터 테이블 모델
    """
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cluster_id = Column(Integer, unique=True, nullable=False, index=True)
    centroid_vector = Column(Vector(20))
    product_count = Column(Integer, default=0)
    dominant_style = Column(String(50))
    avg_warmth_score = Column(Float)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# ============================================================
# Database Connection
# ============================================================

# 동기 엔진 생성
engine = create_engine(
    settings.database_url_sync,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DEBUG
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    데이터베이스 초기화
    테이블 생성 및 pgvector Extension 활성화
    """
    # pgvector Extension 생성 (raw SQL)
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully")


def get_db() -> Session:
    """
    FastAPI Depends용 DB 세션 생성기
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# CRUD Operations
# ============================================================

class ProductCRUD:
    """
    상품 CRUD 연산
    """

    @staticmethod
    def create_product(db: Session, product_data: Dict) -> Product:
        """
        상품 생성
        """
        product = Product(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
        """
        product_id로 상품 조회
        """
        return db.query(Product).filter(Product.product_id == product_id).first()

    @staticmethod
    def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: bool = True
    ) -> List[Product]:
        """
        상품 목록 조회 (필터링)
        """
        query = db.query(Product).filter(Product.is_active == is_active)

        if category:
            query = query.filter(Product.category == category)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_product(db: Session, product_id: str, update_data: Dict) -> Optional[Product]:
        """
        상품 업데이트
        """
        product = ProductCRUD.get_product_by_id(db, product_id)
        if not product:
            return None

        for key, value in update_data.items():
            setattr(product, key, value)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: str, soft_delete: bool = True) -> bool:
        """
        상품 삭제 (소프트 삭제 또는 하드 삭제)
        """
        product = ProductCRUD.get_product_by_id(db, product_id)
        if not product:
            return False

        if soft_delete:
            product.is_active = False
            db.commit()
        else:
            db.delete(product)
            db.commit()

        return True

    @staticmethod
    def search_similar_products(
        db: Session,
        mood_vector: List[float],
        top_k: int = 10,
        cluster_id: Optional[int] = None,
        category: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Mood Vector 기반 유사 상품 검색 (pgvector)

        Args:
            db: DB 세션
            mood_vector: 검색할 무드 벡터 (20차원)
            top_k: 반환할 상품 개수
            cluster_id: 특정 클러스터 내에서만 검색
            category: 카테고리 필터
            min_score: 최소 유사도 점수

        Returns:
            유사도 순으로 정렬된 상품 리스트
        """
        from sqlalchemy import text

        # Vector를 문자열로 변환
        vector_str = '[' + ','.join(map(str, mood_vector)) + ']'

        # 기본 쿼리
        query = f"""
        SELECT
            product_id,
            name,
            category,
            price,
            image_url,
            removed_bg_image_base64,
            primary_keyword,
            cluster_id,
            mood_vector,
            1 - (mood_vector <=> '{vector_str}') AS similarity
        FROM products
        WHERE is_active = true
        """

        # 필터 추가
        if cluster_id is not None:
            query += f" AND cluster_id = {cluster_id}"

        if category:
            query += f" AND category = '{category}'"

        if min_score > 0:
            query += f" AND (1 - (mood_vector <=> '{vector_str}')) >= {min_score}"

        # 정렬 및 제한
        query += f"""
        ORDER BY mood_vector <=> '{vector_str}'
        LIMIT {top_k}
        """

        result = db.execute(text(query))
        rows = result.fetchall()

        # 딕셔너리 리스트로 변환
        products = []
        for row in rows:
            # mood_vector는 문자열로 반환되므로 파싱 필요
            mood_vec_str = row[8]
            if mood_vec_str:
                # '[0.1,0.2,...]' 형식을 리스트로 변환
                mood_vec = eval(mood_vec_str) if isinstance(mood_vec_str, str) else mood_vec_str
            else:
                mood_vec = None

            products.append({
                'product_id': row[0],
                'name': row[1],
                'category': row[2],
                'price': row[3],
                'image_url': row[4],
                'removed_bg_image_base64': row[5],
                'primary_keyword': row[6],
                'cluster_id': row[7],
                'mood_vector': mood_vec,
                'similarity': float(row[9])
            })

        return products

    @staticmethod
    def get_products_by_cluster(db: Session, cluster_id: int) -> List[Product]:
        """
        특정 클러스터의 모든 상품 조회
        """
        return db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.is_active == True
        ).all()

    @staticmethod
    def count_products(db: Session, is_active: bool = True) -> int:
        """
        활성 상품 개수
        """
        return db.query(Product).filter(Product.is_active == is_active).count()


class ClusterCRUD:
    """
    클러스터 CRUD 연산
    """

    @staticmethod
    def create_or_update_cluster(db: Session, cluster_data: Dict) -> Cluster:
        """
        클러스터 생성 또는 업데이트
        """
        cluster = db.query(Cluster).filter(
            Cluster.cluster_id == cluster_data['cluster_id']
        ).first()

        if cluster:
            # 업데이트
            for key, value in cluster_data.items():
                setattr(cluster, key, value)
        else:
            # 생성
            cluster = Cluster(**cluster_data)
            db.add(cluster)

        db.commit()
        db.refresh(cluster)
        return cluster

    @staticmethod
    def get_cluster(db: Session, cluster_id: int) -> Optional[Cluster]:
        """
        클러스터 조회
        """
        return db.query(Cluster).filter(Cluster.cluster_id == cluster_id).first()

    @staticmethod
    def get_all_clusters(db: Session) -> List[Cluster]:
        """
        모든 클러스터 조회
        """
        return db.query(Cluster).order_by(Cluster.cluster_id).all()

    @staticmethod
    def delete_all_clusters(db: Session):
        """
        모든 클러스터 삭제 (재클러스터링 시)
        """
        db.query(Cluster).delete()
        db.commit()


# ============================================================
# Helper Functions
# ============================================================

def product_to_dict(product: Product) -> Dict:
    """
    Product 모델을 딕셔너리로 변환
    """
    return {
        'id': product.id,
        'product_id': product.product_id,
        'name': product.name,
        'category': product.category,
        'price': product.price,
        'image_url': product.image_url,
        'mood_vector': product.mood_vector,
        'colors': {
            'dominant_hex': [product.dominant_hex_1, product.dominant_hex_2],
            'warmth_score': product.warmth_score
        },
        'physics': {
            'circularity': product.circularity,
            'glossiness': product.glossiness,
            'complexity': product.complexity
        },
        'style': {
            'primary_keyword': product.primary_keyword,
            'primary_score': product.primary_score,
            'category': product.category_style,
            'vector_breakdown': product.style_vector
        },
        'cluster_id': product.cluster_id,
        'created_at': product.created_at,
        'updated_at': product.updated_at,
        'is_active': product.is_active
    }
