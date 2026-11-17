import sqlite3

from seed_products import seed_catalog


def test_seed_catalog_is_idempotent_and_uses_requested_paths(tmp_path):
    db_path = tmp_path / "catalog.db"
    image_dir = tmp_path / "images"

    first = seed_catalog(
        db_path,
        write_index_html=False,
        image_dir=image_dir,
    )
    second = seed_catalog(
        db_path,
        write_index_html=False,
        image_dir=image_dir,
    )

    assert first["inserted"] == 150
    assert second["inserted"] == 0
    assert not list(tmp_path.glob("backup_catalog_*"))

    conn = sqlite3.connect(db_path)
    try:
        products = conn.execute(
            "SELECT COUNT(*) FROM products WHERE slug LIKE 'aura-demo-%'"
        ).fetchone()[0]
        variants = conn.execute(
            "SELECT COUNT(*) FROM product_variants v JOIN products p "
            "ON p.id=v.product_id WHERE p.slug LIKE 'aura-demo-%'"
        ).fetchone()[0]
        assert products == 150
        assert variants == 600
    finally:
        conn.close()


def test_seed_catalog_refresh_updates_copy_without_changing_price_stock_or_orders(
    tmp_path,
):
    db_path = tmp_path / "refresh.db"
    image_dir = tmp_path / "images"
    seed_catalog(db_path, write_index_html=False, image_dir=image_dir)

    conn = sqlite3.connect(db_path)
    try:
        product_id = conn.execute(
            "SELECT id FROM products WHERE slug='aura-demo-ao-khoac-01'"
        ).fetchone()[0]
        conn.execute(
            "UPDATE products SET style='Cũ', description='Mô tả cũ', "
            "price=123456, discount_price=120000 WHERE id=?",
            (product_id,),
        )
        conn.execute(
            "UPDATE product_variants SET stock_quantity=7 "
            "WHERE product_id=?",
            (product_id,),
        )
        variant_id = conn.execute(
            "SELECT id FROM product_variants WHERE product_id=? LIMIT 1",
            (product_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO orders (order_code, customer_name, customer_phone, "
            "customer_address, total_amount, status, payment_method) "
            "VALUES ('ORD-REFRESH-TEST', 'Test', '0000000000', 'Temp', "
            "100000, 'PAID', 'TEST')"
        )
        order_id = conn.execute(
            "SELECT id FROM orders WHERE order_code='ORD-REFRESH-TEST'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO order_items (order_id, variant_id, quantity, "
            "unit_price, subtotal) VALUES (?, ?, 1, 100000, 100000)",
            (order_id, variant_id),
        )
        conn.commit()
    finally:
        conn.close()

    refreshed = seed_catalog(
        db_path,
        write_index_html=False,
        image_dir=image_dir,
        refresh=True,
    )
    assert refreshed["refreshed"] == 150

    conn = sqlite3.connect(db_path)
    try:
        product = conn.execute(
            "SELECT style, description, price, discount_price "
            "FROM products WHERE id=?",
            (product_id,),
        ).fetchone()
        stock = conn.execute(
            "SELECT stock_quantity FROM product_variants "
            "WHERE product_id=?",
            (product_id,),
        ).fetchone()[0]
        order = conn.execute(
            "SELECT status, total_amount FROM orders "
            "WHERE order_code='ORD-REFRESH-TEST'"
        ).fetchone()
        assert product[0] != "Cũ"
        assert "Sản phẩm mẫu phục vụ kiểm thử cửa hàng" not in product[1]
        assert product[2:] == (123456, 120000)
        assert stock == 7
        assert order == ('PAID', 100000)
    finally:
        conn.close()
