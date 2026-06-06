"""
Project management endpoints.
"""
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.project import Project
from app.models.memory_capsule import MemoryCapsule
from app.schemas.schemas import ProjectCreate, ProjectOut, CapsuleOut

router = APIRouter()
logger = structlog.get_logger()

# Phase 1: single-user, fixed user ID (local mode)
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.get("/", response_model=List[ProjectOut], summary="List all projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED,
             summary="Create a new project")
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        user_id=DEFAULT_USER_ID,
        name=payload.name,
        description=payload.description,
        color=payload.color,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    logger.info("project_created", project_id=str(project.id), name=project.name)
    return project


@router.get("/{project_id}", response_model=ProjectOut, summary="Get project by ID")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a project")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/timeline", response_model=List[CapsuleOut], summary="Get project timeline")
async def get_project_timeline(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MemoryCapsule)
        .where(MemoryCapsule.project_id == project_id)
        .order_by(MemoryCapsule.created_at.asc())
    )
    return result.scalars().all()
