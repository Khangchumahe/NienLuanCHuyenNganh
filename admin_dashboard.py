from datetime import datetime, timedelta, timezone

from flask import (
    render_template,
    jsonify,
    redirect,
    url_for,
    abort
)

from database.db import get_db_connection


def register_admin_dashboard_routes(app, require_admin, current_user):

    # Dashboard chỉ dành cho Admin.
    @app.get('/admin/dashboard')
    def admin_dashboard_page():
        user = current_user()

        if not user:
            return redirect(url_for('login_page'))

        if user['role'] != 'ADMIN':
            abort(403)

        return render_template(
            'admin_dashboard.html',
            is_admin=True,
            initial_page='overview'
        )

    # Trang làm việc của Staff.
    @app.get('/staff/orders')
    def staff_orders_page():
        return management_page('orders')

    @app.get('/staff/products')
    def staff_products_page():
        return management_page('products')

    def management_page(page):
        user = current_user()

        if not user:
            return redirect(url_for('login_page'))

        if user['role'] not in ('ADMIN', 'STAFF'):
            abort(403)

        return render_template(
            'admin_dashboard.html',
            is_admin=user['role'] == 'ADMIN',
            initial_page=page
        )

    # API thống kê chỉ dành cho Admin.
    @app.get('/api/admin/dashboard/summary')
    @require_admin
    def admin_dashboard_summary():
        today = datetime.now(
            timezone(timedelta(hours=7))
        ).date()

        first_day = today - timedelta(days=6)
        conn = get_db_connection()

        try:
            # Đọc các số liệu trong cùng một snapshot.
            conn.execute('BEGIN')

            stats = dict(conn.execute('''
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM products
                    ) AS products,

                    (
                        SELECT COUNT(*)
                        FROM products
                        WHERE is_published=1
                    ) AS active_products,

                    COUNT(*) AS orders,

                    COALESCE(SUM(
                        CASE
                            WHEN status='PENDING_PAYMENT'
                            THEN 1
                            ELSE 0
                        END
                    ), 0) AS pending,

                    COALESCE(SUM(
                        CASE
                            WHEN status IN (
                                'PAID',
                                'SHIPPING',
                                'DELIVERED'
                            )
                            THEN total_amount
                            ELSE 0
                        END
                    ), 0) AS revenue,

                    (
                        SELECT COUNT(*)
                        FROM product_variants
                        WHERE stock_quantity<=5
                    ) AS low_stock_variants

                FROM orders
            ''').fetchone())

            # Doanh thu theo ngày tạo đơn, múi giờ Việt Nam.
            revenue_rows = conn.execute('''
                SELECT
                    date(created_at, '+7 hours') AS day,
                    SUM(total_amount) AS revenue

                FROM orders

                WHERE status IN (
                    'PAID',
                    'SHIPPING',
                    'DELIVERED'
                )

                AND date(created_at, '+7 hours')
                    BETWEEN ? AND ?

                GROUP BY date(created_at, '+7 hours')
            ''', (
                first_day.isoformat(),
                today.isoformat()
            )).fetchall()

            revenue_by_day = {
                row['day']: row['revenue']
                for row in revenue_rows
            }

            daily_revenue = []

            for offset in range(7):
                day = first_day + timedelta(days=offset)

                daily_revenue.append({
                    'date': day.isoformat(),
                    'label': day.strftime('%d/%m'),
                    'revenue': revenue_by_day.get(
                        day.isoformat(),
                        0
                    )
                })

            status_counts = {
                row['status']: row['count']
                for row in conn.execute('''
                    SELECT
                        status,
                        COUNT(*) AS count
                    FROM orders
                    GROUP BY status
                ''')
            }

            states = [
                'PENDING_PAYMENT',
                'PAID',
                'SHIPPING',
                'DELIVERED',
                'CANCELLED'
            ]

            states += sorted(set(status_counts) - set(states))

            order_statuses = [
                {
                    'status': state,
                    'count': status_counts.get(state, 0)
                }
                for state in states
            ]

            return jsonify(
                success=True,
                stats=stats,
                charts={
                    'daily_revenue': daily_revenue,
                    'order_statuses': order_statuses
                }
            )

        finally:
            conn.close()