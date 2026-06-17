from app.core.database import SessionLocal
from app.db.models import Map, Store, PriceLevel, User, UserMapAccess 
from app.core.security import get_password_hash 

def seed_database():
    db = SessionLocal()
    
    try:
        
        mock_user = User(
            first_name="Jae",
            last_name="Seo",
            email="test@gmail.com",
            hashed_password=get_password_hash("password123"),
            has_purchased_map=True
        )
        db.add(mock_user)
        db.commit()
        db.refresh(mock_user)

        
        sf_map = Map(
            title="San Francisco Thrift Tour",
            slug="sf-thrift-tour",
            description="A curated route through SF's best vintage and resale shops.",
            region="Bay Area",
            map_price=12
        )
        db.add(sf_map)
        db.commit()
        db.refresh(sf_map)

        
        access = UserMapAccess(
            user_id=mock_user.id,
            map_id=sf_map.id
        )
        db.add(access)

                
        bk_stores = [
            {
                "store_name": "Awoke Vintage", "description": "Colorful denim", "address": "132 N 5th St, BK", 
                "latitude": 40.7171, "longitude": -73.9575, "price_range": "4-45", "price_notes": "Premium vintage", 
                "hours": {"Mon": "10-21", "Tue": "10-21", "Wed": "10-21", "Thu": "10-21", "Fri": "10-21", "Sat": "10-21", "Sun": "10-21"}
            },
            {
                "store_name": "Beacon's Closet", "description": "Massive trade store", "address": "74 Guernsey St, BK", 
                "latitude": 40.7236, "longitude": -73.9566, "price_range": "2-45", "price_notes": "Budget friendly", 
                "hours": {"Mon": "11-20", "Tue": "11-20", "Wed": "11-20", "Thu": "11-20", "Fri": "11-20", "Sat": "11-20", "Sun": "11-20"}
            },
            {
                "store_name": "Stella Dallas", "description": "Archival focus", "address": "285 N 6th St, BK", 
                "latitude": 40.7161, "longitude": -73.9515, "price_range": "5-45", "price_notes": "Archive pricing", 
                "hours": {"Mon": "12-19", "Tue": "12-19", "Wed": "12-19", "Thu": "12-19", "Fri": "12-19", "Sat": "12-19", "Sun": "12-19"}
            },
            {
                "store_name": "L Train Vintage", "description": "Streetwear staples", "address": "629 Grand St, BK", 
                "latitude": 40.7118, "longitude": -73.9493, "price_range": "1-45", "price_notes": "Very cheap", 
                "hours": {"Mon": "12-19", "Tue": "12-19", "Wed": "12-19", "Thu": "12-19", "Fri": "12-19", "Sat": "12-19", "Sun": "12-19"}
            },
            {
                "store_name": "Crossroads Trading", "description": "Trendy mid-tier", "address": "135 N 7th St, BK", 
                "latitude": 40.7185, "longitude": -73.9571, "price_range": "3-45", "price_notes": "Standard mall brands", 
                "hours": {"Mon": "11-20", "Tue": "11-20", "Wed": "11-20", "Thu": "11-20", "Fri": "11-20", "Sat": "11-20", "Sun": "11-20"}
            },
            {
                "store_name": "Brooklyn Flea", "description": "Market vintage", "address": "80 Pearl St, BK", 
                "latitude": 40.7045, "longitude": -73.9912, "price_range": "4-45", "price_notes": "Varies by vendor", 
                "hours": {"Mon": "Closed", "Tue": "Closed", "Wed": "Closed", "Thu": "Closed", "Fri": "Closed", "Sat": "10-17", "Sun": "10-17"}
            },
            {
                "store_name": "Mother of Junk", "description": "Vintage home/apparel", "address": "567 Driggs Ave, BK", 
                "latitude": 40.7175, "longitude": -73.9550, "price_range": "3-45", "price_notes": "Mid-range", 
                "hours": {"Mon": "12-19", "Tue": "12-19", "Wed": "12-19", "Thu": "12-19", "Fri": "12-19", "Sat": "12-19", "Sun": "12-19"}
            },
            {
                "store_name": "Dobbin St Vintage", "description": "High-end curation", "address": "121 Dobbin St, BK", 
                "latitude": 40.7245, "longitude": -73.9555, "price_range": "5-45", "price_notes": "Luxury selection", 
                "hours": {"Mon": "12-18", "Tue": "12-18", "Wed": "12-18", "Thu": "12-18", "Fri": "12-18", "Sat": "12-18", "Sun": "12-18"}
            },
            {
                "store_name": "Tokio 7", "description": "Designer archive", "address": "83 E 7th St, NY", 
                "latitude": 40.7275, "longitude": -73.9855, "price_range": "5-45", "price_notes": "Designer prices", 
                "hours": {"Mon": "12-19", "Tue": "12-19", "Wed": "12-19", "Thu": "12-19", "Fri": "12-19", "Sat": "12-19", "Sun": "12-19"}
            },
            {
                "store_name": "Amarcord Vintage", "description": "Museum quality", "address": "223 Bedford Ave, BK", 
                "latitude": 40.7198, "longitude": -73.9582, "price_range": "5-45", "price_notes": "Collector focus", 
                "hours": {"Mon": "12-19", "Tue": "12-19", "Wed": "12-19", "Thu": "12-19", "Fri": "12-19", "Sat": "12-19", "Sun": "12-19"}
            }
        ]

        sf_stores = [
            {
                "store_name": "Goodwill – Fillmore", 
                "description": "Large charity anchor", 
                "address": "1669 Fillmore St, SF", 
                "latitude": 37.7845, 
                "longitude": -122.4330, 
                "price_range": "1-76", 
                "price_notes": "Very affordable", 
                "hours": {"Mon": "9-21", "Tue": "9-21", "Wed": "9-21", "Thu": "9-21", "Fri": "9-21", "Sat": "Closed", "Sun": "Closed"}
            },
            {
                "store_name": "Crossroads – Fillmore", 
                "description": "Buy/sell chain", 
                "address": "1901 Fillmore St, SF", 
                "latitude": 37.7878, 
                "longitude": -122.4336, 
                "price_range": "3-76", 
                "price_notes": "Moderate pricing", 
                "hours": {"Mon": "11-20", "Tue": "11-20", "Wed": "11-20", "Thu": "11-20", "Fri": "11-20", "Sat": "11-20", "Sun": "11-20"}
            },
            {
                "store_name": "Fashion Exchange", 
                "description": "Curated resale", 
                "address": "1446 Polk St, SF", 
                "latitude": 37.7903, 
                "longitude": -122.4204, 
                "price_range": "3-76", 
                "price_notes": "Mid-tier", 
                "hours": {"Mon": "11-18", "Tue": "11-18", "Wed": "11-18", "Thu": "11-18", "Fri": "11-18", "Sat": "11-18", "Sun": "11-18"}
            },
            {
                "store_name": "Big Sylvia’s Vintage", 
                "description": "Small vintage mix", 
                "address": "1167 Sutter St, SF", 
                "latitude": 37.7874, 
                "longitude": -122.4194, 
                "price_range": "4-76", 
                "price_notes": "Vintage premium", 
                "hours": {"Mon": "11-18", "Tue": "11-18", "Wed": "11-18", "Thu": "11-18", "Fri": "11-18", "Sat": "13-18", "Sun": "Closed"}
            },
            {
                "store_name": "Buffalo Exchange", 
                "description": "Consistent turnover", 
                "address": "1555 Haight St, SF", 
                "latitude": 37.7698, 
                "longitude": -122.4485, 
                "price_range": "2-76", 
                "price_notes": "Accessible", 
                "hours": {"Mon": "11-20", "Tue": "11-20", "Wed": "11-20", "Thu": "11-20", "Fri": "11-20", "Sat": "11-20", "Sun": "11-19"}
            },
            {
                "store_name": "2nd Street – Haight", 
                "description": "Japanese resale", 
                "address": "1560 Haight St, SF", 
                "latitude": 37.7698, 
                "longitude": -122.4487, 
                "price_range": "3-76", 
                "price_notes": "Good contemporary", 
                "hours": {"Mon": "11-20", "Tue": "11-20", "Wed": "11-20", "Thu": "11-20", "Fri": "11-20", "Sat": "11-20", "Sun": "11-20"}
            },
            {
                "store_name": "Sensitive Vintage", 
                "description": "Quick scan vintage", 
                "address": "802 Divisadero St, SF", 
                "latitude": 37.7777, 
                "longitude": -122.4382, 
                "price_range": "4-76", 
                "price_notes": "Curated", 
                "hours": {"Mon": "Closed", "Tue": "Closed", "Wed": "Closed", "Thu": "12-18", "Fri": "12-18", "Sat": "12-18", "Sun": "12-18"}
            },
            {
                "store_name": "Wasteland", 
                "description": "High-end vintage", 
                "address": "1660 Haight St, SF", 
                "latitude": 37.7696, 
                "longitude": -122.4491, 
                "price_range": "5-76", 
                "price_notes": "Expensive", 
                "hours": {"Mon": "11-19", "Tue": "11-19", "Wed": "11-19", "Thu": "11-19", "Fri": "11-19", "Sat": "11-19", "Sun": "11-19"}
            },
            {
                "store_name": "Relic Vintage", 
                "description": "True vintage focus", 
                "address": "1208 Haight St, SF", 
                "latitude": 37.7702, 
                "longitude": -122.4435, 
                "price_range": "4-76", 
                "price_notes": "Authentic eras", 
                "hours": {"Mon": "12-18", "Tue": "12-18", "Wed": "12-18", "Thu": "12-18", "Fri": "12-18", "Sat": "12-18", "Sun": "12-18"}
            },
            {
                "store_name": "Static Vintage", 
                "description": "Eclectic streetwear", 
                "address": "1764 Haight St, SF", 
                "latitude": 37.7695, 
                "longitude": -122.4505, 
                "price_range": "3-76", 
                "price_notes": "Street-style focus", 
                "hours": {"Mon": "12-19", "Tue": "12-19", "Wed": "12-19", "Thu": "12-19", "Fri": "12-19", "Sat": "12-19", "Sun": "12-19"}
            }
        ]
          
        
        for data in sf_stores:
            store = Store(
                map_id=sf_map.id,
                store_name=data["store_name"],
                address=data["address"],
                notes=data["description"],
                price_range=data.get("price_range"),
                latitude=float(data["latitude"]), 
                longitude=float(data["longitude"]), 
                hours=data.get("hours"), 
                price_notes=data.get("price_notes"), 
                price_level=PriceLevel.MODERATE, 
            )
            db.add(store)
        
        
        bk_map = Map(
            title="Brooklyn Archival & Vintage Tour",
            slug="bk-archival-tour",
            description="A premium route through Williamsburg and Greenpoint's best designer archives and vintage boutiques.",
            region="New York",
            map_price=15 
        )
        db.add(bk_map)
        db.commit()
        db.refresh(bk_map)

        

        
      
        for data in bk_stores:
            store = Store(
                map_id=bk_map.id,
                store_name=data["store_name"],
                address=data["address"],
                notes=data["description"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                price_level=PriceLevel.MODERATE, 
                price_range=data.get("price_range"),
                price_notes=data.get("price_notes"),
            )
            db.add(store)
            
    

        db.commit()
        print(f"Successfully seeded {len(bk_stores)} stores for map: {bk_map.title}")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()