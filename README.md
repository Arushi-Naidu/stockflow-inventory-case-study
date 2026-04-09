# StockFlow Inventory Management System - Case Study Solution

This repository contains the complete solution for the StockFlow internship case study.

## Project Structure

- `part1_debugging/`: Analysis of the problematic endpoint and its corrected implementation.
- `part2_database/`: Scalable PostgreSQL-compatible schema design, ERD description, and gap analysis.
- `part3_api/`: Functional Flask implementation of the Low-Stock Alerts endpoint with business logic for stockout prediction.

## How to Run the API (Part 3)

1. Ensure you have Python 3.x installed.
2. Navigate to `part3_api/`.
3. (Optional) Create a virtual environment: `python -m venv venv && source venv/bin/activate`.
4. Run the application: `python app.py`.
5. Access the alerts endpoint: `GET http://localhost:5000/api/companies/1/alerts/low-stock`.
### Example Response

```json
{
  "alerts": [
    {
      "product_id": 123,
      "product_name": "Widget A",
      "sku": "WID-001",
      "warehouse_id": 456,
      "warehouse_name": "Main Warehouse",
      "current_stock": 5,
      "threshold": 20,
      "days_until_stockout": 12,
      "supplier": {
        "id": 789,
        "name": "Supplier Corp",
        "contact_email": "orders@supplier.com"
      }
    }
  ],
  "total_alerts": 1
}
```
## Design Assumptions & Reasoning

### Part 1: Debugging
- **Transactions**: Prioritized atomicity. A product should never exist without its initial inventory record.
- **Data Types**: Used `Decimal` for currency to prevent precision loss common with `float`.

### Part 2: Database Design
- **Company Separation**: Multi-tenancy is handled at the `company_id` level across `warehouses` and `products`.
- **Bundling**: Used a self-referencing many-to-many table to support nested product bundles.
- **Auditability**: Included an `inventory_logs` table to satisfy the "track when inventory levels change" requirement.

### Part 3: Low-Stock Alerts
- **Recent Activity**: Defined as any sales occurring within the last 30 days. Products without recent sales are excluded from alerts to prevent noise.
- **Stockout Prediction**: Calculated as `Current Stock / (Total Sales in Last 30 Days / 30)`. This provides a realistic estimate of when replenishment is needed.
- **Dynamic Thresholds**: Assumed thresholds are stored in the `inventory` table to allow for warehouse-specific stock policies.

 
