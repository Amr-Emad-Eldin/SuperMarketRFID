from datetime import datetime
from bson import ObjectId

def init_cart_manager(db):
    """Initialize cart manager with database connection"""
    class CartManager:
        def __init__(self, db):
            self.db = db
            self.cart_collection = db.carts
            self.sessions_collection = db.shopping_sessions

        def start_session(self, user_id):
            """Start a new shopping session"""
            session = {
                'user_id': ObjectId(user_id),
                'start_time': datetime.utcnow(),
                'status': 'active',
                'items': [],
                'total': 0.0
            }
            result = self.sessions_collection.insert_one(session)
            return str(result.inserted_id)

        def get_active_session(self, user_id):
            """Get user's active shopping session"""
            return self.sessions_collection.find_one({
                'user_id': ObjectId(user_id),
                'status': 'active'
            })

        def add_item(self, session_id, product_id, quantity=1):
            """Add item to shopping session"""
            session = self.sessions_collection.find_one({'_id': ObjectId(session_id)})
            if not session:
                return None

            # Get product details
            product = self.db.products.find_one({'_id': ObjectId(product_id)})
            if not product:
                return None

            # Update session
            self.sessions_collection.update_one(
                {'_id': ObjectId(session_id)},
                {
                    '$push': {'items': {
                        'product_id': ObjectId(product_id),
                        'quantity': quantity,
                        'price': product['price'],
                        'added_at': datetime.utcnow()
                    }},
                    '$inc': {'total': product['price'] * quantity}
                }
            )
            return self.get_active_session(str(session['user_id']))

        def remove_item(self, session_id, product_id):
            """Remove item from shopping session"""
            session = self.sessions_collection.find_one({'_id': ObjectId(session_id)})
            if not session:
                return None

            # Find the item to remove
            item = next((i for i in session['items'] if str(i['product_id']) == product_id), None)
            if not item:
                return None

            # Update session
            self.sessions_collection.update_one(
                {'_id': ObjectId(session_id)},
                {
                    '$pull': {'items': {'product_id': ObjectId(product_id)}},
                    '$inc': {'total': -item['price'] * item['quantity']}
                }
            )
            return self.get_active_session(str(session['user_id']))

        def end_session(self, session_id):
            """End shopping session"""
            session = self.sessions_collection.find_one({'_id': ObjectId(session_id)})
            if not session:
                return None

            self.sessions_collection.update_one(
                {'_id': ObjectId(session_id)},
                {
                    '$set': {
                        'status': 'completed',
                        'end_time': datetime.utcnow()
                    }
                }
            )
            return True

    return CartManager(db) 