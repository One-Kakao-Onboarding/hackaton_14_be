"""
데이터베이스 초기화 스크립트
"""
import sys
sys.path.append('..')

from app.database import init_db, engine, SessionLocal
from sqlalchemy import text


def main():
    """데이터베이스 초기화"""
    print("🚀 Initializing database...")

    try:
        # pgvector Extension 활성화 및 테이블 생성
        init_db()

        # 연결 테스트
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL version: {version[:50]}...")

            # pgvector Extension 확인
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector extension is installed")
            else:
                print("⚠️  pgvector extension not found")

        print("\n✅ Database initialization completed!")
        print("\nNext steps:")
        print("1. Run the FastAPI server: python app/main.py")
        print("2. Access Swagger UI: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
