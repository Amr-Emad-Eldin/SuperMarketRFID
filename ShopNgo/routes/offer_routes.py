from flask import Blueprint, request, jsonify, current_app

offer_bp = Blueprint("offer", __name__)


@offer_bp.route("/personal", methods=["GET"])
def get_personal_offers():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    mongo = current_app.mongo

    # Get user's purchase history
    user_orders = list(mongo.db.orders.find({"user_id": user_id}))

    # Simple recommendation logic (in a real app, this would be more sophisticated)
    purchased_products = set()
    for order in user_orders:
        for item in order["items"]:
            purchased_products.add(item["product_id"])

    # Get offers based on user's purchase history
    # This is a simple example - in a real app, you'd have a more sophisticated algorithm
    personalized_offers = list(mongo.db.offers.find({
        "$or": [
            {"product_id": {"$in": list(purchased_products)}},
            {"category_id": {"$in": list(mongo.db.products.find(
                {"product_id": {"$in": list(purchased_products)}},
                {"category_id": 1}
            ).distinct("category_id"))}}
        ]
    }))

    # If no personalized offers, return some default offers
    if not personalized_offers:
        personalized_offers = list(mongo.db.offers.find().limit(5))

    return jsonify({"offers": personalized_offers}), 200