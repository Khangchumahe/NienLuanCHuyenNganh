"""Admin API to create and list product color/size variants; adds no schema changes."""
import sqlite3
from flask import Blueprint, jsonify, request
from database.db import get_db_connection


def register_admin_variant_routes(app, require_admin, require_csrf):
    bp = Blueprint('admin_variant_create', __name__)

    @bp.get('/api/admin/products/<int:product_id>/variants')
    @require_admin
    def list_variants(product_id):
        conn = get_db_connection()
        try:
            product = conn.execute('SELECT id FROM products WHERE id=?', (product_id,)).fetchone()
            if product is None:
                return jsonify(success=False, error='Không tìm thấy sản phẩm'), 404
            rows = conn.execute(
                'SELECT id, product_id, sku, color, size, stock_quantity '
                'FROM product_variants WHERE product_id=? ORDER BY id', (product_id,)
            ).fetchall()
            return jsonify(success=True, variants=[dict(row) for row in rows])
        finally:
            conn.close()

    @bp.post('/api/admin/products/<int:product_id>/variants')
    @require_admin
    @require_csrf
    def create_variant(product_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(success=False, error='Cần gửi JSON object hợp lệ'), 400
        values = {}
        for key in ('sku', 'color', 'size'):
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                return jsonify(success=False, error=f'{key} phải là chuỗi không rỗng'), 400
            values[key] = value.strip()
        if any(len(values[k]) > 100 for k in values):
            return jsonify(success=False, error='SKU, màu hoặc size quá dài'), 400
        n = data.get('stock_quantity')
        if type(n) is not int or n < 0:
            return jsonify(success=False, error='stock_quantity phải là số nguyên không âm'), 400
        conn = get_db_connection()
        try:
            # BEGIN IMMEDIATE prevents concurrent duplicate color/size inserts.
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute('SELECT 1 FROM products WHERE id=?', (product_id,)).fetchone() is None:
                conn.rollback()
                return jsonify(success=False, error='Không tìm thấy sản phẩm'), 404
            duplicated = conn.execute(
                'SELECT 1 FROM product_variants '
                'WHERE product_id=? AND lower(trim(color))=lower(?) AND lower(trim(size))=lower(?)',
                (product_id, values['color'], values['size'])
            ).fetchone()
            if duplicated:
                conn.rollback()
                return jsonify(success=False, error='Size và màu này đã tồn tại cho sản phẩm'), 409
            cur = conn.execute(
                'INSERT INTO product_variants (product_id,sku,color,size,stock_quantity) VALUES (?,?,?,?,?)',
                (product_id, values['sku'], values['color'], values['size'], n)
            )
            conn.commit()
            return jsonify(success=True, variant_id=cur.lastrowid, product_id=product_id), 201
        except sqlite3.IntegrityError:
            conn.rollback()
            return jsonify(success=False, error='SKU bị trùng hoặc dữ liệu không hợp lệ'), 409
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    app.register_blueprint(bp)
