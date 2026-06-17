
from app.core.database import SessionLocal
from app.db.models import Store, User, Map, UserMapAccess
from app.core.security import get_password_hash

def drop_database():
    
    db = SessionLocal()

    try:
        print("Wiping old data...")
        db.query(UserMapAccess).delete()
        db.query(Map).delete()
        db.query(User).delete()
        db.query(Store).delete()
        db.commit()

    except Exception as e:
        print(f"Error wiping data: {e}")
        db.rollback()


if __name__ == "__main__":
    drop_database()