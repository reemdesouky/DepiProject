

-- ============================================
-- Create Database
-- ============================================




-- ============================================
-- Products Table
-- ============================================
CREATE TABLE Products (
    product_id INT IDENTITY(1,1) PRIMARY KEY,
    product_name NVARCHAR(100) NOT NULL UNIQUE
);
GO

-- ============================================
-- Stores Table
-- ============================================
CREATE TABLE Stores (
    store_id INT IDENTITY(1,1) PRIMARY KEY,
    store_name NVARCHAR(100) NOT NULL UNIQUE
);
GO

-- ============================================
-- Warehouses Table
-- ============================================
CREATE TABLE Warehouses (
    warehouse_id INT IDENTITY(1,1) PRIMARY KEY,
    warehouse_name NVARCHAR(100) NOT NULL
);
GO

-- ============================================
-- Warehouse Inventory Table
-- ============================================
CREATE TABLE Warehouse_Inventory (
    warehouse_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    last_updated DATETIME DEFAULT GETDATE(),

    CONSTRAINT PK_WarehouseInventory 
        PRIMARY KEY (warehouse_id, product_id),

    CONSTRAINT FK_WarehouseInventory_Warehouse 
        FOREIGN KEY (warehouse_id)
        REFERENCES Warehouses(warehouse_id),

    CONSTRAINT FK_WarehouseInventory_Product 
        FOREIGN KEY (product_id)
        REFERENCES Products(product_id),

    CONSTRAINT CHK_WarehouseInventory_Qty 
        CHECK (quantity >= 0)
);
GO

-- ============================================
-- Store Inventory Table
-- ============================================
CREATE TABLE Store_Inventory (
    store_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    last_updated DATETIME DEFAULT GETDATE(),

    CONSTRAINT PK_StoreInventory 
        PRIMARY KEY (store_id, product_id),

    CONSTRAINT FK_StoreInventory_Store 
        FOREIGN KEY (store_id)
        REFERENCES Stores(store_id),

    CONSTRAINT FK_StoreInventory_Product 
        FOREIGN KEY (product_id)
        REFERENCES Products(product_id),

    CONSTRAINT CHK_StoreInventory_Qty 
        CHECK (quantity >= 0)
);
GO

-- ============================================
-- Sales Table (transaction level)
-- ============================================
CREATE TABLE Sales (
    sale_id INT IDENTITY(1,1) PRIMARY KEY,

    store_id INT NOT NULL,
    product_id INT NOT NULL,

    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,

    total_price AS (quantity * unit_price) PERSISTED,

    sale_date DATETIME NOT NULL,

    CONSTRAINT FK_Sales_Store
        FOREIGN KEY (store_id)
        REFERENCES Stores(store_id),

    CONSTRAINT FK_Sales_Product
        FOREIGN KEY (product_id)
        REFERENCES Products(product_id),

    CONSTRAINT CHK_Sales_Qty CHECK (quantity > 0),
    CONSTRAINT CHK_Sales_Price CHECK (unit_price >= 0)
);

alter table Sales 
add discount_amount decimal(10,2) null,
 loyalty_points int  null,
 final_amount as (unit_price* quantity)-discount_amount PERSISTED
GO

-- ============================================
-- Daily Sales Table (for forecasting)
-- ============================================
CREATE TABLE DailySales (
    store_id INT NOT NULL,
    product_id INT NOT NULL,

    sale_date DATE NOT NULL,

    total_quantity INT NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL,

    CONSTRAINT PK_DailySales
        PRIMARY KEY (store_id, product_id, sale_date),

    CONSTRAINT FK_DailySales_Store
        FOREIGN KEY (store_id)
        REFERENCES Stores(store_id),

    CONSTRAINT FK_DailySales_Product
        FOREIGN KEY (product_id)
        REFERENCES Products(product_id)
);
GO

-- ============================================
-- Indexes for performance (important)
-- ============================================
CREATE INDEX idx_sales_date ON Sales(sale_date);

CREATE INDEX idx_sales_product ON Sales(product_id);

CREATE INDEX idx_dailysales_product ON DailySales(product_id);

GO
select * from Sales
select * from Store_Inventory
select * from  Warehouse_Inventory