from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from routes.auth_routes import auth_bp
from routes.cart_routes import cart_bp
from routes.location_routes import location_bp
from routes.offers_routes import offers_bp
from routes.analytics_routes import analytics_bp
from routes.admin_routes import admin_bp
from utils.jwt_utils import jwt_bp
from routes.rfid_routes import rfid_bp

from utils.cart_manager import init_cart_manager
from utils.location_manager import init_location_manager
from utils.offers_manager import init_offers_manager
from utils.auth_manager import init_auth_manager
from utils.analytics_manager import init_analytics_manager, init_analytics
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def end_all_active_sessions(mongo):
    """End all active sessions and free up carts"""
    try:
        # Get all active sessions
        active_sessions = mongo.db.sessions.find({"is_active": True})
        
        # Update all carts to available
        cart_ids = [session["cart_id"] for session in active_sessions]
        if cart_ids:
            mongo.db.carts.update_many(
                {"_id": {"$in": cart_ids}},
                {"$set": {"is_available": True}}
            )
        
        # End all active sessions
        mongo.db.sessions.update_many(
            {"is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "ended_at": datetime.utcnow(),
                    "ended_by": "system_shutdown"
                }
            }
        )
        print("Successfully ended all active sessions")
    except Exception as e:
        print(f"Error ending sessions: {str(e)}")

def create_app():
    app = Flask(__name__)
    # Configure MongoDB
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "bongakawabonga")
    
    # Initialize MongoDB and make it available globally
    mongo = PyMongo(app)
    app.mongo = mongo  # This makes mongo available as current_app.mongo
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],  # In production, replace with your Flutter app's domain
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize managers
    auth_manager = init_auth_manager(mongo.db)
    cart_manager = init_cart_manager(mongo.db)
    location_manager = init_location_manager(mongo.db)
    offers_manager = init_offers_manager(mongo.db)
    analytics_manager = init_analytics_manager(mongo.db)
    
    # Initialize analytics indexes
    init_analytics(mongo.db)

    # Register blueprints with API prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(location_bp, url_prefix='/api/location')
    app.register_blueprint(offers_bp, url_prefix='/api/offers')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(rfid_bp, url_prefix='/api/rfid')
    app.register_blueprint(jwt_bp, url_prefix='/api/jwt')

    return app

app = create_app()

if __name__ == '__main__':
    print("Starting main Flask app on 0.0.0.0:5000")
    print("Test with: curl http://192.168.1.37:5000/api/cart/get")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting Flask app: {str(e)}")