from flask import Flask
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv

load_dotenv()

def init_db():
    """Initialize MongoDB connection"""
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopngo")
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "your-secret-key-here")
    
    mongo = PyMongo(app)
    return mongo.db 