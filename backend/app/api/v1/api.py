from fastapi import APIRouter
from app.api.v1.endpoints import ingest, retrieval, capsules, projects, inject, diagnostics, entities

api_router = APIRouter()

api_router.include_router(ingest.router,    prefix="/ingest",    tags=["ingestion"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
api_router.include_router(capsules.router,  prefix="/capsules",  tags=["capsules"])
api_router.include_router(projects.router,  prefix="/projects",  tags=["projects"])
api_router.include_router(inject.router,    prefix="/inject",    tags=["injection"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(entities.router, prefix="/entities", tags=["entities"])
