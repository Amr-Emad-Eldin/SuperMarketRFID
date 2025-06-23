from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def create_test_products():
    """Create test products with RFID tags for testing"""
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    client = MongoClient(mongo_uri)
    db = client.shopngo

    # Test products with RFID tags
    test_products = [
        {
            "name": "Apple",
            "price": 2.50,
            "category": "Fruits",
            "rfid_tag": "53EEC752110001",  # Your actual RFID UID
            "stock_quantity": 100,
            "description": "Fresh red apple",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Banana",
            "price": 1.75,
            "category": "Fruits", 
            "rfid_tag": "04A3B2C1D0E9F8",  # Another test RFID
            "stock_quantity": 50,
            "description": "Yellow banana",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Milk",
            "price": 3.99,
            "category": "Dairy",
            "rfid_tag": "1234567890ABCD",  # Another test RFID
            "stock_quantity": 25,
            "description": "Fresh whole milk",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Bread",
            "price": 2.25,
            "category": "Bakery",
            "rfid_tag": "ABCDEF123456",  # Another test RFID
            "stock_quantity": 30,
            "description": "Fresh white bread",
            "created_at": datetime.utcnow()
        }
    ]

    # Check if products already exist
    existing_products = db.products.count_documents({})
    if existing_products > 0:
        print(f"Found {existing_products} existing products.")
        response = input("Do you want to add test products anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Insert products
    result = db.products.insert_many(test_products)
    print(f"Successfully created {len(result.inserted_ids)} test products:")
    
    for product in test_products:
        print(f"- {product['name']}: ${product['price']} (RFID: {product['rfid_tag']})")
    
    print("\nYou can now test with these RFID tags:")
    print("1. Scan your RFID tag (53EEC752110001) - it will add Apple to cart")
    print("2. Add more RFID tags to the script for other products")

if __name__ == "__main__":
    create_test_products() 