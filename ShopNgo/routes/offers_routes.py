from flask import Blueprint, jsonify, request
from functools import wraps
from utils.auth_manager import init_auth_manager
from utils.offers_manager import init_offers_manager
from bson import ObjectId

offers_bp = Blueprint('offers', __name__)

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

@offers_bp.route('/get', methods=['GET'])
@token_required
def get_offers(user):
    """Get all active offers"""
    offers_manager = init_offers_manager(request.app.mongo.db)
    offers = offers_manager.get_active_offers()
    
    # Convert ObjectId to string for JSON serialization
    for offer in offers:
        offer['_id'] = str(offer['_id'])
        if 'product_id' in offer:
            offer['product_id'] = str(offer['product_id'])
    
    return jsonify(offers)

@offers_bp.route('/get/<offer_id>', methods=['GET'])
@token_required
def get_offer(user, offer_id):
    """Get specific offer"""
    offers_manager = init_offers_manager(request.app.mongo.db)
    offer = offers_manager.get_offer(offer_id)
    
    if not offer:
        return jsonify({'message': 'Offer not found'}), 404
    
    offer['_id'] = str(offer['_id'])
    if 'product_id' in offer:
        offer['product_id'] = str(offer['product_id'])
    
    return jsonify(offer)

@offers_bp.route('/product/<product_id>', methods=['GET'])
@token_required
def get_product_offers(user, product_id):
    """Get all active offers for a specific product"""
    offers_manager = init_offers_manager(request.app.mongo.db)
    offers = offers_manager.get_offers_for_product(product_id)
    
    for offer in offers:
        offer['_id'] = str(offer['_id'])
        offer['product_id'] = str(offer['product_id'])
    
    return jsonify(offers)

@offers_bp.route('/category/<category>', methods=['GET'])
@token_required
def get_category_offers(user, category):
    """Get all active offers for a specific category"""
    offers_manager = init_offers_manager(request.app.mongo.db)
    offers = offers_manager.get_offers_for_category(category)
    
    for offer in offers:
        offer['_id'] = str(offer['_id'])
        if 'product_id' in offer:
            offer['product_id'] = str(offer['product_id'])
    
    return jsonify(offers)

# Admin routes for managing offers
@offers_bp.route('/create', methods=['POST'])
@token_required
def create_offer(user):
    """Create a new offer (admin only)"""
    if user.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    required_fields = ['name', 'description', 'discount', 'start_date', 'end_date']
    
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    offers_manager = init_offers_manager(request.app.mongo.db)
    offer_id = offers_manager.add_offer(data)
    
    return jsonify({'message': 'Offer created', 'offer_id': offer_id}), 201

@offers_bp.route('/update/<offer_id>', methods=['PUT'])
@token_required
def update_offer(user, offer_id):
    """Update an offer (admin only)"""
    if user.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    offers_manager = init_offers_manager(request.app.mongo.db)
    
    if offers_manager.update_offer(offer_id, data):
        return jsonify({'message': 'Offer updated'})
    return jsonify({'message': 'Offer not found'}), 404

@offers_bp.route('/delete/<offer_id>', methods=['DELETE'])
@token_required
def delete_offer(user, offer_id):
    """Delete an offer (admin only)"""
    if user.get('role') != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    offers_manager = init_offers_manager(request.app.mongo.db)
    
    if offers_manager.delete_offer(offer_id):
        return jsonify({'message': 'Offer deleted'})
    return jsonify({'message': 'Offer not found'}), 404 