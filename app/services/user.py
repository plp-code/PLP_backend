from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserCreate

class UserService:
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Fetch a user by their unique email address."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, obj_in: UserCreate, hashed_password: str) -> User:
        """Register a brand new user into the database."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=hashed_password,
            has_purchased_map=False  
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_password(db: Session, user: User, hashed_password: str) -> User:
        """Updates a user's password in the database."""
        user.hashed_password = hashed_password
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    