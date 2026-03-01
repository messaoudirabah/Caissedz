"""
CaisseDZ AI Pro - Main AI Service
Central hub for all AI features with Qt threading support.
"""

from PySide6.QtCore import QThread, Signal
import sys
import os

# Add ai folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai'))

try:
    from predictors.stock_predictor import StockPredictor
except ImportError:
    StockPredictor = None

class AIService:
    """Main AI coordinator for CaisseDZ Pro."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.stock_predictor = StockPredictor(db_manager) if StockPredictor else None
    
    def get_stock_alerts(self, threshold_days=3):
        """Get products at risk of running out."""
        if not self.stock_predictor:
            return []
        return self.stock_predictor.get_critical_products(threshold_days)
    
    def predict_product_depletion(self, product_id, current_stock):
        """Get prediction for a specific product."""
        if not self.stock_predictor:
            return (999, 0, "unavailable")
        return self.stock_predictor.predict_stock_depletion(product_id, current_stock)


class StockPredictionThread(QThread):
    """Background thread for AI predictions to avoid UI blocking."""
    predictions_ready = Signal(list)
    
    def __init__(self, ai_service, threshold_days=3):
        super().__init__()
        self.ai_service = ai_service
        self.threshold_days = threshold_days
    
    def run(self):
        """Execute prediction in background."""
        try:
            alerts = self.ai_service.get_stock_alerts(self.threshold_days)
            self.predictions_ready.emit(alerts)
        except Exception as e:
            print(f"AI Prediction Error: {e}")
            self.predictions_ready.emit([])
