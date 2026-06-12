
from app.core.database import SessionLocal
from app.db.models import User, Map, UserMapAccess
from app.core.security import get_password_hash

def seed_database():
    
    db = SessionLocal()

    try:
        print("Wiping old data...")
        db.query(UserMapAccess).delete()
        db.query(Map).delete()
        db.query(User).delete()
        db.commit()

    except Exception as e:
        print(f"Error wiping data: {e}")
        db.rollback()

    try:
        print("Seeding database...")

        mock_user = User(
            email="test_buyer@example.com",
            hashed_password=get_password_hash("fake_hashed_password_12345"), 
            is_active=True,
            has_purchased_map=True
        )

        mock_user2 = User(
            email="jaeyseo0922@gmail.com",
            hashed_password=get_password_hash("testing123"),
            is_active=True,
            has_purchased_map=False
        )  

        db.add(mock_user2)

        db.add(mock_user)
        db.commit()
        db.refresh(mock_user) 
        

        
        map_bought = Map(
            title="Tokyo Hidden Ramen Guide",
            slug="tokyo-ramen",
            description="The best under-the-radar ramen spots.",
            google_embed_url="https://www.google.com/maps/d/embed?mid=fake_tokyo_123"
        )
        
        map_unbought = Map(
            title="New York Coffee Tour",
            slug="nyc-coffee",
            description="A walking map of Brooklyn cafes.",
            google_embed_url="https://www.google.com/maps/d/embed?mid=fake_nyc_456"
        )
        
        db.add_all([map_bought, map_unbought])
        db.commit()
        db.refresh(map_bought)
        db.refresh(map_unbought)

        
        
        purchase_record = UserMapAccess(
            user_id=mock_user.id,
            map_id=map_bought.id
        )
        
        db.add(purchase_record)
        db.commit()

        print("Success! Database seeded.")
        print(f"Created User: {mock_user.email}")
        print(f"Created Maps: '{map_bought.title}' & '{map_unbought.title}'")
        print(f"Linked '{map_bought.title}' to user as a purchase.")

    except Exception as e:
        print(f"Error inserting data: {e}")
        
        db.rollback() 
    finally:
        
        db.close()

if __name__ == "__main__":
    seed_database()