from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def init_carts():
    """Initialize the 10 physical carts in the database"""
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    client = MongoClient(mongo_uri)
    db = client.shopngo

    # Check if carts already exist
    existing_carts = db.carts.count_documents({})
    if existing_carts > 0:
        print(f"Found {existing_carts} existing carts. Skipping initialization.")
        return

    # Create carts
    carts = []
    for i in range(1, 11):
        cart = {
            "cart_number": i,
            "barcode": f"CART{i:03d}",  # CART001, CART002, etc.
            "is_available": True,
            "created_at": datetime.utcnow()
        }
        carts.append(cart)

    # Insert carts
    result = db.carts.insert_many(carts)
    print(f"Successfully initialized {len(result.inserted_ids)} carts:")
    for cart in carts:
        print(f"- Cart {cart['cart_number']}: {cart['barcode']}")

if __name__ == "__main__":
    init_carts() 