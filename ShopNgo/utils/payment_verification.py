# import os
# from twilio.rest import Client
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# import re
# import random
#
# load_dotenv()
#
# class PaymentVerification:
#     def __init__(self, mongo_db):
#         self.mongo = mongo_db
#         # Initialize Twilio client
#         self.twilio_client = Client(
#             os.getenv('TWILIO_ACCOUNT_SID'),
#             os.getenv('TWILIO_AUTH_TOKEN')
#         )
#         self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
#
#     def format_phone_number(self, phone_number):
#         """Format phone number to international format"""
#         try:
#             # Remove any non-digit characters
#             digits = re.sub(r'\D', '', phone_number)
#
#             # Handle Egypt numbers specifically
#             if digits.startswith('0'):  # If starts with 0
#                 digits = '20' + digits[1:]  # Replace 0 with 20
#             elif digits.startswith('1'):  # If starts with 1
#                 digits = '20' + digits  # Add 20 prefix
#             elif not digits.startswith('20'):  # If doesn't start with 20
#                 digits = '20' + digits  # Add 20 prefix
#
#             # Ensure the number is in international format
#             if not digits.startswith('+'):
#                 digits = '+' + digits
#
#             print(f"Formatted phone number: {digits}")  # Debug log
#             return digits
#
#         except Exception as e:
#             print(f"Error formatting phone number: {str(e)}")
#             raise ValueError(f"Invalid phone number format: {phone_number}")
#
#     def send_otp(self, phone_number):
#         """Send OTP via SMS using Twilio"""
#         try:
#             # Format phone number
#             formatted_number = self.format_phone_number(phone_number)
#             print(f"Attempting to send SMS to: {formatted_number}")
#
#             # Generate a 6-digit OTP
#             otp = str(random.randint(100000, 999999))
#
#             # Prepare the message
#             message = f"Your ShopNGo verification code is: {otp}. This code will expire in 5 minutes."
#
#             # Send SMS using Twilio
#             message = self.twilio_client.messages.create(
#                 body=message,
#                 from_=self.twilio_phone,
#                 to=formatted_number
#             )
#
#             if message.sid:
#                 # Store OTP in database with expiration
#                 verification_record = {
#                     "phone_number": formatted_number,
#                     "otp": otp,
#                     "created_at": datetime.utcnow(),
#                     "expires_at": datetime.utcnow() + timedelta(minutes=5),
#                     "verified": False,
#                     "message_status": "sent",
#                     "message_id": message.sid
#                 }
#
#                 self.mongo.db.otp_verifications.insert_one(verification_record)
#                 print(f"OTP sent successfully to {formatted_number}: {otp}")  # For development
#                 return True, "Verification code sent successfully"
#             else:
#                 return False, "Failed to send SMS"
#
#         except Exception as e:
#             error_message = str(e)
#             print(f"Error sending SMS: {error_message}")
#             return False, f"Failed to send verification code: {error_message}"
#
#     def verify_otp(self, phone_number, otp):
#         """Verify the OTP for a given phone number"""
#         try:
#             # Format phone number
#             formatted_number = self.format_phone_number(phone_number)
#
#             # Find the most recent unverified OTP for this phone number
#             verification = self.mongo.db.otp_verifications.find_one({
#                 "phone_number": formatted_number,
#                 "otp": otp,
#                 "verified": False,
#                 "expires_at": {"$gt": datetime.utcnow()}
#             })
#
#             if not verification:
#                 return False, "Invalid or expired verification code"
#
#             # Mark OTP as verified
#             self.mongo.db.otp_verifications.update_one(
#                 {"_id": verification["_id"]},
#                 {"$set": {
#                     "verified": True,
#                     "verified_at": datetime.utcnow(),
#                     "message_status": "verified"
#                 }}
#             )
#
#             return True, "Verification successful"
#
#         except Exception as e:
#             error_message = str(e)
#             print(f"Error verifying code: {error_message}")
#             return False, f"Verification failed: {error_message}"
#
#     def validate_payment_method(self, payment_method, phone_number=None, card_number=None):
#         """Validate payment method details"""
#         if payment_method == "mobile_wallet":
#             if not phone_number:
#                 return False, "Phone number is required for mobile wallet payment"
#
#             # Basic phone number validation
#             try:
#                 formatted_number = self.format_phone_number(phone_number)
#                 # Basic validation - should be at least 10 digits after country code
#                 if len(re.sub(r'\D', '', formatted_number)) < 10:
#                     return False, "Invalid phone number format"
#                 return True, None
#             except Exception as e:
#                 return False, "Invalid phone number format"
#
#         elif payment_method == "visa":
#             if not card_number:
#                 return False, "Card number is required for Visa payment"
#             if not phone_number:
#                 return False, "Phone number is required for OTP verification"
#
#             # Validate card number
#             if not (card_number.startswith("4") and 13 <= len(card_number) <= 19 and card_number.isdigit()):
#                 return False, "Invalid Visa card number"
#
#             # Basic phone number validation
#             try:
#                 formatted_number = self.format_phone_number(phone_number)
#                 if len(re.sub(r'\D', '', formatted_number)) < 10:
#                     return False, "Invalid phone number format"
#                 return True, None
#             except Exception as e:
#                 return False, "Invalid phone number format"
#
#         return False, "Invalid payment method"