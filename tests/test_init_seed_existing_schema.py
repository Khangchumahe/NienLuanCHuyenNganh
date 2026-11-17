from database import db


def test_init_db_seeds_products_when_categories_exist_but_products_are_empty(monkeypatch, tmp_path):
    db_path = tmp_path / "categories-only.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    db.ensure_schema()
    conn = db.get_db_connection()
    try:
        conn.execute(
            "INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)",
            ("Danh mục có sẵn", "existing-category", "Fixture"),
        )
        conn.commit()
    finally:
        conn.close()

    db.init_db()
    conn = db.get_db_connection()
    try:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0
        assert conn.execute(
            "SELECT COUNT(*) FROM categories WHERE slug='existing-category'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_init_db_does_not_duplicate_existing_product_catalog():
    conn = db.get_db_connection()
    try:
        before = tuple(
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("products", "product_variants")
        )
    finally:
        conn.close()
    db.init_db()
    conn = db.get_db_connection()
    try:
        after = tuple(
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("products", "product_variants")
        )
        assert after == before
    finally:
        conn.close()


def test_init_db_does_not_change_seeded_150_product_catalog(monkeypatch, tmp_path):
    from seed_products import seed_catalog

    db_path = tmp_path / "demo-150.db"
    seed_catalog(db_path, write_index_html=False, image_dir=tmp_path / "images")
    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    conn = db.get_db_connection()
    try:
        before = tuple(
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("products", "product_variants")
        )
    finally:
        conn.close()
    db.init_db()
    conn = db.get_db_connection()
    try:
        after = tuple(
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("products", "product_variants")
        )
        assert before == after == (150, 600)
    finally:
        conn.close()
