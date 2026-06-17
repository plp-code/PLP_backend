from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core.security import create_access_token, get_password_hash, verify_password

from app.schemas.user import UserChangePassword, UserCreate, UserResponse
from app.services.user import UserService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
    
    
    access_token = create_access_token(data={"sub": str(new_user.id)})

    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True, 
        max_age=1800,  
        expires=1800,
        samesite="lax",
        secure=False, # true for production  
    )

    return new_user

@router.put("/change-password", response_model=UserResponse)
def change_password(
    password_data: UserChangePassword, 
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user) #can do with admin later
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
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticates a user and returns a secure JWT.
    Note: OAuth2PasswordRequestForm strictly uses the field name 'username', 
    so we map form_data.username to our database's email column.
    """
    user = UserService.get_by_email(db, email=form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token =  create_access_token(data={"sub": str(user.id)})

    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True, 
        max_age=1800,  
        expires=1800,
        samesite="lax",
        secure=True,  
    )

    return {"message": "Successfully logged in"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="auth_token",
        httponly=True,
        samesite="lax",
        secure=True, 
    )
    return {"message": "Successfully logged out"}