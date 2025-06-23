from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from utils.jwt_utils import jwt_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/add_product", methods=["POST"])
@jwt_required
def add_product():
    # Check if user has admin role
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    mongo = current_app.mongo

    # Validate required fields for product
    required_fields = ["name", "price", "category", "rfid_tag", "stock_quantity"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields", "required": required_fields}), 400

    # Create product object
    product = {
        "name": data["name"],
        "price": data["price"],
        "category": data["category"],
        "rfid_tag": data["rfid_tag"],
        "stock_quantity": data["stock_quantity"],
        "description": data.get("description", ""),
        "location": data.get("location", ""),
        "image_url": data.get("image_url", ""),
        "barcode": data.get("barcode", ""),
        "created_at": data.get("timestamp"),
        "store_id": data.get("store_id")
    }

    # Check if product with same RFID already exists
    existing_product = mongo.db.products.find_one({"rfid_tag": data["rfid_tag"]})
    if existing_product:
        return jsonify({"error": "Product with this RFID tag already exists"}), 409

    # Insert the product
    result = mongo.db.products.insert_one(product)

    return jsonify({
        "message": "Product added successfully",
        "product_id": str(result.inserted_id)
    }), 201


@admin_bp.route("/update_product", methods=["PUT"])
@jwt_required
def update_product():
    # Check if user has admin role
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    # Get product_id from URL parameters
    product_id = request.args.get("product_id")
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400

    data = request.get_json()
    mongo = current_app.mongo

    # Update the product
    try:
        result = mongo.db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": data}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/delete_product", methods=["DELETE"])
@jwt_required
def delete_product():
    # Check if user has admin role
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    # Get product_id from URL parameters
    product_id = request.args.get("product_id")
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400

    mongo = current_app.mongo

    # Delete the product
    try:
        result = mongo.db.products.delete_one({"_id": ObjectId(product_id)})

        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/inventory", methods=["GET"])
@jwt_required
def get_inventory():
    # Check if user has admin role
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    mongo = current_app.mongo

    # Optional filters
    store_id = request.args.get("store_id")
    category = request.args.get("category")

    # Build query
    query = {}
    if store_id:
        query["store_id"] = store_id
    if category:
        query["category"] = category

    # Get products
    products = list(mongo.db.products.find(query))

    # Convert ObjectId to string for JSON serialization
    for product in products:
        product["_id"] = str(product["_id"])

    return jsonify({"products": products}), 200