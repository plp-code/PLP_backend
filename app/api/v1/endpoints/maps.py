from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import literal
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.db.models import Map, UserMapAccess, Store, User
from app.schemas.store import StoreMinimalResponse, StoreResponse
from app.schemas.map import MapResponse

router = APIRouter()


@router.get("/", response_model=List[MapResponse])
def get_maps(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user_optional)
):
    maps = db.query(Map).all()
    current_user_id = current_user.id if current_user else None 
    
    user_access_ids = {
        access.map_id for access in db.query(UserMapAccess.map_id)
        .filter(UserMapAccess.user_id == current_user_id)
        .all()
    }
    
    for map_item in maps:
        map_item.has_access = map_item.id in user_access_ids
        
    return maps

@router.get("/{map_slug}/stores/minimal", response_model=List[StoreMinimalResponse])
def get_map_pins(
    map_slug: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    map_obj = db.query(Map).join(UserMapAccess).filter(
        Map.slug == map_slug,
        UserMapAccess.user_id == current_user.id
    ).first()
    
    if not map_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(Store).filter(Store.map_id == map_obj.id).all()

@router.get("/{map_slug}/stores", response_model=List[StoreResponse])
def get_stores_paginated(
    map_slug: str, 
    page: int = 1, 
    limit: int = 5, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    map_obj = db.query(Map).join(UserMapAccess).filter(
        Map.slug == map_slug,
        UserMapAccess.user_id == current_user.id
    ).first()

    if not map_obj:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return db.query(Store).filter(
        Store.map_id == map_obj.id
    ).order_by(Store.id).offset((page - 1) * limit).limit(limit).all()