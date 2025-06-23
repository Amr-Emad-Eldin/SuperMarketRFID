from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from utils.jwt_utils import create_access_token,jwt_required

from bson import ObjectId

location_bp = Blueprint("location", __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

@location_bp.route("/submit", methods=["POST"])
@jwt_required
def submit_location():
    """Submit user's current location"""
    try:
        mongo = current_app.mongo

        data = request.get_json()
        user_email = request.user.get("email")  # Get user_id from JWT token
        user = mongo.db.users.find_one({"email": user_email})
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id = str(user["_id"])
        # Validate required fields
        required_fields = ['latitude', 'longitude']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields',
                'required_fields': required_fields
            }), 400

        # Create location document
        location_data = {
            "user_id": user_id,  # Use the user_id from JWT token
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "accuracy": data.get("accuracy"),
            "speed": data.get("speed"),
            "heading": data.get("heading"),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat())
        }

        mongo = current_app.mongo
        locations = mongo.db.user_locations

        locations.insert_one(location_data)
        return jsonify({"message": "Location submitted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@location_bp.route("/nearby-branches", methods=["GET"])
@jwt_required
def get_nearby_branches():
    """Get branches within a certain radius of user's location"""
    try:
        lat = float(request.args.get('latitude'))
        lon = float(request.args.get('longitude'))
        radius = float(request.args.get('radius', 5))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates or radius"}), 400

    mongo = current_app.mongo
    branches = mongo.db.branches
    
    # Get all branches (in a real app, you'd use geospatial queries)
    all_branches = list(branches.find())
    
    # Filter branches by distance
    nearby_branches = []
    for branch in all_branches:
        distance = calculate_distance(
            lat, lon,
            branch['latitude'],
            branch['longitude']
        )
        if distance <= radius:
            branch['distance'] = round(distance, 2)
            branch['_id'] = str(branch['_id'])
            nearby_branches.append(branch)
    
    # Sort by distance
    nearby_branches.sort(key=lambda x: x['distance'])
    
    return jsonify({
        "branches": nearby_branches,
        "count": len(nearby_branches)
    }), 200

@location_bp.route("/current-branch", methods=["GET"])
@jwt_required
def get_current_branch():
    """Get the branch the user is currently in"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    mongo = current_app.mongo
    locations = mongo.db.user_locations
    branches = mongo.db.branches

    # Get user's latest location
    latest_location = locations.find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )

    if not latest_location:
        return jsonify({"error": "No location data found"}), 404

    # Find the closest branch
    all_branches = list(branches.find())
    closest_branch = None
    min_distance = float('inf')

    for branch in all_branches:
        distance = calculate_distance(
            latest_location['latitude'],
            latest_location['longitude'],
            branch['latitude'],
            branch['longitude']
        )
        if distance < min_distance:
            min_distance = distance
            closest_branch = branch

    if closest_branch and min_distance <= 0.1:  # Within 100 meters
        closest_branch['_id'] = str(closest_branch['_id'])
        closest_branch['distance'] = round(min_distance, 2)
        return jsonify({
            "branch": closest_branch,
            "is_in_store": True
        }), 200
    else:
        return jsonify({
            "is_in_store": False,
            "closest_branch": {
                "name": closest_branch['name'],
                "distance": round(min_distance, 2)
            } if closest_branch else None
        }), 200

@location_bp.route("/history", methods=["GET"])
@jwt_required
def get_location_history():
    """Get user's location history"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    try:
        limit = int(request.args.get('limit', 50))
        days = int(request.args.get('days', 7))
    except ValueError:
        return jsonify({"error": "Invalid limit or days parameter"}), 400

    mongo = current_app.mongo
    locations = mongo.db.user_locations

    # Calculate the date threshold
    from datetime import timedelta
    date_threshold = datetime.utcnow() - timedelta(days=days)

    # Get location history
    history = list(locations.find(
        {
            "user_id": user_id,
            "timestamp": {"$gte": date_threshold}
        },
        sort=[("timestamp", -1)],
        limit=limit
    ))

    # Convert ObjectId to string and format timestamp
    for location in history:
        location['_id'] = str(location['_id'])
        location['timestamp'] = location['timestamp'].isoformat()

    return jsonify({
        "history": history,
        "count": len(history)
    }), 200
