from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from app.api import deps
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password, decode_token, set_auth_cookie

from app.schemas.user import UserChangePassword, UserCreate, UserResponse, LoginRequest
from app.services.user import UserService

router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate, 
    response: Response,
    db: Session = Depends(deps.get_db)
):
    """
    Registers a new user, auto-logs them in by setting a secure JWT cookie, 
    and returns the user profile.
    """
    user = UserService.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    
    new_user = UserService.create(db, user=user_in, hashed_password=hashed_password)
        
    
    access_token = create_access_token(data={"sub": str(new_user.id)}, expires_delta=timedelta(minutes=15))
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)}, expires_delta=timedelta(days=7))

    set_auth_cookie(response, "access_token", f"Bearer {access_token}")
    set_auth_cookie(response, "refresh_token", f"Bearer {refresh_token}", 7*24*60*60, "/api/v1/auth/refresh")
        
    return {"message": "User registered successfully"}


@router.put("/change-password", response_model=UserResponse)
def change_password(
    password_data: UserChangePassword, 
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user) 
):
    """
    Allows a logged-in user to safely change their password.
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    new_hashed_password = get_password_hash(password_data.new_password)
    
    UserService.update_password(db, user=current_user, hashed_password=new_hashed_password)
    
    return current_user

@router.post("/login", response_model=dict)
def login_user(
    response: Response,
    data: LoginRequest, 
    db: Session = Depends(deps.get_db),
):
    """
    Authenticates a user via JSON body and sets secure JWT cookies.
    """
    user = UserService.get_by_email(db, email=data.email)
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(minutes=15))
    refresh_token = create_refresh_token(data={"sub": str(user.id)}, expires_delta=timedelta(days=7))
    
    set_auth_cookie(response, "access_token", f"Bearer {access_token}")
    set_auth_cookie(response, "refresh_token", f"Bearer {refresh_token}", 7*24*60*60, "/api/v1/auth/refresh")
    
    return {"message": "Logged in"}

@router.post("/refresh")
def refresh_session(response: Response, refresh_token: str = Cookie(None)):
    """
    Refreshes the access token using the refresh token cookie.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = decode_token(refresh_token, expected_type="refresh")
    
    user_id_string = payload.get("sub")
    
    if not user_id_string:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    new_access_token = create_access_token(
        data={"sub": str(user_id_string)}, 
        expires_delta=timedelta(minutes=15)
    )

    set_auth_cookie(response, "access_token", f"Bearer {new_access_token}")
    return {"message": "Token refreshed"}


@router.post("/logout")
def logout(response: Response):
    """
    Logs out the user by clearing the authentication cookies.
    """
    
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    
    return {"message": "Logged out"}