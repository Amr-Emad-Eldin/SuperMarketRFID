from flask import Blueprint, request, jsonify, current_app, render_template
from utils.jwt_utils import jwt_required
# from utils.payment_verification import PaymentVerification
from bson import ObjectId
from datetime import datetime, timedelta
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


cart_bp = Blueprint("cart", __name__)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "nzezo7251@gmail.com"
SENDER_PASSWORD = "egzi jrel vctk ccpv"



def end_user_session(user_email):
    """End a user's active session and free up the cart"""
    mongo = current_app.mongo
    session = mongo.db.sessions.find_one({
        "user_email": user_email,
        "is_active": True
    })
    
    if session:
        # Free up the cart
        mongo.db.carts.update_one(
            {"_id": session["cart_id"]},
            {"$set": {"is_available": True}}
        )
        # End the session
        mongo.db.sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"is_active": False, "ended_at": datetime.utcnow()}}
        )

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via email using Gmail SMTP"""
    try:
        print(f"Attempting to send OTP to email: {email}")  # Debug log
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Your Shop N Go Checkout OTP"

        # Email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #333;">Your Checkout OTP</h2>
                <p>Your OTP for completing your purchase is:</p>
                <h1 style="color: #4CAF50; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                <p>This OTP will expire in 5 minutes.</p>
                <p>If you didn't request this OTP, please ignore this email.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">This is an automated message, please do not reply.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")  # Debug log
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print("Starting TLS connection...")  # Debug log
            server.starttls()
            print("Logging in to SMTP server...")  # Debug log
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Sending email...")  # Debug log
            server.send_message(msg)
            print("Email sent successfully!")  # Debug log
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")  # Debug log
        return False

@cart_bp.route("/start_session", methods=["POST"])
@jwt_required
def start_session():
    """Start a new shopping session with a physical cart"""
    try:
        mongo = current_app.mongo
        user_email = request.user.get("email")
        data = request.get_json()
        
        if not data or "cart_barcode" not in data:
            return jsonify({"error": "Cart barcode is required"}), 400

        # End any existing active session for this user
        end_user_session(user_email)
        
        # Find the cart by barcode
        cart = mongo.db.carts.find_one({
            "barcode": data["cart_barcode"],
            "is_available": True
        })
        
        if not cart:
            return jsonify({
                "error": "Cart not found or is currently in use",
                "message": "Please scan a different cart barcode"
            }), 400

        # Create new session
        session = {
            "user_email": user_email,
            "cart_id": cart["_id"],
            "items": [],
            "total_amount": 0,
            "is_active": True,
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mark cart as unavailable
        mongo.db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {"is_available": False}}
        )
        
        # Insert session
        result = mongo.db.sessions.insert_one(session)
        
        return jsonify({
            "message": "Shopping session started",
            "session_id": str(result.inserted_id),
            "cart_number": cart["cart_number"]
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/end_session", methods=["POST"])
@jwt_required
def end_session():
    """End the current shopping session"""
    try:
        mongo = current_app.mongo
        user_email = request.user.get("email")
        
        # End the session
        end_user_session(user_email)
        
        return jsonify({
            "message": "Shopping session ended successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/scan", methods=["POST"])
@jwt_required
def scan_product():
    """Add a product to cart using RFID scan"""
    try:
        data = request.get_json()
        mongo = current_app.mongo
        user_email = request.user.get("email")
        
        if not data.get("rfid_tag"):
            return jsonify({"error": "RFID tag is required"}), 400
        
        # Get active session
        session = mongo.db.sessions.find_one({
            "user_email": user_email,
            "is_active": True
        })
        if not session:
            return jsonify({"error": "No active shopping session. Please start a session first"}), 400
        
        # Find product by RFID tag
        product = mongo.db.products.find_one({"rfid_tag": data["rfid_tag"]})
        if not product:
            return jsonify({"error": "Product not found"}), 404

        # Check if product is in stock
        if product.get("stock_quantity", 0) <= 0:
            return jsonify({"error": f"Product {product['name']} is out of stock"}), 400

        # Check if product is already in session
        existing_item = next(
            (item for item in session["items"] if item["product_id"] == str(product["_id"])),
            None
        )

        if existing_item:
            # Check if adding one more would exceed stock
            if existing_item["quantity"] + 1 > product["stock_quantity"]:
                return jsonify({"error": f"Cannot add more {product['name']}. Only {product['stock_quantity']} available"}), 400
            # Update quantity
            existing_item["quantity"] += 1
            existing_item["total_price"] = existing_item["price"] * existing_item["quantity"]
        else:
            # Add new item
            session["items"].append({
                "product_id": str(product["_id"]),
                "name": product["name"],
                "price": product["price"],
                "quantity": 1,
                "total_price": product["price"],
                "rfid_tag": product["rfid_tag"],
                "scanned_at": datetime.utcnow()
            })
        
        # Update session total
        session["total_amount"] = sum(item["total_price"] for item in session["items"])
        
        # Update session in database
        mongo.db.sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {
                "items": session["items"],
                "total_amount": session["total_amount"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({
            "message": "Product scanned successfully",
            "session": {
                "items": session["items"],
                "total_amount": session["total_amount"]
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/get", methods=["GET"])
@jwt_required
def get_session():
    """Get current shopping session for authenticated user"""
    try:
        mongo = current_app.mongo
        user_email = request.user.get("email")
        
        # Get active session
        session = mongo.db.sessions.find_one({
            "user_email": user_email,
            "is_active": True
        })
        
        if not session:
            return jsonify({
                "message": "No active shopping session",
                "session": {"items": [], "total_amount": 0}
            }), 200
        
        # Get cart details
        cart = mongo.db.carts.find_one({"_id": session["cart_id"]})
        
        return jsonify({
            "session": {
                "session_id": str(session["_id"]),
                "cart_number": cart["cart_number"],
                "items": session["items"],
                "total_amount": session["total_amount"]
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/remove", methods=["POST"])
@jwt_required
def remove_from_cart():
    """Remove a product from session"""
    try:
        data = request.get_json()
        mongo = current_app.mongo
        user_email = request.user.get("email")
        
        if not data or "product_id" not in data:
            return jsonify({"error": "Product ID is required"}), 400
        
        # Get active session
        session = mongo.db.sessions.find_one({
            "user_email": user_email,
            "is_active": True
        })
        if not session:
            return jsonify({"error": "No active shopping session"}), 400

        # Find the item index
        item_index = None
        for i, item in enumerate(session["items"]):
            if item["product_id"] == data["product_id"]:
                item_index = i
                break

        if item_index is None:
            return jsonify({"error": "Product not found in session"}), 404

        # Remove only one quantity of the item
        if session["items"][item_index]["quantity"] > 1:
            session["items"][item_index]["quantity"] -= 1
            session["items"][item_index]["total_price"] = session["items"][item_index]["price"] * session["items"][item_index]["quantity"]
        else:
            # Remove the entire item if quantity is 1
            session["items"].pop(item_index)

        # Update session total
        session["total_amount"] = sum(item["total_price"] for item in session["items"])
        
        # Update session in database
        mongo.db.sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {
                "items": session["items"],
                "total_amount": session["total_amount"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({
            "message": "Product removed from session",
            "session": {
                "items": session["items"],
                "total_amount": session["total_amount"]
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/initiate-checkout", methods=["POST"])
@jwt_required
def initiate_checkout():
    """Initiate checkout process and send OTP"""
    try:
        mongo = current_app.mongo
        user_email = request.user.get("email")
        print(f"User email from JWT: {user_email}")
        
        data = request.get_json()
        
        # Validate payment method
        payment_method = data.get('payment_method')
        if not payment_method or payment_method not in ['mobile_wallet', 'visa']:
            return jsonify({
                "error": "Invalid payment method",
                "message": "Payment method must be either 'mobile_wallet' or 'visa'"
            }), 400

        # For visa, require card number
        if payment_method == 'visa' and not data.get('card_number'):
            return jsonify({
                "error": "Card number required for visa payment"
            }), 400
        
        # Get user's cart
        cart = mongo.db.carts.find_one({"user_email": user_email})
        if not cart or not cart.get("items"):
            return jsonify({"error": "Cart is empty"}), 400

        # Check if all items are available in sufficient quantity
        for item in cart["items"]:
            product = mongo.db.products.find_one({"_id": ObjectId(item["product_id"])})
            if not product:
                return jsonify({"error": f"Product {item['name']} not found"}), 404
            if product.get("stock_quantity", 0) < item["quantity"]:
                return jsonify({
                    "error": f"Insufficient quantity for {item['name']}. Available: {product.get('stock_quantity', 0)}"
                }), 400

        # Generate OTP
        otp = generate_otp()
        print(f"Generated OTP: {otp}")
        otp_expiry = datetime.utcnow() + timedelta(minutes=5)

        # Store OTP and payment info in database with current cart state
        mongo.db.checkout_otps.update_one(
            {"user_email": user_email},
            {
                "$set": {
                    "otp": otp,
                    "expiry": otp_expiry,
                    "created_at": datetime.utcnow(),
                    "payment_method": payment_method,
                    "card_number": data.get('card_number') if payment_method == 'visa' else None,
                    "verified": False,
                    "cart_items": cart["items"].copy(),  # Store a copy of the current cart items
                    "total_amount": cart["total_amount"]
                }
            },
            upsert=True
        )

        # Send OTP via email
        print("Attempting to send OTP email...")
        if not send_otp_email(user_email, otp):
            print("Failed to send OTP email")
            return jsonify({"error": "Failed to send OTP"}), 500

        print("OTP email sent successfully")
        return jsonify({
            "message": "OTP sent successfully",
            "expiry": otp_expiry.isoformat(),
            "payment_method": payment_method
        }), 200

    except Exception as e:
        print(f"Error in initiate-checkout: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/verify-checkout", methods=["POST"])
@jwt_required
def verify_checkout():
    """Verify OTP and complete checkout"""
    try:
        mongo = current_app.mongo
        user_email = request.user.get("email")
        data = request.get_json()
        
        if not data or "otp" not in data:
            return jsonify({"error": "OTP is required"}), 400

        # Get stored OTP and payment info
        stored_checkout = mongo.db.checkout_otps.find_one({
            "user_email": user_email,
            "expiry": {"$gt": datetime.utcnow()},
            "verified": False
        })

        if not stored_checkout:
            return jsonify({"error": "OTP expired, not found, or already used"}), 400

        if stored_checkout["otp"] != data["otp"]:
            return jsonify({"error": "Invalid OTP"}), 400

        # Get active session
        session = mongo.db.sessions.find_one({
            "user_email": user_email,
            "is_active": True
        })
        if not session or not session.get("items"):
            return jsonify({"error": "Session is empty"}), 400

        # Verify quantities are still available
        for item in session["items"]:
            product = mongo.db.products.find_one({"_id": ObjectId(item["product_id"])})
            if not product:
                return jsonify({"error": f"Product {item['name']} not found"}), 404
            if product.get("stock_quantity", 0) < item["quantity"]:
                return jsonify({
                    "error": f"Insufficient quantity for {item['name']}. Available: {product.get('stock_quantity', 0)}"
                }), 400

        try:
            # Update product quantities
            for item in session["items"]:
                result = mongo.db.products.update_one(
                    {"_id": ObjectId(item["product_id"])},
                    {"$inc": {"stock_quantity": -item["quantity"]}}
                )
                if result.modified_count == 0:
                    raise Exception(f"Failed to update quantity for product {item['name']}")

            # Create order with payment info
            order = {
                "user_email": user_email,
                "items": session["items"],
                "total_amount": session["total_amount"],
                "payment_method": stored_checkout["payment_method"],
                "card_number": stored_checkout.get("card_number"),
                "status": "completed",
                "created_at": datetime.utcnow(),
                "order_number": f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
            }
            
            # Insert order
            mongo.db.orders.insert_one(order)
            
            # End the session and free up the cart
            end_user_session(user_email)
            
            # Mark OTP as verified
            mongo.db.checkout_otps.update_one(
                {"_id": stored_checkout["_id"]},
                {"$set": {"verified": True, "verified_at": datetime.utcnow()}}
            )

            return jsonify({
                "message": "Checkout completed successfully",
                "order": {
                    "order_number": order["order_number"],
                    "items": order["items"],
                    "total_amount": order["total_amount"],
                    "payment_method": order["payment_method"],
                    "created_at": order["created_at"].isoformat()
                }
            }), 200

        except Exception as e:
            # If anything fails, try to revert product quantities
            for item in session["items"]:
                mongo.db.products.update_one(
                    {"_id": ObjectId(item["product_id"])},
                    {"$inc": {"stock_quantity": item["quantity"]}}
                )
            raise e

    except Exception as e:
        print(f"Error in verify-checkout: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/orders", methods=["GET"])
@jwt_required
def get_orders():
    """Get user's order history"""
    try:
        mongo = current_app.mongo
        user_email = request.user.get("email")
        
        # Get orders for user
        orders = list(mongo.db.orders.find(
            {"user_email": user_email},
            sort=[("created_at", -1)]
        ))
        
        # Convert ObjectId to string and format dates
        for order in orders:
            order["_id"] = str(order["_id"])
            order["created_at"] = order["created_at"].isoformat()
            # Remove sensitive data
            if "card_number" in order:
                order["card_number"] = "****" + order["card_number"][-4:]
        
        return jsonify({
            "orders": orders,
            "count": len(orders)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cart_bp.route("/toggle", methods=["POST"])
@jwt_required
def toggle_product():
    """Toggle a product in the cart using RFID scan: add if not present, remove if present."""
    try:
        data = request.get_json()
        mongo = current_app.mongo
        user_email = request.user.get("email")
        if not data.get("rfid_tag"):
            return jsonify({"error": "RFID tag is required"}), 400

        # Get active session
        session = mongo.db.sessions.find_one({
            "user_email": user_email,
            "is_active": True
        })
        if not session:
            return jsonify({"error": "No active shopping session. Please start a session first"}), 400

        # Find product by RFID tag
        product = mongo.db.products.find_one({"rfid_tag": data["rfid_tag"]})
        if not product:
            return jsonify({"error": "Product not found"}), 404

        # Check if product is already in session
        existing_item_index = next((i for i, item in enumerate(session["items"]) if item["rfid_tag"] == data["rfid_tag"]), None)

        if existing_item_index is not None:
            # Remove the item
            session["items"].pop(existing_item_index)
            session["total_amount"] = sum(item["total_price"] for item in session["items"])
            mongo.db.sessions.update_one(
                {"_id": session["_id"]},
                {"$set": {
                    "items": session["items"],
                    "total_amount": session["total_amount"],
                    "updated_at": datetime.utcnow()
                }}
            )
            return jsonify({
                "message": f"Product removed from cart: {product['name']} ({product.get('flavor', '')})",
                "session": {
                    "items": session["items"],
                    "total_amount": session["total_amount"]
                }
            }), 200
        else:
            # Add the item
            if product.get("stock_quantity", 0) <= 0:
                return jsonify({"error": f"Product {product['name']} is out of stock"}), 400
            session["items"].append({
                "product_id": str(product["_id"]),
                "name": product["name"],
                "price": product["price"],
                "quantity": 1,
                "total_price": product["price"],
                "rfid_tag": product["rfid_tag"],
                "flavor": product.get("flavor"),
                "scanned_at": datetime.utcnow()
            })
            session["total_amount"] = sum(item["total_price"] for item in session["items"])
            mongo.db.sessions.update_one(
                {"_id": session["_id"]},
                {"$set": {
                    "items": session["items"],
                    "total_amount": session["total_amount"],
                    "updated_at": datetime.utcnow()
                }}
            )
            return jsonify({
                "message": f"Product added to cart: {product['name']} ({product.get('flavor', '')})",
                "session": {
                    "items": session["items"],
                    "total_amount": session["total_amount"]
                }
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @cart_bp.route("/verify_phone_page")
# @jwt_required
# def verify_phone_page():
#     """Serve the phone verification page"""
#     return render_template('verify_phone.html')

# @cart_bp.route("/verify_phone", methods=["POST"])
# def verify_phone():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "No data provided"}), 400
#
#         # Get Firebase ID token from Authorization header
#         auth_header = request.headers.get('Authorization')
#         if not auth_header or not auth_header.startswith('Bearer '):
#             return jsonify({"error": "No Firebase token provided"}), 401
#
#         id_token = auth_header.split('Bearer ')[1]
#
#         # Verify Firebase token
#         try:
#             decoded_token = auth.verify_id_token(id_token)
#             firebase_uid = decoded_token['uid']
#             phone_number = decoded_token.get('phone_number')
#
#             if not phone_number:
#                 return jsonify({"error": "Phone number not verified in Firebase"}), 400
#
#         except Exception as e:
#             return jsonify({"error": f"Invalid Firebase token: {str(e)}"}), 401
#
#         # Get user from database
#         mongo = current_app.mongo
#         user = mongo.db.users.find_one({"firebase_uid": firebase_uid})
#         if not user:
#             return jsonify({"error": "User not found"}), 404
#
#         # Update user's phone number
#         mongo.db.users.update_one(
#             {"_id": user["_id"]},
#             {"$set": {
#                 "phone_number": phone_number,
#                 "phone_verified": True,
#                 "updated_at": datetime.utcnow()
#             }}
#         )
#
#         # If there's an active shopping session, create checkout attempt
#         active_session = mongo.db.shopping_sessions.find_one({
#             "user_id": user["_id"],
#             "status": "active"
#         })
#
#         if active_session:
#             checkout_attempt = {
#                 "session_id": active_session["_id"],
#                 "user_id": user["_id"],
#                 "payment_method": data.get("payment_method", "mobile_wallet"),
#                 "phone_number": phone_number,
#                 "status": "pending",
#                 "created_at": datetime.utcnow(),
#                 "expires_at": datetime.utcnow() + timedelta(minutes=5)
#             }
#
#             result = mongo.db.checkout_attempts.insert_one(checkout_attempt)
#
#             return jsonify({
#                 "message": "Phone verified successfully",
#                 "checkout_id": str(result.inserted_id)
#             }), 200
#
#         return jsonify({"message": "Phone verified successfully"}), 200
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

