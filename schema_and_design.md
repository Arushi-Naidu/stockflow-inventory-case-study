# Part 2: Database Design

## Database Schema (SQL DDL)

```sql
-- Core Business Units
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product Catalog
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    base_price DECIMAL(15, 2),
    is_bundle BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier Management
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_suppliers (
    product_id INTEGER REFERENCES products(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    PRIMARY KEY (product_id, supplier_id)
);

-- Inventory Tracking (Multi-Warehouse)
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    low_stock_threshold INTEGER DEFAULT 10,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, warehouse_id)
);

-- Inventory Audit Logs
CREATE TABLE inventory_logs (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id),
    change_amount INTEGER NOT NULL, -- (+10 for restock, -5 for sale)
    transaction_type VARCHAR(50), -- 'SALE', 'RESTOCK', 'ADJUSTMENT', 'TRANSFER'
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bundle Definition (Self-referencing Products)
CREATE TABLE bundles (
    parent_product_id INTEGER REFERENCES products(id),
    component_product_id INTEGER REFERENCES products(id),
    quantity_required INTEGER DEFAULT 1,
    PRIMARY KEY (parent_product_id, component_product_id)
);

-- Indexes for performance
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
```

## Gap Analysis & Questions for Product Team

1. **Unit of Measure (UOM)**: Are products sold as "each", "kg", "liters", or "boxes"? We need a UOM table to prevent mixing units in inventory.
2. **Reorder Management**: Should the `low_stock_threshold` be dynamic based on sales velocity, or a static number set by the user?
3. **Multi-Currency**: Since this is a B2B SaaS, will companies operate in different currencies? We may need a `currency_code` column in the `companies` and `products` tables.
4. **Warehouse Transfers**: How should we handle "in-transit" stock when moving items between warehouses? 
5. **Batch/Serial Tracking**: Do we need to track specific batches or serial numbers for perishable or high-value goods?
6. **Bundle Pricing**: Is a bundle's price derived strictly from its components, or can it have its own independent price?

## Design Rationale

- **Normalization**: Used a many-to-many relationship for `product_suppliers` because a product might be sourced from multiple suppliers to ensure supply chain resilience.
- **Data Integrity**: Added a `CHECK (quantity >= 0)` constraint on the inventory table to prevent "phantom stock" issues at the database level.
- **Auditability**: The `inventory_logs` table is crucial for B2B applications where reconciliations are common. It tracks every single change to stock levels.
- **Performance**: Indexed `sku` and `product_id`/`warehouse_id` combinations to ensure that inventory lookups (the most common operation) remain fast even with millions of records.
