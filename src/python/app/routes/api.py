from fastapi import APIRouter

from src.python.app.routes import auth, checkout, maps, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(maps.router, prefix="/maps", tags=["maps"])
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
