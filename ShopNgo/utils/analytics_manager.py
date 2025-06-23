from datetime import datetime, timedelta
from bson import ObjectId

def init_analytics_manager(db):
    """Initialize analytics manager with database connection"""
    class AnalyticsManager:
        def __init__(self, db):
            self.db = db
            self.analytics_collection = db.analytics
            self.sessions_collection = db.shopping_sessions
            self.products_collection = db.products

        def track_page_view(self, user_id, page_name):
            """Track page view"""
            self.analytics_collection.insert_one({
                'user_id': ObjectId(user_id),
                'event_type': 'page_view',
                'page_name': page_name,
                'timestamp': datetime.utcnow()
            })

        def track_product_view(self, user_id, product_id):
            """Track product view"""
            self.analytics_collection.insert_one({
                'user_id': ObjectId(user_id),
                'event_type': 'product_view',
                'product_id': ObjectId(product_id),
                'timestamp': datetime.utcnow()
            })

        def get_daily_sales(self, days=7):
            """Get daily sales for the last n days"""
            start_date = datetime.utcnow() - timedelta(days=days)
            pipeline = [
                {
                    '$match': {
                        'status': 'completed',
                        'end_time': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$end_time'
                            }
                        },
                        'total_sales': {'$sum': '$total'},
                        'order_count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            return list(self.sessions_collection.aggregate(pipeline))

        def get_top_products(self, limit=10):
            """Get top selling products"""
            pipeline = [
                {
                    '$match': {'status': 'completed'}
                },
                {'$unwind': '$items'},
                {
                    '$group': {
                        '_id': '$items.product_id',
                        'total_quantity': {'$sum': '$items.quantity'},
                        'total_revenue': {'$sum': {'$multiply': ['$items.price', '$items.quantity']}}
                    }
                },
                {'$sort': {'total_quantity': -1}},
                {'$limit': limit}
            ]
            results = list(self.sessions_collection.aggregate(pipeline))
            
            # Get product details
            for result in results:
                product = self.products_collection.find_one({'_id': result['_id']})
                if product:
                    result['product_name'] = product.get('name', 'Unknown')
                    result['product_id'] = str(result['_id'])
                    del result['_id']
            
            return results

        def get_user_activity(self, user_id, days=30):
            """Get user activity for the last n days"""
            start_date = datetime.utcnow() - timedelta(days=days)
            return list(self.analytics_collection.find({
                'user_id': ObjectId(user_id),
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', -1))

        def get_store_performance(self, store_id, days=30):
            """Get store performance metrics"""
            start_date = datetime.utcnow() - timedelta(days=days)
            pipeline = [
                {
                    '$match': {
                        'store_id': ObjectId(store_id),
                        'status': 'completed',
                        'end_time': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_sales': {'$sum': '$total'},
                        'order_count': {'$sum': 1},
                        'average_order_value': {'$avg': '$total'}
                    }
                }
            ]
            result = list(self.sessions_collection.aggregate(pipeline))
            return result[0] if result else None

    return AnalyticsManager(db)

def init_analytics(db):
    """Initialize analytics collections and indexes"""
    # Create indexes for better query performance
    db.analytics.create_index([('user_id', 1), ('timestamp', -1)])
    db.analytics.create_index([('event_type', 1), ('timestamp', -1)])
    db.shopping_sessions.create_index([('status', 1), ('end_time', -1)])
    db.shopping_sessions.create_index([('user_id', 1), ('status', 1)]) 