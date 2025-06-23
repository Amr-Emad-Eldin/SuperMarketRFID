from flask import Blueprint, jsonify, request
from functools import wraps
from utils.auth_manager import init_auth_manager
from utils.analytics_manager import init_analytics_manager
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        auth_manager = init_auth_manager(request.app.mongo.db)
        user = auth_manager.verify_token(token)
        
        if not user:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        auth_manager = init_auth_manager(request.app.mongo.db)
        user = auth_manager.verify_token(token)
        
        if not user or user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        return f(user, *args, **kwargs)
    return decorated

@analytics_bp.route('/track/page', methods=['POST'])
@token_required
def track_page_view(user):
    """Track page view"""
    data = request.get_json()
    if not data or 'page_name' not in data:
        return jsonify({'message': 'Missing page_name'}), 400
    
    analytics_manager = init_analytics_manager(request.app.mongo.db)
    analytics_manager.track_page_view(str(user['_id']), data['page_name'])
    return jsonify({'message': 'Page view tracked'})

@analytics_bp.route('/track/product', methods=['POST'])
@token_required
def track_product_view(user):
    """Track product view"""
    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({'message': 'Missing product_id'}), 400
    
    analytics_manager = init_analytics_manager(request.app.mongo.db)
    analytics_manager.track_product_view(str(user['_id']), data['product_id'])
    return jsonify({'message': 'Product view tracked'})

@analytics_bp.route('/user/activity', methods=['GET'])
@token_required
def get_user_activity(user):
    """Get user's activity"""
    days = request.args.get('days', default=30, type=int)
    analytics_manager = init_analytics_manager(request.app.mongo.db)
    activity = analytics_manager.get_user_activity(str(user['_id']), days)
    
    # Convert ObjectId to string for JSON serialization
    for event in activity:
        event['_id'] = str(event['_id'])
        if 'product_id' in event:
            event['product_id'] = str(event['product_id'])
    
    return jsonify(activity)

# Admin routes
@analytics_bp.route('/sales/daily', methods=['GET'])
@admin_required
def get_daily_sales(user):
    """Get daily sales data (admin only)"""
    days = request.args.get('days', default=7, type=int)
    analytics_manager = init_analytics_manager(request.app.mongo.db)
    sales_data = analytics_manager.get_daily_sales(days)
    return jsonify(sales_data)

@analytics_bp.route('/products/top', methods=['GET'])
@admin_required
def get_top_products(user):
    """Get top selling products (admin only)"""
    limit = request.args.get('limit', default=10, type=int)
    analytics_manager = init_analytics_manager(request.app.mongo.db)
    top_products = analytics_manager.get_top_products(limit)
    return jsonify(top_products)

@analytics_bp.route('/store/<store_id>/performance', methods=['GET'])
@admin_required
def get_store_performance(user, store_id):
    """Get store performance metrics (admin only)"""
    days = request.args.get('days', default=30, type=int)
    analytics_manager = init_analytics_manager(request.app.mongo.db)
    performance = analytics_manager.get_store_performance(store_id, days)
    return jsonify(performance if performance else {'message': 'No data available'}) 