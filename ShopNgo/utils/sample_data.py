from pymongo import MongoClient
from datetime import datetime

def create_sample_branches():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['shopngo']
    
    # Sample branch data (using real locations in Egypt)
    branches = [
        {
            "name": "City Stars Branch",
            "address": "City Stars Mall, Heliopolis, Cairo",
            "latitude": 30.0626,
            "longitude": 31.4447,
            "phone": "+20 2 2480 0000",
            "opening_hours": "10:00-22:00",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Mall of Egypt Branch",
            "address": "Mall of Egypt, Giza",
            "latitude": 30.0131,
            "longitude": 31.2089,
            "phone": "+20 2 3537 0000",
            "opening_hours": "10:00-22:00",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Cairo Festival City Branch",
            "address": "Cairo Festival City Mall, New Cairo",
            "latitude": 30.0307,
            "longitude": 31.4707,
            "phone": "+20 2 2619 0000",
            "opening_hours": "10:00-22:00",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Alexandria City Center Branch",
            "address": "Alexandria City Center, Alexandria",
            "latitude": 31.2195,
            "longitude": 29.9462,
            "phone": "+20 3 483 0000",
            "opening_hours": "10:00-22:00",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Mansoura Branch",
            "address": "Mansoura City Center, Mansoura",
            "latitude": 31.0409,
            "longitude": 31.3785,
            "phone": "+20 50 230 0000",
            "opening_hours": "10:00-22:00",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Clear existing branches
    db.branches.delete_many({})
    
    # Insert new branches
    result = db.branches.insert_many(branches)
    
    print(f"Successfully inserted {len(result.inserted_ids)} branches")
    
    # Create indexes
    db.branches.create_index([("latitude", 1), ("longitude", 1)])
    db.branches.create_index("name")
    
    return result.inserted_ids

if __name__ == "__main__":
    create_sample_branches() 