"""AURA customer portal: customer-owned orders and profile, without changing admin endpoints."""
import sqlite3
from flask import render_template, jsonify, request, g
from database.db import get_db_connection, sp_create_order_and_deduct_stock


def register_customer_routes(app, require_login, require_csrf):
    @app.get('/customer')
    def customer_page():
        return render_template('customer_portal.html')

    @app.get('/api/customer/orders')
    @require_login
    def customer_orders():
        if g.user['role'] != 'CUSTOMER':
            return jsonify(success=False, error='Chỉ dành cho Customer'), 403
        c = get_db_connection()
        try:
            rows = c.execute('''SELECT o.id, o.order_code, o.total_amount, o.status, o.created_at
                FROM orders o JOIN customer_order_links l ON l.order_id=o.id
                WHERE l.user_id=? ORDER BY o.id DESC''', (g.user['id'],)).fetchall()
            return jsonify(success=True, orders=[dict(x) for x in rows])
        finally:
            c.close()

    @app.get('/api/customer/orders/<int:order_id>')
    @require_login
    def customer_order_detail(order_id):
        if g.user['role'] != 'CUSTOMER':
            return jsonify(success=False, error='Chỉ dành cho Customer'), 403
        c = get_db_connection()
        try:
            order = c.execute('''SELECT o.* FROM orders o JOIN customer_order_links l ON l.order_id=o.id
                WHERE o.id=? AND l.user_id=?''', (order_id, g.user['id'])).fetchone()
            if not order:
                return jsonify(success=False, error='Không tìm thấy đơn hàng'), 404
            items = c.execute('''SELECT oi.variant_id, oi.quantity, oi.unit_price, oi.subtotal,
                pv.sku, pv.size, pv.color, p.name FROM order_items oi
                JOIN product_variants pv ON pv.id=oi.variant_id
                JOIN products p ON p.id=pv.product_id WHERE oi.order_id=?''', (order_id,)).fetchall()
            history = c.execute('''SELECT old_status, new_status, changed_at FROM order_status_history
                WHERE order_id=? ORDER BY id''', (order_id,)).fetchall()
            return jsonify(success=True, order=dict(order), items=[dict(x) for x in items], history=[dict(x) for x in history])
        finally:
            c.close()

    @app.patch('/api/customer/profile')
    @require_login
    @require_csrf
    def customer_update_profile():
        if g.user['role'] != 'CUSTOMER':
            return jsonify(success=False, error='Chỉ dành cho Customer'), 403
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(success=False, error='JSON không hợp lệ'), 400
        name = (data.get('full_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        if not 1 <= len(name) <= 120 or len(phone) > 30:
            return jsonify(success=False, error='Họ tên hoặc số điện thoại không hợp lệ'), 400
        c = get_db_connection()
        try:
            c.execute('UPDATE users SET full_name=?, phone=? WHERE id=? AND role=?', (name, phone, g.user['id'], 'CUSTOMER'))
            c.commit()
            return jsonify(success=True)
        finally:
            c.close()

    @app.post('/api/customer/checkout')
    @require_login
    @require_csrf
    def customer_checkout():
        if g.user['role'] != 'CUSTOMER':
            return jsonify(success=False, error='Chỉ dành cho Customer'), 403
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get('items'), list):
            return jsonify(success=False, error='Dữ liệu đơn hàng không hợp lệ'), 400
        raw_items = data['items']
        if not 1 <= len(raw_items) <= 30:
            return jsonify(success=False, error='Giỏ hàng phải có 1-30 dòng'), 400
        phone = (data.get('phone') or g.user.get('phone') or '').strip()
        address = (data.get('address') or '').strip()
        if not (5 <= len(phone) <= 30 and 5 <= len(address) <= 300):
            return jsonify(success=False, error='Vui lòng nhập số điện thoại và địa chỉ hợp lệ'), 400
        quantities = {}
        for item in raw_items:
            if not isinstance(item, dict) or type(item.get('variant_id')) is not int or type(item.get('quantity')) is not int:
                return jsonify(success=False, error='variant_id và quantity phải là số nguyên'), 400
            vid, qty = item['variant_id'], item['quantity']
            if vid <= 0 or not 1 <= qty <= 20:
                return jsonify(success=False, error='ID hoặc số lượng không hợp lệ'), 400
            quantities[vid] = quantities.get(vid, 0) + qty
            if quantities[vid] > 20:
                return jsonify(success=False, error='Vượt số lượng tối đa'), 400
        result = sp_create_order_and_deduct_stock(
            {
                'name': g.user['full_name'],
                'phone': phone,
                'address': address,
            },
            [{'variant_id': variant_id, 'quantity': quantity}
             for variant_id, quantity in quantities.items()],
            'VIRTUAL_SANDBOX',
            customer_user_id=g.user['id'],
        )
        if not result['success']:
            return jsonify(result), 409
        return jsonify(**result, status='PENDING_PAYMENT'), 201
