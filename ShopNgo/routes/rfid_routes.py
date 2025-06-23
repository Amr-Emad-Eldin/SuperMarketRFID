from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from bson import ObjectId

rfid_bp = Blueprint('rfid', __name__)

@rfid_bp.route('/scan', methods=['POST'])
def receive_rfid():
    """Receive RFID UID and process cart operations"""
    try:
        data = request.get_json()
        uid = data.get('uid')
        if not uid:
            return jsonify({'error': 'No UID provided'}), 400

        print(f"Received RFID UID: {uid}")
        
        # Get MongoDB instance
        mongo = current_app.mongo
        
        # Look for cart with this RFID UID
        cart = mongo.db.carts.find_one({"barcode": uid})
        
        if not cart:
            # If no cart found, create a new cart entry (for testing)
            cart_data = {
                "cart_number": mongo.db.carts.count_documents({}) + 1,
                "barcode": uid,
                "is_available": True,
                "created_at": datetime.utcnow()
            }
            result = mongo.db.carts.insert_one(cart_data)
            cart = mongo.db.carts.find_one({"_id": result.inserted_id})
            print(f"Created new cart entry for UID: {uid}")
        
        # Check if cart is available
        if cart.get("is_available", True):
            return jsonify({
                'message': 'Cart available',
                'cart_id': str(cart['_id']),
                'cart_number': cart.get('cart_number'),
                'barcode': cart.get('barcode'),
                'status': 'available'
            }), 200
        else:
            # Cart is in use, check if there's an active session
            active_session = mongo.db.sessions.find_one({
                "cart_id": cart['_id'],
                "is_active": True
            })
            
            if active_session:
                return jsonify({
                    'message': 'Cart in use',
                    'cart_id': str(cart['_id']),
                    'cart_number': cart.get('cart_number'),
                    'barcode': cart.get('barcode'),
                    'status': 'in_use',
                    'session_id': str(active_session['_id'])
                }), 200
            else:
                # Mark cart as available if no active session
                mongo.db.carts.update_one(
                    {"_id": cart['_id']},
                    {"$set": {"is_available": True}}
                )
                return jsonify({
                    'message': 'Cart now available',
                    'cart_id': str(cart['_id']),
                    'cart_number': cart.get('cart_number'),
                    'barcode': cart.get('barcode'),
                    'status': 'available'
                }), 200
                
    except Exception as e:
        print(f"Error processing RFID scan: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@rfid_bp.route('/scan_product', methods=['POST'])
def scan_product_rfid():
    """Scan product via RFID without authentication - for ESP32"""
    try:
        data = request.get_json()
        rfid_tag = data.get('rfid_tag')
        if not rfid_tag:
            return jsonify({'error': 'RFID tag is required'}), 400

        print(f"RFID Product Scan: {rfid_tag}")
        
        mongo = current_app.mongo
        
        # Find product by RFID tag
        product = mongo.db.products.find_one({"rfid_tag": rfid_tag})
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': f'No product found with RFID tag: {rfid_tag}'
            }), 404

        # Check if product is in stock
        if product.get("stock_quantity", 0) <= 0:
            return jsonify({
                'error': 'Product out of stock',
                'message': f'Product {product["name"]} is out of stock'
            }), 400

        # For now, just return the product info
        # In a real system, you might want to:
        # 1. Add to a temporary cart
        # 2. Associate with a specific cart/session
        # 3. Use a different authentication method
        
        return jsonify({
            'message': 'Product scanned successfully',
            'product': {
                'id': str(product['_id']),
                'name': product['name'],
                'price': product['price'],
                'category': product.get('category'),
                'rfid_tag': product['rfid_tag'],
                'stock_quantity': product.get('stock_quantity', 0)
            }
        }), 200

    except Exception as e:
        print(f"Error scanning product: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@rfid_bp.route('/carts', methods=['GET'])
def get_all_carts():
    """Get all carts with their RFID barcodes"""
    try:
        mongo = current_app.mongo
        carts = list(mongo.db.carts.find({}, {
            'cart_number': 1,
            'barcode': 1,
            'is_available': 1,
            'created_at': 1
        }))
        
        # Convert ObjectId to string for JSON serialization
        for cart in carts:
            cart['_id'] = str(cart['_id'])
            if 'created_at' in cart:
                cart['created_at'] = cart['created_at'].isoformat()
        
        return jsonify({'carts': carts}), 200
        
    except Exception as e:
        print(f"Error getting carts: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500