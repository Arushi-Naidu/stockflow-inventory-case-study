from flask import Flask, jsonify
from datetime import datetime, timedelta
import math

app = Flask(__name__)

# --- Mock Database / Data Models ---
# In a real app, these would be SQLAlchemy models
DATA = {
    "warehouses": [
        {"id": 456, "name": "Main Warehouse", "company_id": 1},
        {"id": 457, "name": "Secondary Warehouse", "company_id": 1}
    ],
    "products": [
        {"id": 123, "name": "Widget A", "sku": "WID-001", "supplier_id": 789},
        {"id": 124, "name": "Gadget B", "sku": "GAD-002", "supplier_id": 789}
    ],
    "suppliers": {
        789: {"id": 789, "name": "Supplier Corp", "contact_email": "orders@supplier.com"}
    },
    "inventory": [
        # (product_id, warehouse_id, quantity, threshold)
        {"product_id": 123, "warehouse_id": 456, "quantity": 5, "threshold": 20},
        {"product_id": 124, "warehouse_id": 456, "quantity": 50, "threshold": 10}
    ],
    "sales": [
        # Recent sales (last 30 days) to calculate average daily velocity
        {"product_id": 123, "quantity": 10, "date": datetime.now() - timedelta(days=2)},
        {"product_id": 123, "quantity": 5, "date": datetime.now() - timedelta(days=5)},
        {"product_id": 124, "quantity": 100, "date": datetime.now() - timedelta(days=40)} # Not recent
    ]
}

def calculate_days_until_stockout(product_id, current_stock):
    """
    Assumes lead time calculation based on sales in the last 30 days.
    Logic: Total Sales in 30 days / 30 = Average Daily Sales.
    Stock / Avg Daily Sales = Days remaining.
    """
    lookback_days = 30
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    recent_sales = [s for s in DATA["sales"] 
                    if s["product_id"] == product_id and s["date"] > cutoff_date]
    
    total_qty_sold = sum(s["quantity"] for s in recent_sales)
    
    if total_qty_sold == 0:
        return None # No recent activity or no sales
        
    avg_daily_sales = total_qty_sold / lookback_days
    return math.ceil(current_stock / avg_daily_sales)

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):
    # 1. Filter warehouses for this company
    company_warehouses = [w for w in DATA["warehouses"] if w["company_id"] == company_id]
    warehouse_ids = [w["id"] for w in company_warehouses]
    
    alerts = []
    
    # 2. Check inventory for these warehouses
    for item in DATA["inventory"]:
        if item["warehouse_id"] in warehouse_ids:
            # Check if below threshold
            if item["quantity"] < item["threshold"]:
                
                # Check for recent sales activity
                days_left = calculate_days_until_stockout(item["product_id"], item["quantity"])
                
                # Business Rule: Only alert if there is recent sales activity
                if days_left is not None:
                    product = next(p for p in DATA["products"] if p["id"] == item["product_id"])
                    supplier = DATA["suppliers"].get(product["supplier_id"])
                    warehouse = next(w for w in DATA["warehouses"] if w["id"] == item["warehouse_id"])
                    
                    alerts.append({
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "sku": product["sku"],
                        "warehouse_id": warehouse["id"],
                        "warehouse_name": warehouse["name"],
                        "current_stock": item["quantity"],
                        "threshold": item["threshold"],
                        "days_until_stockout": days_left,
                        "supplier": supplier
                    })
                    
    return jsonify({
        "alerts": alerts,
        "total_alerts": len(alerts)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
