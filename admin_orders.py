"""Admin order management for existing AURA FASHION SQLite schema.
Only allow fulfillment transitions; payment finalization remains with payment service.
"""
import sqlite3
from flask import jsonify, request
from database.db import get_db_connection

STATES = {'PENDING_PAYMENT', 'PAID', 'CANCELLED', 'SHIPPING', 'DELIVERED'}
ALLOWED = {
    'PENDING_PAYMENT': {'CANCELLED'},
    'PAID': {'SHIPPING'},
    'SHIPPING': {'DELIVERED'},
    'DELIVERED': set(),
    'CANCELLED': set(),
}


def register_admin_order_routes(app, require_admin, require_csrf):
    @app.get('/api/admin/orders')
    @require_admin
    def admin_list_orders():
        status = request.args.get('status', '').strip().upper()
        if status and status not in STATES:
            return jsonify(success=False, error='Trang thai khong hop le'), 400
        conn = get_db_connection()
        try:
            sql = '''SELECT o.id, o.order_code, o.customer_name, o.customer_phone,
                            o.total_amount, o.status, o.payment_method, o.created_at,
                            (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id=o.id) item_count
                     FROM orders o'''
            args = []
            if status:
                sql += ' WHERE o.status = ?'
                args.append(status)
            sql += ' ORDER BY o.id DESC LIMIT 100'
            orders = [dict(row) for row in conn.execute(sql, args)]
            return jsonify(success=True, orders=orders, count=len(orders))
        finally:
            conn.close()

    @app.get('/api/admin/orders/<int:order_id>')
    @require_admin
    def admin_order_detail(order_id):
        conn = get_db_connection()
        try:
            order = conn.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
            if order is None:
                return jsonify(success=False, error='Khong tim thay don hang'), 404
            items = conn.execute('''
                SELECT oi.id, oi.variant_id, oi.quantity, oi.unit_price, oi.subtotal,
                       pv.sku, pv.color, pv.size, p.name AS product_name
                FROM order_items oi JOIN product_variants pv ON pv.id=oi.variant_id
                JOIN products p ON p.id=pv.product_id
                WHERE oi.order_id=? ORDER BY oi.id
            ''', (order_id,)).fetchall()
            payments = conn.execute('''SELECT id, transaction_code, amount, status, created_at
                                       FROM payments WHERE order_id=? ORDER BY id''', (order_id,)).fetchall()
            history = conn.execute('''SELECT id, old_status, new_status, note, changed_at
                                      FROM order_status_history WHERE order_id=? ORDER BY id''', (order_id,)).fetchall()
            return jsonify(success=True, order=dict(order), items=[dict(r) for r in items],
                           payments=[dict(r) for r in payments], history=[dict(r) for r in history])
        finally:
            conn.close()

    @app.patch('/api/admin/orders/<int:order_id>/status')
    @require_admin
    @require_csrf
    def admin_change_order_status(order_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get('status'), str):
            return jsonify(success=False, error='Can gui JSON voi truong status'), 400
        desired = data['status'].strip().upper()
        if desired not in STATES:
            return jsonify(success=False, error='Trang thai khong hop le'), 400
        conn = get_db_connection()
        try:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT status FROM orders WHERE id=?', (order_id,)).fetchone()
            if row is None:
                conn.rollback()
                return jsonify(success=False, error='Khong tim thay don hang'), 404
            previous = row['status']
            if desired not in ALLOWED.get(previous, set()):
                conn.rollback()
                return jsonify(success=False, error=f'Khong cho phep: {previous} -> {desired}'), 409
            if desired == 'CANCELLED':
                # Stock was deducted at order creation in the existing db.py.
                # Cancel only pending order with a pending payment; restore exactly once.
                payments = conn.execute('SELECT status FROM payments WHERE order_id=?', (order_id,)).fetchall()
                if not payments or any(p['status'] != 'PENDING' for p in payments):
                    conn.rollback()
                    return jsonify(success=False, error='Thanh toan khong con PENDING; khong the huy an toan'), 409
                items = conn.execute('SELECT variant_id, quantity FROM order_items WHERE order_id=?', (order_id,)).fetchall()
                for item in items:
                    conn.execute('UPDATE product_variants SET stock_quantity = stock_quantity + ? WHERE id=?',
                                 (item['quantity'], item['variant_id']))
                conn.execute("UPDATE payments SET status='CANCELLED' WHERE order_id=? AND status='PENDING'", (order_id,))
            updated = conn.execute('UPDATE orders SET status=? WHERE id=? AND status=?',
                                   (desired, order_id, previous))
            if updated.rowcount != 1:
                raise RuntimeError('Trang thai don hang vua thay doi')
            # Database trigger trg_track_order_status writes history.
            conn.commit()
            return jsonify(success=True, order_id=order_id, old_status=previous, status=desired)
        except (sqlite3.Error, RuntimeError):
            conn.rollback()
            app.logger.exception('Failed to update order %s', order_id)
            return jsonify(success=False, error='Loi cap nhat don hang'), 500
        finally:
            conn.close()
