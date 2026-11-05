"""
Database Manager for Clothing Store
Hỗ trợ: CRUD, Trigger, Indexes, Stored Procedure (Transaction ACID)
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'store.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    seed_sample_data()

# Tự động khởi tạo ngay khi module db được import nếu database chưa tồn tại
if not os.path.exists(DB_PATH):
    init_db()


def seed_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kiểm tra nếu đã có dữ liệu thì không seed lại
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # 1. Seed Categories
    categories = [
        ("Áo Nam", "ao-nam", "Các loại áo sơ mi, áo polo, áo thun nam cao cấp"),
        ("Quần Nam", "quan-nam", "Quần âu, quần kaki, quần jean nam trẻ trung, thanh lịch"),
        ("Áo Khoác", "ao-khoac", "Áo khoác blazer, áo khoác gió thể thao nam nữ chống nước"),
        ("Đầm & Váy Nữ", "dam-vay-nu", "Đầm lụa, chân váy chữ A, thiết kế tôn dáng công sở và dạ tiệc")
    ]
    cursor.executemany("INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)", categories)
    
    # 2. Seed Products
    products = [
        (
            1, # Áo Nam
            "Áo Sơ Mi Nam Oxford Slimfit Tay Dài",
            "ao-so-mi-oxford-slimfit",
            399000,
            349000,
            "100% Cotton Oxford dệt sợi đôi, thấm hút mồ hôi, bề mặt đứng form, chống nhăn nhẹ.",
            "Công sở, Dự tiệc nhẹ, Đi phỏng vấn, Đi làm hàng ngày.",
            "Size S: 1m55-1m64 (50-57kg) | Size M: 1m65-1m72 (58-65kg) | Size L: 1m70-1m78 (66-74kg) | Size XL: 1m75-1m85 (75-85kg)",
            "Áo sơ mi Oxford kinh điển với cổ button-down lịch lãm. Form Slimfit tôn dáng, dễ dàng phối cùng quần tây hoặc quần jean.",
            "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&auto=format&fit=crop&q=80"
        ),
        (
            1, # Áo Nam
            "Áo Thun Nam Cổ Tròn Cotton Compact 260GSM",
            "ao-thun-cotton-compact-260gsm",
            250000,
            199000,
            "100% Cotton Compact chải kỹ, định lượng dày dặn 260GSM, co giãn 4 chiều, không xù lông.",
            "Streetwear, Dạo phố, Thể thao, Năng động hàng ngày.",
            "Size S: 1m50-1m62 (48-55kg) | Size M: 1m63-1m70 (56-64kg) | Size L: 1m71-1m77 (65-73kg) | Size XL: 1m78-1m85 (74-84kg)",
            "Chiếc áo thun basic không thể thiếu trong tủ đồ. Bề mặt vải mịn mượt, giữ form cổ áo sau nhiều lần giặt.",
            "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80"
        ),
        (
            2, # Quần Nam
            "Quần Tây Âu Nam Dáng Tapered Co Giãn Cao Cấp",
            "quan-tay-au-tapered-nam",
            480000,
            420000,
            "Vải Tuyết Mưa pha Spandex co giãn nhẹ, giữ ly sắc nét, không nhăn, không bám bụi.",
            "Công sở, Hội nghị, Đám cưới, Sự kiện trang trọng.",
            "Size S (29): 1m60-1m67 (52-58kg) | Size M (30): 1m68-1m74 (59-66kg) | Size L (31-32): 1m72-1m78 (67-75kg) | Size XL (33): 1m76-1m84 (76-85kg)",
            "Quần âu may đo tỉ mỉ, ống tapered gọn gàng tôn chiều cao. Đai lưng thiết kế đệm thun co giãn thông minh.",
            "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&auto=format&fit=crop&q=80"
        ),
        (
            2, # Quần Nam
            "Quần Jean Nam Dáng Slimfit Denim Indigo Nhật Bản",
            "quan-jean-nam-slimfit-indigo",
            520000,
            469000,
            "Denim 12.5oz cotton nguyên bản pha 2% elastane, wash màu Indigo sâu, co giãn thoải mái.",
            "Cá tính, Dạo phố, Đi chơi cuối tuần, Phối áo thun.",
            "Size S (29): 1m58-1m66 (50-57kg) | Size M (30): 1m67-1m73 (58-65kg) | Size L (31): 1m72-1m77 (66-74kg) | Size XL (32): 1m76-1m85 (75-84kg)",
            "Quần jeans phong cách trẻ trung hiện đại, đũng quần thoải mái, giữ màu bền bỉ qua thời gian.",
            "https://images.unsplash.com/photo-1542272604-780c96856592?w=600&auto=format&fit=crop&q=80"
        ),
        (
            3, # Áo Khoác
            "Áo Khoác Blazer Nam Hàn Quốc 2 Khuy Form Relaxed",
            "ao-khoac-blazer-nam-han-quoc",
            750000,
            680000,
            "Chất liệu dạ kẻ chìm pha sợi rayon thoáng khí, lớp lót lụa habutai cao cấp.",
            "Smart Casual, Dự tiệc, Cà phê cuối tuần, Hẹn hò.",
            "Size M: 1m65-1m73 (58-66kg) | Size L: 1m72-1m79 (67-76kg) | Size XL: 1m78-1m86 (77-86kg)",
            "Mẫu blazer thời thượng mang đậm phong cách Hàn Quốc. Cầu vai đệm mỏng tự nhiên, dễ phối cả áo thun lẫn sơ mi.",
            "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&auto=format&fit=crop&q=80"
        ),
        (
            3, # Áo Khoác
            "Áo Khoác Gió Nam Nữ 2 Lớp Chống Nước GORE-TEX Like",
            "ao-khoac-gio-2-lop-chong-nuoc",
            420000,
            360000,
            "Vải dù micro-polyester tráng màng kháng nước 10.000mm, cản gió 100%, lót lưới thoáng khí.",
            "Đi phượt, Thể thao ngoài trời, Đi mưa gió nhẹ, Chạy xe máy.",
            "Size S: 1m50-1m60 (45-53kg) | Size M: 1m60-1m68 (54-63kg) | Size L: 1m68-1m76 (64-73kg) | Size XL: 1m75-1m85 (74-85kg)",
            "Áo khoác gió đa năng tiện dụng quanh năm. Có mũ trùm tháo rời, khóa kéo phủ màng chống thấm nước an toàn.",
            "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=600&auto=format&fit=crop&q=80"
        ),
        (
            4, # Đầm & Váy Nữ
            "Đầm Suông Nữ Lụa Xước Cổ Chữ V Sang Trọng",
            "dam-suong-nu-lua-xuoc-co-v",
            590000,
            490000,
            "Chất lụa xước ánh nhung mờ cao cấp, rũ mềm mại, không nhăn, độ co giãn nhẹ.",
            "Dự tiệc cưới, Sự kiện, Dạo phố, Hẹn hò thanh lịch.",
            "Size S: 1m52-1m60 (45-51kg, eo 64-68cm) | Size M: 1m58-1m65 (52-57kg, eo 69-73cm) | Size L: 1m62-1m70 (58-65kg, eo 74-78cm)",
            "Đầm thiết kế dáng suông che khuyết điểm vòng hai cực tốt. Cổ chữ V thanh thoát tôn bờ xương quai xanh quyến rũ.",
            "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&auto=format&fit=crop&q=80"
        ),
        (
            4, # Đầm & Váy Nữ
            "Chân Váy Chữ A Lưng Cao Xếp Ly Dáng Dài",
            "chan-vay-chu-a-lung-cao-xep-ly",
            380000,
            320000,
            "Chất vải tuyết hàn dập ly nhiệt bền bỉ, dày dặn đứng form, lót quần bên trong an toàn.",
            "Công sở, Giáo viên, Đi học, Dạo phố dịu dàng.",
            "Size S: 1m50-1m58 (44-50kg, eo 62-66cm) | Size M: 1m56-1m64 (51-56kg, eo 67-71cm) | Size L: 1m62-1m68 (57-63kg, eo 72-76cm)",
            "Chân váy chữ A kinh điển giúp hack dáng kéo dài chân. Dễ dàng phối cùng áo sơ mi, áo len mỏng hay áo thun ôm.",
            "https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?w=600&auto=format&fit=crop&q=80"
        )
    ]

    cursor.executemany("""
        INSERT INTO products 
        (category_id, name, slug, price, discount_price, material, style, size_guide, description, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    # 3. Seed Product Variants (SKUs)
    variants = [
        # Áo Sơ Mi Nam Oxford (ID: 1)
        (1, "OXF-WHT-S", "Trắng", "S", 15),
        (1, "OXF-WHT-M", "Trắng", "M", 25),
        (1, "OXF-WHT-L", "Trắng", "L", 20),
        (1, "OXF-WHT-XL", "Trắng", "XL", 12),
        (1, "OXF-BLU-M", "Xanh Nhạt", "M", 18),
        (1, "OXF-BLU-L", "Xanh Nhạt", "L", 15),

        # Áo Thun Cotton Compact (ID: 2)
        (2, "TSH-BLK-M", "Đen", "M", 30),
        (2, "TSH-BLK-L", "Đen", "L", 25),
        (2, "TSH-WHT-M", "Trắng", "M", 35),
        (2, "TSH-WHT-L", "Trắng", "L", 28),
        (2, "TSH-GRY-L", "Xám Tiêu", "L", 14),

        # Quần Tây Âu Tapered (ID: 3)
        (3, "PNT-BLK-S", "Đen", "S", 10),
        (3, "PNT-BLK-M", "Đen", "M", 20),
        (3, "PNT-BLK-L", "Đen", "L", 18),
        (3, "PNT-NVY-M", "Xanh Navy", "M", 15),
        (3, "PNT-NVY-L", "Xanh Navy", "L", 12),

        # Quần Jean Nam Indigo (ID: 4)
        (4, "JEA-IND-M", "Xanh Indigo", "M", 20),
        (4, "JEA-IND-L", "Xanh Indigo", "L", 22),
        (4, "JEA-IND-XL", "Xanh Indigo", "XL", 10),

        # Áo Khoác Blazer Nam (ID: 5)
        (5, "BLZ-BEG-M", "Màu Be", "M", 8),
        (5, "BLZ-BEG-L", "Màu Be", "L", 12),
        (5, "BLZ-BLK-L", "Đen", "L", 10),

        # Áo Khoác Gió 2 Lớp (ID: 6)
        (6, "WND-BLK-M", "Đen", "M", 20),
        (6, "WND-BLK-L", "Đen", "L", 25),
        (6, "WND-NVY-L", "Xanh Đen", "L", 15),

        # Đầm Suông Nữ Lụa Xước (ID: 7)
        (7, "DRS-RED-S", "Đỏ Rượu", "S", 10),
        (7, "DRS-RED-M", "Đỏ Rượu", "M", 15),
        (7, "DRS-BEG-M", "Be Ánh Kim", "M", 12),

        # Chân Váy Chữ A (ID: 8)
        (8, "SKT-BLK-S", "Đen", "S", 14),
        (8, "SKT-BLK-M", "Đen", "M", 18),
        (8, "SKT-BRN-M", "Nâu Tây", "M", 15)
    ]

    cursor.executemany("""
        INSERT INTO product_variants (product_id, sku, color, size, stock_quantity)
        VALUES (?, ?, ?, ?, ?)
    """, variants)

    conn.commit()
    conn.close()
    print("Database initialized and sample data seeded successfully!")

# ========================================================
# CÁC HÀM MÔ PHỎNG STORED PROCEDURE & ACID TRANSACTIONS
# ========================================================

def sp_create_order_and_deduct_stock(customer_info, cart_items, payment_method="VIRTUAL_SANDBOX"):
    """
    Thủ tục mô phỏng Stored Procedure tạo đơn hàng và trừ kho an toàn (ACID Transaction).
    Nếu bất kỳ biến thể nào không đủ tồn kho, Transaction sẽ ROLLBACK ngay lập tức.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Kiểm tra tồn kho từng mặt hàng
        total_amount = 0.0
        validated_items = []
        for item in cart_items:
            variant_id = item['variant_id']
            qty = int(item['quantity'])
            
            cursor.execute("""
                SELECT pv.id, pv.stock_quantity, pv.sku, p.name, p.discount_price, p.price
                FROM product_variants pv
                JOIN products p ON pv.product_id = p.id
                WHERE pv.id = ?
            """, (variant_id,))
            variant = cursor.fetchone()
            
            if not variant:
                raise ValueError(f"Biến thể mã ID {variant_id} không tồn tại!")
            
            if variant['stock_quantity'] < qty:
                raise ValueError(f"Sản phẩm '{variant['name']} ({variant['sku']})' chỉ còn {variant['stock_quantity']} chiếc, không đủ {qty} chiếc yêu cầu!")
            
            price = variant['discount_price'] if variant['discount_price'] else variant['price']
            subtotal = price * qty
            total_amount += subtotal
            
            validated_items.append({
                'variant_id': variant_id,
                'quantity': qty,
                'unit_price': price,
                'subtotal': subtotal
            })

        # 2. Tạo đơn hàng mới
        order_code = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("""
            INSERT INTO orders (order_code, customer_name, customer_phone, customer_address, total_amount, status, payment_method)
            VALUES (?, ?, ?, ?, ?, 'PENDING_PAYMENT', ?)
        """, (
            order_code,
            customer_info.get('name', 'Khách mua hàng'),
            customer_info.get('phone', '0901234567'),
            customer_info.get('address', '123 Đường Mẫu, Q. Ninh Kiều, Cần Thơ'),
            total_amount,
            payment_method
        ))
        order_id = cursor.lastrowid

        # 3. Chèn các mặt hàng vào order_items & trừ tồn kho (Kích hoạt Trigger kiểm tra)
        for v in validated_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, variant_id, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, v['variant_id'], v['quantity'], v['unit_price'], v['subtotal']))
            
            cursor.execute("""
                UPDATE product_variants 
                SET stock_quantity = stock_quantity - ?
                WHERE id = ?
            """, (v['quantity'], v['variant_id']))

        # 4. Tạo bản ghi thanh toán ảo
        trans_code = f"TRX-{datetime.now().strftime('%y%m%d%H%M')}-{order_id}"
        cursor.execute("""
            INSERT INTO payments (order_id, transaction_code, amount, status)
            VALUES (?, ?, ?, 'PENDING')
        """, (order_id, trans_code, total_amount))

        conn.commit()
        return {
            'success': True,
            'order_id': order_id,
            'order_code': order_code,
            'transaction_code': trans_code,
            'total_amount': total_amount
        }
    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()

def sp_process_payment_webhook(transaction_code, status="SUCCESS"):
    """
    Thủ tục xử lý Webhook khi cổng thanh toán ảo trả về kết quả (SUCCESS / CANCELLED / FAILED)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        cursor.execute("SELECT order_id, status FROM payments WHERE transaction_code = ?", (transaction_code,))
        payment = cursor.fetchone()
        if not payment:
            raise ValueError(f"Không tìm thấy giao dịch {transaction_code}!")

        order_id = payment['order_id']

        # Cập nhật bảng payments
        cursor.execute("""
            UPDATE payments 
            SET status = ?
            WHERE transaction_code = ?
        """, (status, transaction_code))

        # Cập nhật trạng thái đơn hàng (sẽ kích hoạt trigger trg_track_order_status)
        new_order_status = 'PAID' if status == 'SUCCESS' else 'CANCELLED'
        cursor.execute("""
            UPDATE orders 
            SET status = ?
            WHERE id = ?
        """, (new_order_status, order_id))

        # Nếu giao dịch bị hủy, hoàn lại số lượng tồn kho
        if status == 'CANCELLED':
            cursor.execute("SELECT variant_id, quantity FROM order_items WHERE order_id = ?", (order_id,))
            items = cursor.fetchall()
            for it in items:
                cursor.execute("""
                    UPDATE product_variants 
                    SET stock_quantity = stock_quantity + ?
                    WHERE id = ?
                """, (it['quantity'], it['variant_id']))

        conn.commit()
        return {'success': True, 'order_id': order_id, 'new_status': new_order_status}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def get_all_products(category_id=None, search=None):
    """Lấy danh sách sản phẩm kèm tổng số lượng tồn kho và các biến thể"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT p.*, c.name as category_name,
               COALESCE(SUM(pv.stock_quantity), 0) as total_stock
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_variants pv ON p.id = pv.product_id
        WHERE p.is_published = 1
    """
    params = []
    
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.material LIKE ? OR p.style LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
        
    query += " GROUP BY p.id ORDER BY p.id ASC"
    
    cursor.execute(query, params)
    products = [dict(row) for row in cursor.fetchall()]
    
    # Nạp kèm danh sách biến thể của từng sản phẩm
    for prod in products:
        cursor.execute("SELECT * FROM product_variants WHERE product_id = ?", (prod['id'],))
        prod['variants'] = [dict(v) for v in cursor.fetchall()]
        
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    product = dict(row)
    cursor.execute("SELECT * FROM product_variants WHERE product_id = ?", (product_id,))
    product['variants'] = [dict(v) for v in cursor.fetchall()]
    conn.close()
    return product

def get_db_stats():
    """Hàm thống kê phục vụ giảng viên kiểm tra Database, Trigger, Order logs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_variants")
    total_variants = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM order_status_history ORDER BY changed_at DESC LIMIT 5")
    recent_status_logs = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM inventory_logs ORDER BY created_at DESC LIMIT 5")
    recent_inventory_logs = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        'total_products': total_products,
        'total_variants': total_variants,
        'total_orders': total_orders,
        'recent_status_logs': recent_status_logs,
        'recent_inventory_logs': recent_inventory_logs
    }
