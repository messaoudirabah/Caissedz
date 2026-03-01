class Product:
    def __init__(self, id=None, name="", category="", price_sale=0.0, price_cost=0.0, stock=0, active=1, image_path=""):
        self.id = id
        self.name = name
        self.category = category
        self.price_sale = price_sale
        self.price_cost = price_cost
        self.stock = stock
        self.active = active
        self.image_path = image_path

    @staticmethod
    def from_row(row):
        return Product(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            price_sale=row['price_sale'],
            price_cost=row['price_cost'],
            stock=row['stock'],
            active=row['active'],
            image_path=row['image_path']
        )
