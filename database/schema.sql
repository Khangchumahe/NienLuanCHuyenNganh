-- ========================================================
-- CƠ SỞ DỮ LIỆU CỬA HÀNG QUẦN ÁO THỜI TRANG (SQLITE / SQL)
-- Môn: Niên luận Chuyên ngành Kỹ thuật Phần mềm
-- Áp dụng: CRUD, Index, Trigger, Transaction (Stored Procedure)
-- ========================================================

-- 1. BẢNG DANH MỤC
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER DEFAULT 1
);

-- 2. BẢNG SẢN PHẨM CHÍNH
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    price REAL NOT NULL,
    discount_price REAL,
    material TEXT,          -- Chất liệu (Cotton, Linen, Lụa, Oxford...)
    style TEXT,             -- Phong cách (Công sở, Dạo phố, Thể thao, Tiệc...)
    size_guide TEXT,        -- Hướng dẫn size chi tiết (dùng cho RAG)
    description TEXT,       -- Mô tả tính năng, cách bảo quản
    image_url TEXT,
    is_published INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- 3. BẢNG BIẾN THỂ SẢN PHẨM (SKU THEO SIZE & MÀU)
CREATE TABLE IF NOT EXISTS product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL,
    size TEXT NOT NULL,       -- S, M, L, XL, XXL
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 4. BẢNG ĐƠN HÀNG
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_address TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_PAYMENT', -- PENDING_PAYMENT, PAID, CANCELLED, SHIPPING, DELIVERED
    payment_method TEXT NOT NULL,                   -- VIRTUAL_SANDBOX, COD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. BẢNG CHI TIẾT ĐƠN HÀNG
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    variant_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);

-- 6. BẢNG GIAO DỊCH THANH TOÁN ẢO
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    transaction_code TEXT NOT NULL UNIQUE,
    amount REAL NOT NULL,
    payment_gateway TEXT DEFAULT 'VNPAY_SANDBOX_SIMULATOR',
    status TEXT NOT NULL, -- PENDING, SUCCESS, FAILED, CANCELLED
    checksum_signature TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- 7. BẢNG LỊCH SỬ THAY ĐỔI TRẠNG THÁI ĐƠN HÀNG (AUDIT TRAIL)
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    note TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- 8. BẢNG NHẬT KÝ KHO HÀNG (INVENTORY LOGS)
CREATE TABLE IF NOT EXISTS inventory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,
    change_quantity INTEGER NOT NULL,
    remaining_stock INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);

-- ========================================================
-- PHẦN CHỈ MỤC (INDEXES) ĐỂ TỐI ƯU TRUY VẤN
-- ========================================================
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id, is_published);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(discount_price, price);
CREATE INDEX IF NOT EXISTS idx_variants_product ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_code ON orders(order_code);
CREATE INDEX IF NOT EXISTS idx_payments_transaction ON payments(transaction_code);

-- ========================================================
-- PHẦN TRIGGERS (RÀNG BUỘC TOÀN VẸN & TỰ ĐỘNG HÓA DỮ LIỆU)
-- ========================================================

-- Trigger 1: Ngăn chặn số lượng tồn kho âm (Data Constraint)
CREATE TRIGGER IF NOT EXISTS trg_prevent_negative_stock
BEFORE UPDATE OF stock_quantity ON product_variants
BEGIN
    SELECT CASE
        WHEN NEW.stock_quantity < 0 THEN
            RAISE(ABORT, 'Lỗi ràng buộc Trigger: Số lượng tồn kho không được phép nhỏ hơn 0!')
    END;
END;

-- Trigger 2: Tự động ghi nhật ký lịch sử khi trạng thái đơn hàng thay đổi
CREATE TRIGGER IF NOT EXISTS trg_track_order_status
AFTER UPDATE OF status ON orders
WHEN OLD.status <> NEW.status
BEGIN
    INSERT INTO order_status_history (order_id, old_status, new_status, note)
    VALUES (NEW.id, OLD.status, NEW.status, 'Tự động ghi nhận bởi Trigger cơ sở dữ liệu');
END;

-- Trigger 3: Tự động ghi nhật ký biến động kho khi cập nhật tồn kho
CREATE TRIGGER IF NOT EXISTS trg_log_inventory_change
AFTER UPDATE OF stock_quantity ON product_variants
WHEN OLD.stock_quantity <> NEW.stock_quantity
BEGIN
    INSERT INTO inventory_logs (variant_id, change_quantity, remaining_stock, reason)
    VALUES (NEW.id, (NEW.stock_quantity - OLD.stock_quantity), NEW.stock_quantity, 'Cập nhật kho từ hệ thống');
END;
