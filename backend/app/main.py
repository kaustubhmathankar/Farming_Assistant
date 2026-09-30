from contextlib import asynccontextmanager
from app.models import utcnow_naive

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import delete

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import RevokedToken
from app.routers import admin, agent, auth, conversations, farmers
from app.services.security_headers import SecurityHeadersMiddleware




@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.execute(delete(RevokedToken).where(RevokedToken.expires_at < utcnow_naive()))
        db.commit()
    yield
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.app_env.lower() != "production" else None,
    redoc_url="/redoc" if settings.app_env.lower() != "production" else None,
    lifespan=lifespan,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(farmers.router, prefix=settings.api_prefix)
app.include_router(conversations.router, prefix=settings.api_prefix)
app.include_router(agent.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "ok", "version": settings.app_version}


@app.get("/health")
def health():
    return {"status": "healthy"}
