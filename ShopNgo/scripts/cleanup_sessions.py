from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def cleanup_sessions():
    """Check and clean up any remaining active sessions"""
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    client = MongoClient(mongo_uri)
    db = client.shopngo

    # Find all active sessions
    active_sessions = list(db.sessions.find({"is_active": True}))
    print(f"Found {len(active_sessions)} active sessions:")
    
    for session in active_sessions:
        print(f"\nSession ID: {session['_id']}")
        print(f"User Email: {session.get('user_email', 'N/A')}")
        print(f"Started At: {session.get('started_at', 'N/A')}")
        print(f"Cart ID: {session.get('cart_id', 'N/A')}")
        print(f"Items: {len(session.get('items', []))}")
        print(f"Total Amount: {session.get('total_amount', 0)}")

    if active_sessions:
        # Get cart IDs from active sessions
        cart_ids = [session["cart_id"] for session in active_sessions]
        
        # Update all carts to available
        result = db.carts.update_many(
            {"_id": {"$in": cart_ids}},
            {"$set": {"is_available": True}}
        )
        print(f"\nUpdated {result.modified_count} carts to available")
        
        # End all active sessions
        result = db.sessions.update_many(
            {"is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "ended_at": datetime.utcnow(),
                    "ended_by": "manual_cleanup"
                }
            }
        )
        print(f"Ended {result.modified_count} active sessions")
    else:
        print("\nNo active sessions found")

if __name__ == "__main__":
    cleanup_sessions() 