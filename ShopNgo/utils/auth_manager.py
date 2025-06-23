from datetime import datetime, timedelta
from bson import ObjectId
import jwt
import os
from werkzeug.security import generate_password_hash, check_password_hash

def init_auth_manager(db):
    """Initialize auth manager with database connection"""
    class AuthManager:
        def __init__(self, db):
            self.db = db
            self.users_collection = db.users
            self.secret_key = os.getenv('JWT_SECRET', 'your-secret-key-here')

        def register_user(self, email, password, name):
            """Register a new user"""
            # Check if user already exists
            if self.users_collection.find_one({'email': email}):
                return None, 'Email already registered'

            # Create new user
            user = {
                'email': email,
                'password': generate_password_hash(password),
                'name': name,
                'created_at': datetime.utcnow(),
                'role': 'user'
            }
            result = self.users_collection.insert_one(user)
            user['_id'] = result.inserted_id

            # Generate token
            token = self._generate_token(user)
            return token, None

        def login_user(self, email, password):
            """Login user and return token"""
            user = self.users_collection.find_one({'email': email})
            if not user:
                return None, 'User not found'

            if not check_password_hash(user['password'], password):
                return None, 'Invalid password'

            token = self._generate_token(user)
            return token, None

        def get_user(self, user_id):
            """Get user by ID"""
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                user.pop('password', None)
            return user

        def update_user(self, user_id, update_data):
            """Update user data"""
            if 'password' in update_data:
                update_data['password'] = generate_password_hash(update_data['password'])

            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0

        def verify_token(self, token):
            """Verify JWT token and return user"""
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                user = self.get_user(payload['user_id'])
                if not user:
                    return None
                return user
            except jwt.ExpiredSignatureError:
                return None
            except jwt.InvalidTokenError:
                return None

        def _generate_token(self, user):
            """Generate JWT token for user"""
            payload = {
                'user_id': str(user['_id']),
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(days=1)
            }
            return jwt.encode(payload, self.secret_key, algorithm='HS256')

    return AuthManager(db) 