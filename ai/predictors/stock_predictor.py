"""
CaisseDZ AI Pro - Stock Predictor
Offline-first predictive analytics for inventory management.
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

class StockPredictor:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def get_sales_history(self, product_id, days=14):
        """Fetch sales history for a product over the last N days."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date(s.date) as sale_date, SUM(si.quantity) as total_qty
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ? AND s.date >= date('now', '-{} days')
                GROUP BY sale_date
                ORDER BY sale_date ASC
            """.format(days), (product_id,))
            return cursor.fetchall()
    
    def predict_stock_depletion(self, product_id, current_stock):
        """
        Predict how many days until stock runs out.
        Returns: (days_remaining, daily_forecast, confidence)
        """
        history = self.get_sales_history(product_id, days=14)
        
        if len(history) < 3:
            # Not enough data
            return (999, 0, "low")
        
        # Prepare training data
        today = datetime.now().date()
        X = []
        y = []
        
        for sale_date_str, qty in history:
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date()
            days_ago = (today - sale_date).days
            X.append([days_ago])
            y.append(qty)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        model = LinearRegression().fit(X, y)
        
        # Predict tomorrow's sales (day 0)
        tomorrow_forecast = model.predict([[0]])[0]
        
        if tomorrow_forecast <= 0:
            return (999, 0, "low")
        
        days_remaining = current_stock / tomorrow_forecast
        
        # Confidence based on data points
        confidence = "high" if len(history) >= 7 else "medium"
        
        return (days_remaining, tomorrow_forecast, confidence)
    
    def get_critical_products(self, threshold_days=3):
        """
        Get all products predicted to run out within threshold_days.
        Returns list of (product_id, name, days_remaining, forecast)
        """
        critical = []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, stock FROM products WHERE active = 1")
            products = cursor.fetchall()
        
        for product in products:
            days_left, forecast, confidence = self.predict_stock_depletion(
                product['id'], 
                product['stock']
            )
            
            if days_left < threshold_days and confidence != "low":
                critical.append({
                    'id': product['id'],
                    'name': product['name'],
                    'days_remaining': days_left,
                    'daily_forecast': forecast,
                    'confidence': confidence
                })
        
        return critical
