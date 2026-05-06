# user_assets_routes.py — API каталога пользовательских материалов (лаб. №3)
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import ValidationError

from auth import get_current_active_user
from schemas import (
    PresignedUrlResponse,
    User,
    UserAssetCreateBody,
    UserAssetListResponse,
    UserAssetResponse,
    UserAssetUpdateBody,
)
from user_asset_service import UserAssetService, get_user_asset_service

router = APIRouter(prefix="/user-assets", tags=["user-assets"])


# Более длинные пути — выше, чтобы не перехватывались /{asset_id}


@router.get("", response_model=UserAssetListResponse)
async def list_user_assets(
    current_user: User = Depends(get_current_active_user),
    svc: UserAssetService = Depends(get_user_asset_service),
    q: Optional[str] = Query(None, max_length=200, description="Поиск по названию, описанию, имени файла"),
    category: Optional[str] = Query(None, max_length=50),
    date_from: Optional[date] = Query(None, description="Фильтр: создано с даты (UTC)"),
    date_to: Optional[date] = Query(None, description="Фильтр: создано по дату (UTC)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Literal["created_at", "title", "size_bytes", "original_filename"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    all_users: bool = Query(False, description="Список всех пользователей (нужно files.view_all)"),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from не может быть позже date_to")
    return svc.list_assets(
        current_user,
        q=q,
        category=category,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        all_users=all_users,
    )


@router.get("/{asset_id}/download-url", response_model=PresignedUrlResponse)
async def get_download_presigned(
    asset_id: int,
    current_user: User = Depends(get_current_active_user),
    svc: UserAssetService = Depends(get_user_asset_service),
    expires_seconds: int = Query(3600, ge=60, le=86400),
):
    url, cap = svc.presigned_download(current_user, asset_id, expires_seconds=expires_seconds)
    return PresignedUrlResponse(url=url, expires_in=cap)


@router.get("/{asset_id}", response_model=UserAssetResponse)
async def get_user_asset(
    asset_id: int,
    current_user: User = Depends(get_current_active_user),
    svc: UserAssetService = Depends(get_user_asset_service),
):
    return svc.get_one(current_user, asset_id)


@router.post("", response_model=UserAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_user_asset(
    current_user: User = Depends(get_current_active_user),
    svc: UserAssetService = Depends(get_user_asset_service),
    title: str = Form(..., min_length=1, max_length=200),
    description: Optional[str] = Form(None, max_length=2000),
    category: str = Form("general", max_length=50),
    file: UploadFile = File(...),
):
    try:
        meta = UserAssetCreateBody(title=title, description=description, category=category)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    return await svc.create_with_upload(
        current_user,
        file,
        meta.title,
        meta.description,
        meta.category,
    )


@router.put("/{asset_id}", response_model=UserAssetResponse)
async def update_user_asset(
    asset_id: int,
    body: UserAssetUpdateBody,
    current_user: User = Depends(get_current_active_user),
    svc: UserAssetService = Depends(get_user_asset_service),
):
    return svc.update_meta(current_user, asset_id, body)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_asset(
    asset_id: int,
    current_user: User = Depends(get_current_active_user),
    svc: UserAssetService = Depends(get_user_asset_service),
):
    svc.delete_asset(current_user, asset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
