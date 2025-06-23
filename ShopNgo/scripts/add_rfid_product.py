from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def add_rfid_product():
    """Add a product with your RFID tag"""
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    client = MongoClient(mongo_uri)
    db = client.shopngo

    # Your RFID tag UID
    rfid_uid = "53EEC752110001"  # Your actual RFID sticker
    
    # Product details
    product = {
        "name": "Apple",
        "price": 2.50,
        "category": "Fruits",
        "rfid_tag": rfid_uid,
        "stock_quantity": 100,
        "description": "Fresh red apple",
        "created_at": datetime.utcnow()
    }

    # Check if product already exists
    existing = db.products.find_one({"rfid_tag": rfid_uid})
    if existing:
        print(f"Product with RFID {rfid_uid} already exists: {existing['name']}")
        return

    # Insert product
    result = db.products.insert_one(product)
    print(f"✅ Product added successfully!")
    print(f"Name: {product['name']}")
    print(f"Price: ${product['price']}")
    print(f"RFID Tag: {product['rfid_tag']}")
    print(f"ID: {result.inserted_id}")
    
    print(f"\n🎯 Now when you scan your RFID sticker, it will add {product['name']} to the cart!")

if __name__ == "__main__":
    add_rfid_product() 