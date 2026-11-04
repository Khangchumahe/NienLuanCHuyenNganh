"""Admin product + inventory API for AURA FASHION. SQLite schema-compatible."""
import sqlite3
from contextlib import contextmanager
from flask import Blueprint, jsonify, request
from database.db import get_db_connection


@contextmanager
def _transaction():
    conn = get_db_connection()
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def _json():
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        raise ValueError('Gửi JSON object hợp lệ')
    return d


def _text(value, key, required=True):
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f'{key} phải là chuỗi không rỗng')
    return value.strip()


def _money(value, key):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1_000_000_000_000:
        raise ValueError(f'{key} phải là số trong khoảng 0 đến 1 nghìn tỷ')
    return value


def _stock(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('stock_quantity phải là số nguyên không âm')
    return value


def _product_data(d, old=None):
    out = {}
    for key in ('name', 'slug'):
        if key in d or old is None:
            out[key] = _text(d.get(key), key)
    for key in ('description', 'material', 'style', 'size_guide', 'image_url'):
        if key in d:
            out[key] = _text(d[key], key, required=False)
    if 'category_id' in d or old is None:
        n = d.get('category_id')
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ValueError('category_id phải là số nguyên dương')
        out['category_id'] = n
    for key in ('price', 'discount_price'):
        if key in d or (key == 'price' and old is None):
            out[key] = None if key == 'discount_price' and d[key] is None else _money(d.get(key), key)
    effective = dict(old or {})
    effective.update(out)
    if effective.get('discount_price') is not None and effective['discount_price'] > effective['price']:
        raise ValueError('discount_price không được lớn hơn price')
    return out


def register_admin_product_routes(app, require_admin, require_csrf, rag_service=None):
    bp = Blueprint('admin_product_crud', __name__)

    @bp.get('/api/admin/products')
    @require_admin
    def list_products():
        conn = get_db_connection()
        try:
            rows = conn.execute('''SELECT p.*, c.name AS category_name,
              COALESCE(SUM(v.stock_quantity), 0) AS total_stock
              FROM products p JOIN categories c ON p.category_id=c.id
              LEFT JOIN product_variants v ON v.product_id=p.id
              GROUP BY p.id ORDER BY p.id DESC''').fetchall()
            return jsonify(success=True, products=[dict(row) for row in rows])
        finally:
            conn.close()

    @bp.post('/api/admin/products')
    @require_admin
    @require_csrf
    def add_product():
        try:
            fields = _product_data(_json())
            with _transaction() as conn:
                columns = ', '.join(fields)
                marks = ', '.join('?' for _ in fields)
                cur = conn.execute(f'INSERT INTO products ({columns}) VALUES ({marks})', list(fields.values()))
                new_id = cur.lastrowid
            return jsonify(success=True, product_id=new_id), 201
        except ValueError as e:
            return jsonify(success=False, error=str(e)), 400
        except sqlite3.IntegrityError:
            return jsonify(success=False, error='Slug trùng hoặc danh mục không tồn tại'), 409

    @bp.put('/api/admin/products/<int:product_id>')
    @require_admin
    @require_csrf
    def update_product(product_id):
        try:
            d = _json()
            with _transaction() as conn:
                row = conn.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
                if row is None:
                    return jsonify(success=False, error='Không tìm thấy sản phẩm'), 404
                fields = _product_data(d, dict(row))
                if not fields:
                    return jsonify(success=False, error='Không có trường cần cập nhật'), 400
                changes = ', '.join(f'{k}=?' for k in fields)
                conn.execute(f'UPDATE products SET {changes} WHERE id=?', [*fields.values(), product_id])
            return jsonify(success=True, product_id=product_id)
        except ValueError as e:
            return jsonify(success=False, error=str(e)), 400
        except sqlite3.IntegrityError:
            return jsonify(success=False, error='Slug trùng hoặc danh mục không tồn tại'), 409

    @bp.patch('/api/admin/products/<int:product_id>/visibility')
    @require_admin
    @require_csrf
    def set_visibility(product_id):
        try:
            d = _json()
            if type(d.get('is_published')) is not bool:
                raise ValueError('is_published phải là true hoặc false')
            with _transaction() as conn:
                cur = conn.execute('UPDATE products SET is_published=? WHERE id=?', (int(d['is_published']), product_id))
                if cur.rowcount == 0:
                    return jsonify(success=False, error='Không tìm thấy sản phẩm'), 404
            return jsonify(success=True, product_id=product_id, is_published=d['is_published'])
        except ValueError as e:
            return jsonify(success=False, error=str(e)), 400

    @bp.patch('/api/admin/variants/<int:variant_id>/stock')
    @require_admin
    @require_csrf
    def set_stock(variant_id):
        try:
            n = _stock(_json().get('stock_quantity'))
            with _transaction() as conn:
                cur = conn.execute('UPDATE product_variants SET stock_quantity=? WHERE id=?', (n, variant_id))
                if cur.rowcount == 0:
                    return jsonify(success=False, error='Không tìm thấy biến thể'), 404
                # trg_log_inventory_change trong schema.sql tự ghi log.
            return jsonify(success=True, variant_id=variant_id, stock_quantity=n)
        except ValueError as e:
            return jsonify(success=False, error=str(e)), 400

    app.register_blueprint(bp)
