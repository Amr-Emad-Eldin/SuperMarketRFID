from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

rfid_products = [
    # Molto
    {"rfid_tag": "53FFC752110001", "name": "Molto", "price": 14.5, "flavor": "Strawberry"},
    {"rfid_tag": "53FEC752110001", "name": "Molto", "price": 14.5, "flavor": "Strawberry"},
    {"rfid_tag": "53F9C752110001", "name": "Molto", "price": 14.5, "flavor": "Chocolate"},
    # Chips
    {"rfid_tag": "53F8C752110001", "name": "Chips", "price": 10.0, "flavor": "Cheese"},
    {"rfid_tag": "53F7C752110001", "name": "Chips", "price": 10.0, "flavor": "Cheese"},
    {"rfid_tag": "53F6C752110001", "name": "Chips", "price": 10.0, "flavor": "Cheese"},
    # V Cola
    {"rfid_tag": "53F1C752110001", "name": "V Cola", "price": 8.0, "flavor": "Diet"},
    {"rfid_tag": "53F0C752110001", "name": "V Cola", "price": 8.0, "flavor": "Diet"},
    {"rfid_tag": "53EFC752110001", "name": "V Cola", "price": 8.0, "flavor": "Regular"},
    {"rfid_tag": "53EEC752110001", "name": "V Cola", "price": 8.0, "flavor": "Regular"},
]

def add_bulk_rfid_products():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    client = MongoClient(mongo_uri)
    db = client.shopngo

    for prod in rfid_products:
        existing = db.products.find_one({"rfid_tag": prod["rfid_tag"]})
        if existing:
            print(f"Product with RFID {prod['rfid_tag']} already exists: {existing['name']} ({existing.get('flavor', 'N/A')})")
            continue
        product_doc = {
            "name": prod["name"],
            "price": prod["price"],
            "flavor": prod["flavor"],
            "rfid_tag": prod["rfid_tag"],
            "stock_quantity": 1,  # Each tag is a unique item
            "description": f"{prod['name']} - {prod['flavor']}",
            "created_at": datetime.utcnow()
        }
        db.products.insert_one(product_doc)
        print(f"Added: {product_doc['name']} ({product_doc['flavor']}) - RFID: {product_doc['rfid_tag']}")

if __name__ == "__main__":
    add_bulk_rfid_products()
    print("\nAll products added!") 