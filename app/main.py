"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analyze, recommend, admin, smart_recommend, ai_interior
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = FastAPI(
    title="Interior Mood Matching API",
    description="인테리어 무드 매칭 및 상품 추천 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(ai_interior.router, prefix="/api", tags=["AI Interior"])
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(recommend.router, prefix="/api/v1", tags=["Recommendation"])
app.include_router(smart_recommend.router, prefix="/api/v1", tags=["Smart Recommendation"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/")
async def root():
    """헬스체크"""
    return {
        "service": "Interior Mood Matching API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """헬스체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
