from flask import Blueprint, request, jsonify, current_app
from utils.jwt_utils import create_access_token,jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    mongo = current_app.mongo
    users = mongo.db.users

    if users.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 409

    hashed_pw = generate_password_hash(data["password"])
    users.insert_one({
        "firstName": data["firstName"],
        "lastName": data["lastName"],
        "email": data["email"],
        "password": hashed_pw,
        "gender": data["gender"],
        "role": "customer"
    })
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route("/protected", methods=["GET"])
@jwt_required
def protected():
    user_info = request.user
    return jsonify({"message": f"Hello, {user_info['email']}!"})

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    mongo = current_app.mongo
    users = mongo.db.users
    user = users.find_one({"email": data["email"]})

    if user and check_password_hash(user["password"], data["password"]):
        token_data = {"email": user["email"], "role": user["role"]}
        token = create_access_token(token_data, current_app.config["SECRET_KEY"])
        return jsonify({"message": "Login successful",
                        "user": {
                            "token": token,
                            "email": user["email"],
                            "firstName": user["firstName"]}})
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_user_info():
    mongo = current_app.mongo
    user = mongo.db.users.find_one({"email": request.user["email"]})
    if user:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        user.pop("password", None)  # Remove password from response
        return jsonify({"user": user}), 200
    return jsonify({"error": "User not found"}), 404
