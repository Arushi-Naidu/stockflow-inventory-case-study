# Part 1: Code Review & Debugging

## Identified Issues

### 1. Lack of Transactional Atomicity
- **Problem**: The code calls `db.session.commit()` twice.
- **Impact**: If the second commit fails (e.g., database connection drops or integrity error on `Inventory`), a `Product` is created in the database without any associated `Inventory`. This leads to "ghost products" and incorrect stock counts.
- **Fix**: Use a single commit at the end of the function or wrap both operations in a context manager to ensure either both succeed or none do.

### 2. Architectural Flaw: Product-Warehouse Mapping
- **Problem**: The `Product` model instantiation includes `warehouse_id`.
- **Impact**: The business requirements state "Products can exist in multiple warehouses". Hardcoding a warehouse ID into the central Product record makes it impossible to manage that product in multiple locations without duplicate product entries, which breaks SKU management.
- **Fix**: Remove `warehouse_id` from the `Product` creation. Let the `Inventory` table handle the relationship between products and warehouses.

### 3. SKU Uniqueness and Integrity
- **Problem**: No check for existing SKUs before insertion.
- **Impact**: SKUs must be unique platform-wide. If `db.session.commit()` is called and the SKU already exists, an unhandled `IntegrityError` will occur, causing a 500 Internal Server Error for the user.
- **Fix**: Add a check for existing SKUs and return a user-friendly 400 error if it exists.

### 4. Decimal Precision for Pricing
- **Problem**: Assuming `data['price']` is a float.
- **Impact**: Floating-point arithmetic is unreliable for financial data (e.g., $10.00 - $9.99 can become $0.00999999997).
- **Fix**: Cast pricing to `Decimal` (Python's `decimal` module) and ensure the DB column is `NUMERIC` or `DECIMAL`.

### 5. Missing Error Handling & Field Validation
- **Problem**: Accessing `data['name']` directly without checking if the key exists or if value is valid.
- **Impact**: If a client sends a malformed JSON body, the app will crash with a `KeyError`.
- **Fix**: Use `.get()` or a validation schema (like Marshmallow or Pydantic) to handle missing and invalid data.

---

## Corrected Implementation

```python
from flask import request, jsonify
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError
from models import db, Product, Inventory

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    
    # 1. Validate Required Fields
    required_fields = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # 2. Check for Unique SKU
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({"error": f"Product with SKU {data['sku']} already exists"}), 409

        # 3. Handle Price as Decimal
        try:
            price = Decimal(str(data['price']))
            if price < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            return jsonify({"error": "Invalid price value"}), 400

        # 4. Create Product (Remove warehouse_id from here)
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price
        )
        db.session.add(product)
        
        # Flush to get the product.id without committing the transaction yet
        db.session.flush()

        # 5. Create Inventory Entry
        inventory = Inventory(
            product_id=product.id,
            warehouse_id=data['warehouse_id'],
            quantity=max(0, int(data['initial_quantity']))
        )
        db.session.add(inventory)

        # 6. Single Atomic Commit
        db.session.commit()
        
        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
```
