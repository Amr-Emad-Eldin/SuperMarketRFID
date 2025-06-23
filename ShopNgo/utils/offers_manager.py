from datetime import datetime
from bson import ObjectId

def init_offers_manager(db):
    """Initialize offers manager with database connection"""
    class OffersManager:
        def __init__(self, db):
            self.db = db
            self.offers_collection = db.offers

        def get_active_offers(self):
            """Get all active offers"""
            current_time = datetime.utcnow()
            return list(self.offers_collection.find({
                'start_date': {'$lte': current_time},
                'end_date': {'$gte': current_time},
                'is_active': True
            }))

        def get_offer(self, offer_id):
            """Get specific offer"""
            return self.offers_collection.find_one({'_id': ObjectId(offer_id)})

        def add_offer(self, offer_data):
            """Add new offer"""
            offer_data['created_at'] = datetime.utcnow()
            result = self.offers_collection.insert_one(offer_data)
            return str(result.inserted_id)

        def update_offer(self, offer_id, offer_data):
            """Update offer"""
            result = self.offers_collection.update_one(
                {'_id': ObjectId(offer_id)},
                {'$set': offer_data}
            )
            return result.modified_count > 0

        def delete_offer(self, offer_id):
            """Delete offer"""
            result = self.offers_collection.delete_one({'_id': ObjectId(offer_id)})
            return result.deleted_count > 0

        def get_offers_for_product(self, product_id):
            """Get all active offers for a specific product"""
            current_time = datetime.utcnow()
            return list(self.offers_collection.find({
                'product_id': ObjectId(product_id),
                'start_date': {'$lte': current_time},
                'end_date': {'$gte': current_time},
                'is_active': True
            }))

        def get_offers_for_category(self, category):
            """Get all active offers for a specific category"""
            current_time = datetime.utcnow()
            return list(self.offers_collection.find({
                'category': category,
                'start_date': {'$lte': current_time},
                'end_date': {'$gte': current_time},
                'is_active': True
            }))

    return OffersManager(db) 