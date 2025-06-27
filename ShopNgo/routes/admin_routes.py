from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from utils.jwt_utils import jwt_required
from datetime import datetime, timedelta
from collections import Counter

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


# --- ADMIN ANALYTICS ENDPOINTS ---

@admin_bp.route("/active_carts", methods=["GET"])
@jwt_required
def get_active_carts():
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    mongo = current_app.mongo
    # Find all active sessions (carts in use)
    active_sessions = list(mongo.db.sessions.find({"is_active": True}))
    for session in active_sessions:
        session["_id"] = str(session["_id"])
        session["cart_id"] = str(session["cart_id"])
        session["started_at"] = session["started_at"].isoformat() if "started_at" in session else None
        session["updated_at"] = session["updated_at"].isoformat() if "updated_at" in session else None
    return jsonify({"active_carts": active_sessions, "count": len(active_sessions)})

@admin_bp.route("/orders", methods=["GET"])
@jwt_required
def get_all_orders():
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    mongo = current_app.mongo
    orders = list(mongo.db.orders.find({}, sort=[("created_at", -1)]))
    for order in orders:
        order["_id"] = str(order["_id"])
        order["created_at"] = order["created_at"].isoformat() if "created_at" in order else None
        if "card_number" in order:
            order["card_number"] = "****" + order["card_number"][-4:]
    return jsonify({"orders": orders, "count": len(orders)})

@admin_bp.route("/analytics/peak_hours", methods=["GET"])
@jwt_required
def get_peak_hours():
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    mongo = current_app.mongo
    days = int(request.args.get("days", 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    orders = list(mongo.db.orders.find({"created_at": {"$gte": start_date, "$lte": end_date}}))
    hours = [order["created_at"].hour for order in orders if "created_at" in order]
    hour_counts = Counter(hours)
    peak_hours = hour_counts.most_common(5)
    return jsonify({"peak_hours": peak_hours, "total_orders": len(orders)})

@admin_bp.route("/analytics/trending_products", methods=["GET"])
@jwt_required
def get_trending_products():
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    mongo = current_app.mongo
    days = int(request.args.get("days", 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    orders = list(mongo.db.orders.find({"created_at": {"$gte": start_date, "$lte": end_date}}))
    product_counter = Counter()
    for order in orders:
        for item in order.get("items", []):
            product_counter[item["product_id"]] += item.get("quantity", 1)
    top_products = product_counter.most_common(10)
    # Get product details
    products = []
    for product_id, count in top_products:
        product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
        if product:
            products.append({
                "product_id": str(product_id),
                "name": product.get("name", "Unknown"),
                "total_quantity": count
            })
    return jsonify({"trending_products": products})

@admin_bp.route("/analytics/product_associations", methods=["GET"])
@jwt_required
def get_product_associations():
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    mongo = current_app.mongo
    days = int(request.args.get("days", 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    orders = list(mongo.db.orders.find({"created_at": {"$gte": start_date, "$lte": end_date}}))
    # Build baskets
    baskets = [set(item["product_id"] for item in order.get("items", [])) for order in orders]
    pair_counter = Counter()
    for basket in baskets:
        for a in basket:
            for b in basket:
                if a < b:
                    pair_counter[(a, b)] += 1
    top_pairs = pair_counter.most_common(10)
    associations = []
    for (a, b), count in top_pairs:
        prod_a = mongo.db.products.find_one({"_id": ObjectId(a)})
        prod_b = mongo.db.products.find_one({"_id": ObjectId(b)})
        if prod_a and prod_b:
            associations.append({
                "product_a": {"id": str(a), "name": prod_a.get("name", "Unknown")},
                "product_b": {"id": str(b), "name": prod_b.get("name", "Unknown")},
                "count": count
            })
    return jsonify({"product_associations": associations})

@admin_bp.route("/analytics/sales", methods=["GET"])
@jwt_required
def get_sales_analytics():
    if request.user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    mongo = current_app.mongo
    days = int(request.args.get("days", 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    orders = list(mongo.db.orders.find({"created_at": {"$gte": start_date, "$lte": end_date}}))
    total_sales = sum(order.get("total_amount", 0) for order in orders)
    total_products = sum(item.get("quantity", 1) for order in orders for item in order.get("items", []))
    return jsonify({
        "total_sales": total_sales,
        "total_products_sold": total_products,
        "order_count": len(orders)
    })
