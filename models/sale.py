from datetime import datetime

class Sale:
    def __init__(self, id=None, date=None, total=0.0, payment_type="cash", user_id=None, items=None):
        self.id = id
        self.date = date or datetime.now()
        self.total = total
        self.payment_type = payment_type
        self.user_id = user_id
        self.items = items or []

class SaleItem:
    def __init__(self, id=None, sale_id=None, product_id=None, quantity=0, price=0.0, product_name=""):
        self.id = id
        self.sale_id = sale_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        self.product_name = product_name # For UI/Receipt convenience
