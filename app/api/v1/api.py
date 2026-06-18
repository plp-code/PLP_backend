from fastapi import APIRouter
from app.api.v1.endpoints import auth, user, maps, checkout

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(maps.router, prefix="/maps", tags=["maps"])
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
