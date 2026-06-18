from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserCreate

class UserService:
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Fetch a user by their unique email address."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user: UserCreate, hashed_password: str) -> User:
        """Register a brand new user into the database."""
        db_obj = User(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
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
    
    @staticmethod
    def get_profile_with_maps(db: Session, user_id: int) -> User | None:
        """Fetches a user along with their purchased maps for profile display."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def grant_user_map_access(db: Session, user_id: int, map_id: int):
        """Grants a user access to a specific map after purchase."""
        from app.db.models import UserMapAccess
        access_record = UserMapAccess(user_id=user_id, map_id=map_id)
        db.add(access_record)
        db.commit()