"""AURA FASHION admin dashboard; register after authentication and order/product routes."""
from flask import render_template, jsonify
from database.db import get_db_connection


def register_admin_dashboard_routes(app, require_admin):
    @app.get('/admin/dashboard')
    @require_admin
    def admin_dashboard_page():
        return render_template('admin_dashboard.html')

    @app.get('/api/admin/dashboard/summary')
    @require_admin
    def admin_dashboard_summary():
        conn = get_db_connection()
        try:
            products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
            active_products = conn.execute('SELECT COUNT(*) FROM products WHERE is_published=1').fetchone()[0]
            orders = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM orders WHERE status='PENDING_PAYMENT'").fetchone()[0]
            revenue = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status IN ('PAID','SHIPPING','DELIVERED')").fetchone()[0]
            low_stock = conn.execute('SELECT COUNT(*) FROM product_variants WHERE stock_quantity <= 5').fetchone()[0]
            return jsonify(success=True, stats=dict(products=products, active_products=active_products,
                         orders=orders, pending=pending, revenue=revenue, low_stock_variants=low_stock))
        finally:
            conn.close()
