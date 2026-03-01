# ai_quickstart_demo.py
"""
CaisseDZ AI Pro - Quickstart Demo
Feature: Predictive Stock Forecasting (Offline-First)

This script demonstrates how scikit-learn can be used locally to 
predict when a product will run out of stock based on sales trends.
"""

try:
    import numpy as np
    from sklearn.linear_model import LinearRegression
except ImportError:
    print("AI Quickstart Error: Dependencies missing.")
    print("Please run: pip install scikit-learn numpy")
    exit()

def simulate_stock_prediction():
    print("="*40)
    print(" 🤖 CAISSEDZ AI PRO - STOCK FORENSICS")
    print("="*40)

    # 1. Training Data: Days (relative to today) vs Quantities Sold
    # [Today-7, Today-6, Today-5, Today-4, Today-3, Today-2, Today-1]
    days_ago = np.array([7, 6, 5, 4, 3, 2, 1]).reshape(-1, 1)
    
    # Example: Sales are increasing (5, 7, 8, 10, 12, 13, 15)
    sales_history = np.array([5, 7, 8, 10, 12, 13, 15])

    # 2. Train Local Model (Linear Regression)
    model = LinearRegression().fit(days_ago, sales_history)

    # 3. Predict Tomorrow's Sales (X=0)
    tomorrow_forecast = model.predict([[0]])[0]
    
    current_stock = 38  # Example current inventory
    
    # 4. Intelligence Logic
    if tomorrow_forecast <= 0:
        days_remaining = 99
    else:
        days_remaining = current_stock / tomorrow_forecast

    print(f"🔹 Produit: Café Espresso (Stock Actuel: {current_stock})")
    print(f"🔹 Tendance: Ventes en hausse...")
    print(f"📈 Prédiction demain: ~{tomorrow_forecast:.1f} unités à vendre.")
    print(f"⏳ Autonomie estimée: {days_remaining:.1f} jours.")

    if days_remaining < 3:
        print("\n🚨 [AI WARNING]: STOCK CRITIQUE DANS 3 JOURS.")
        print("💡 CONSEIL: Passer commande avant Jeudi pour éviter la rupture.")
    else:
        print("\n✅ Stock sécurisé pour la semaine.")

    print("="*40)

if __name__ == "__main__":
    simulate_stock_prediction()
