from jose import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from functools import wraps

jwt_bp = Blueprint('jwt', __name__)

def create_access_token(data: dict, secret: str, expires_in: int = 3600):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_in)
    payload.update({"exp": expire})
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

def verify_token(token: str, secret: str):
    try:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        return decoded
    except jwt.JWTError:
        return None

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]
        decoded = verify_token(token, current_app.config["SECRET_KEY"])
        if not decoded:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Inject user info if needed
        request.user = decoded
        return f(*args, **kwargs)
    return decorated