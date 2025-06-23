from datetime import datetime

class CartInitializer:
    _instance = None
    _initialized = False

    def __new__(cls, db=None):
        if cls._instance is None:
            cls._instance = super(CartInitializer, cls).__new__(cls)
        return cls._instance

    def __init__(self, db=None):
        if not self._initialized and db is not None:
            self.db = db
            self._initialized = True
            self.initialize_carts()

    def initialize_carts(self):
        """Initialize the 10 physical carts if they don't exist"""
        existing_carts = self.db.carts.count_documents({})
        
        if existing_carts == 0:
            carts = []
            for i in range(1, 11):
                cart = {
                    "cart_number": i,
                    "barcode": f"CART{i:03d}",  # CART001, CART002, etc.
                    "is_available": True,
                    "created_at": datetime.utcnow()
                }
                carts.append(cart)
            self.db.carts.insert_many(carts)
            print(f"Initialized {len(carts)} physical carts")
        else:
            print(f"Found {existing_carts} existing carts")

def init_cart_initializer(db):
    """Initialize the cart system"""
    return CartInitializer(db) 