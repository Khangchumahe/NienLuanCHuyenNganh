"""
Flask Application for Clothing Store
Tích hợp: RAG AI Chatbot, Virtual Payment Simulator, SQL Database (Triggers & Stored Procedures)
"""

from flask import Flask, render_template, request, jsonify, session, g, redirect, url_for
from functools import wraps
import os
import secrets
from database.db import (
    init_db, get_all_products, get_product_by_id, 
    sp_create_order_and_deduct_stock, get_db_stats,
    create_user, verify_user, get_db_connection
)
from services.rag_engine import rag_service
from services.payment_service import generate_checksum, process_mock_payment_callback

app = Flask(__name__)
# Thiết lập FLASK_SECRET_KEY trong môi trường khi triển khai thật.
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_COOKIE_SECURE') == '1',
    MAX_CONTENT_LENGTH=1024 * 1024,
)


def current_user():
    user_id = session.get('user_id')
    if not isinstance(user_id, int):
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            'SELECT id, email, full_name, phone, role FROM users '
            'WHERE id = ? AND is_active = 1', (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        g.user = current_user()
        if g.user is None:
            return jsonify(success=False, error='Bạn cần đăng nhập'), 401
        return view(*args, **kwargs)
    return wrapped


def require_admin(view):
    @wraps(view)
    @require_login
    def wrapped(*args, **kwargs):
        if g.user['role'] != 'ADMIN':
            return jsonify(success=False, error='Bạn không có quyền Admin'), 403
        return view(*args, **kwargs)
    return wrapped


def require_management(view):
    @wraps(view)
    @require_login
    def wrapped(*args, **kwargs):
        if g.user['role'] not in ('ADMIN', 'STAFF'):
            return jsonify(
                success=False,
                error='Bạn không có quyền quản lý'
            ), 403
        return view(*args, **kwargs)
    return wrapped


def require_csrf(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = session.get('csrf_token')
        supplied = request.headers.get('X-CSRF-Token', '')
        if not expected or not secrets.compare_digest(expected, supplied):
            return jsonify(success=False, error='CSRF token không hợp lệ'), 403
        return view(*args, **kwargs)
    return wrapped


def account_home(user):
    if user['role'] == 'ADMIN':
        return url_for('admin_dashboard_page')
    if user['role'] == 'STAFF':
        return url_for('staff_orders_page')
    return url_for('customer_page')


@app.get('/login')
def login_page():
    user = current_user()
    if user:
        return redirect(account_home(user))
    return render_template('customer_portal.html')


@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ'), 400
    result = create_user(data.get('email'), data.get('password'),
                         data.get('full_name'), data.get('phone'))
    return jsonify(result), (201 if result['success'] else 400)


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ'), 400
    user = verify_user(data.get('email'), data.get('password'))
    if not user:
        return jsonify(success=False, error='Email hoặc mật khẩu không đúng'), 401
    session.clear()
    session['user_id'] = user['id']
    session['csrf_token'] = secrets.token_urlsafe(32)
    session.permanent = False
    return jsonify(success=True, user=user, csrf_token=session['csrf_token'])


@app.route('/api/auth/me', methods=['GET'])
@require_login
def api_me():
    return jsonify(success=True, user=g.user, csrf_token=session.get('csrf_token'))


@app.route('/api/auth/logout', methods=['POST'])
@require_login
@require_csrf
def api_logout():
    session.clear()
    return jsonify(success=True, message='Đã đăng xuất')


# Khởi tạo Database và nạp dữ liệu mẫu
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def api_products():
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', type=str)
    products = get_all_products(category_id=category_id, search=search)
    return jsonify({'success': True, 'products': products})

@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm'}), 404
    return jsonify({'success': True, 'product': product})


@app.route('/api/orders/checkout', methods=['POST'])
def api_checkout():
    """API dat hang va lien ket voi Customer"""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(success=False, error='JSON khong hop le'), 400

    customer_info = data.get('customer', {})
    cart_items = data.get('items', [])
    payment_method = data.get('payment_method', 'VIRTUAL_SANDBOX')

    if not isinstance(cart_items, list) or not cart_items:
        return jsonify(success=False, error='Gio hang dang trong!'), 400

    # Lay Customer ID tu phien dang nhap
    customer_user_id = None
    session_user_id = session.get('user_id')

    if session_user_id is not None:
        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT id, role FROM users WHERE id = ?",
                (session_user_id,)
            ).fetchone()

            if user and user['role'] == 'CUSTOMER':
                customer_user_id = user['id']
        finally:
            conn.close()

    # Tao don, tru kho va lien ket Customer trong transaction
    result = sp_create_order_and_deduct_stock(
        customer_info,
        cart_items,
        payment_method,
        customer_user_id=customer_user_id
    )

    if not result['success']:
        return jsonify(result), 400

    # Dong bo RAG sau khi don duoc tao
    try:
        rag_service.sync_knowledge_base()
    except Exception:
        app.logger.exception('RAG sync failed after checkout')

    checksum = generate_checksum(
        result['transaction_code'],
        result['total_amount']
    )
    result['checksum'] = checksum

    return jsonify(result)


@app.route('/api/payment/simulate-callback', methods=['POST'])
def api_payment_callback():
    """API Webhook mô phỏng phản hồi từ cổng thanh toán ảo"""
    data = request.get_json() or {}
    transaction_code = data.get('transaction_code')
    status = data.get('status', 'SUCCESS') # SUCCESS hoặc CANCELLED

    if not transaction_code:
        return jsonify({'success': False, 'error': 'Thiếu mã giao dịch!'}), 400

    result = process_mock_payment_callback(transaction_code, status)
    # Cập nhật lại kho cho RAG
    rag_service.sync_knowledge_base()
    return jsonify(result)

@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    """API Chatbot AI sử dụng RAG Engine"""
    data = request.get_json() or {}
    user_query = data.get('message', '').strip()
    
    if not user_query:
        return jsonify({'success': False, 'error': 'Tin nhắn không được để trống'}), 400

    response_data = rag_service.generate_response(user_query)
    return jsonify({
        'success': True,
        'data': response_data
    })

@app.route('/api/ai/sync-rag', methods=['POST'])
@require_management
@require_csrf
def api_sync_rag():
    """Đồng bộ lại Knowledge Base của RAG từ SQL"""
    count = rag_service.sync_knowledge_base()
    return jsonify({'success': True, 'synced_count': count, 'message': f'Đã đồng bộ {count} tài liệu sản phẩm vào RAG!'})

@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def api_admin_stats():
    """Lấy dữ liệu thống kê kiểm tra Trigger và Database"""
    stats = get_db_stats()
    return jsonify({'success': True, 'stats': stats})


# Admin - Quan ly san pham va kho hang
from admin_products import register_admin_product_routes

register_admin_product_routes(
    app,
    require_management,
    require_csrf,
    rag_service
)
# Admin - Quan ly size, mau sac
from admin_variants import register_admin_variant_routes

register_admin_variant_routes(
    app,
    require_management,
    require_csrf
)


# Admin - Quan ly don hang
from admin_orders import register_admin_order_routes

register_admin_order_routes(
    app,
    require_management,
    require_csrf
)


# Admin Dashboard
from admin_dashboard import register_admin_dashboard_routes

register_admin_dashboard_routes(
    app,
    require_admin, current_user)


# Customer Portal
from customer_portal import register_customer_routes

register_customer_routes(
    app,
    require_login,
    require_csrf
)




from product_social import register_product_social
register_product_social(app, require_login, require_csrf, current_user)


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ĐANG KHỞI CHẠY HỆ THỐNG CỬA HÀNG THỜI TRANG TÍCH HỢP RAG AI")
    print("🔗 Địa chỉ truy cập: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
