"""
Flask Application for Clothing Store
Tích hợp: RAG AI Chatbot, Virtual Payment Simulator, SQL Database (Triggers & Stored Procedures)
"""

from collections import OrderedDict
from threading import Lock
from time import monotonic
import json

from dotenv import load_dotenv
from flask import Flask, Response, render_template, request, jsonify, session, g
from functools import wraps
import os
import secrets

load_dotenv()

from database.db import (
    init_db, get_all_products, get_product_by_id, 
    sp_create_order_and_deduct_stock, get_db_stats,
    create_user, verify_user, get_db_connection
)
from services.rag_engine import rag_service
from services.payment_service import (
    generate_checksum, process_mock_payment_callback,
    create_zalopay_order_payload, OFFICIAL_TEST_CARDS, OFFICIAL_WALLETS,
    process_card_or_wallet_payment
)

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


def require_csrf(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = session.get('csrf_token')
        supplied = request.headers.get('X-CSRF-Token', '')
        if not expected or not secrets.compare_digest(expected, supplied):
            return jsonify(success=False, error='CSRF token không hợp lệ'), 403
        return view(*args, **kwargs)
    return wrapped


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
    if not product or not product['is_published']:
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
    payment_method = data.get('payment_method', 'ZALOPAY_SANDBOX')

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

    # Sinh payload ZaloPay Sandbox chính thức tương thích zalopay.js.
    result['zalopay'] = create_zalopay_order_payload(
        order_code=result['order_code'],
        transaction_code=result['transaction_code'],
        amount=result['total_amount'],
        customer_info=customer_info,
        items=cart_items
    )

    return jsonify(result)


@app.route('/api/payment/test-cards', methods=['GET'])
def api_test_cards():
    """API lấy danh sách thẻ tín dụng mẫu có sẵn chính thức để hiển thị trên giao diện"""
    return jsonify({
        'success': True,
        'cards': OFFICIAL_TEST_CARDS,
        'wallets': OFFICIAL_WALLETS
    })


@app.route('/api/payment/process-card', methods=['POST'])
def api_process_card_payment():
    """API xác thực và xử lý thanh toán qua thẻ tín dụng/ATM hoặc ví ZaloPay kèm OTP 3D-Secure"""
    data = request.get_json() or {}
    transaction_code = data.get('transaction_code')
    payment_type = data.get('payment_type', 'CREDIT_CARD')
    card_data = data.get('card_data')
    wallet_data = data.get('wallet_data')
    otp = data.get('otp', '').strip()

    if not transaction_code:
        return jsonify({'success': False, 'message': 'Thiếu mã giao dịch!'}), 400

    result = process_card_or_wallet_payment(
        transaction_code=transaction_code,
        payment_type=payment_type,
        card_data=card_data,
        wallet_data=wallet_data,
        otp=otp
    )

    if result.get('success'):
        # Cập nhật lại kho cho RAG
        rag_service.sync_knowledge_base()

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

from services.agentic_rag import AgenticRAGEngine

agentic_ai = AgenticRAGEngine()

_chat_requests = OrderedDict()
_chat_requests_lock = Lock()


def _chat_rate_allowed(address):
    now = monotonic()
    with _chat_requests_lock:
        while _chat_requests and next(iter(_chat_requests.values()))[0] <= now:
            _chat_requests.popitem(last=False)
        if address not in _chat_requests and len(_chat_requests) >= 4096:
            return False
        expires, count = _chat_requests.get(address, (now + 60, 0))
        if count >= 20:
            return False
        _chat_requests[address] = (expires, count + 1)
        return True


@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ'), 400
    message = data.get('message')
    if not isinstance(message, str) or not message.strip():
        return jsonify(success=False, error='Vui lòng nhập tin nhắn hợp lệ'), 400
    message = message.strip()
    if len(message) > 2000:
        return jsonify(success=False, error='Tin nhắn tối đa 2.000 ký tự'), 400
    if not _chat_rate_allowed(request.remote_addr):
        return jsonify(success=False, error='Bạn gửi nhiều tin nhắn quá nhanh. Hãy thử lại sau ít phút.'), 429, {
            'Retry-After': '60',
        }

    history = data.get('conversation_history', [])
    if not isinstance(history, list):
        history = []
    history = [
        {'role': entry['role'], 'content': entry['content'].strip()[:2000]}
        for entry in history[-12:]
        if isinstance(entry, dict)
        and entry.get('role') in ('user', 'assistant')
        and isinstance(entry.get('content'), str)
        and entry['content'].strip()
    ]
    recent_ids = data.get('recent_product_ids', [])
    recent_ids = list(dict.fromkeys(
        product_id for product_id in recent_ids[:3]
        if type(product_id) is int and 0 < product_id < 2**63
    )) if isinstance(recent_ids, list) else []
    user = current_user()
    customer_user_id = user['id'] if user and user['role'] == 'CUSTOMER' else None

    def result():
        try:
            return {
                'success': True,
                'data': agentic_ai.chat_with_agent(message, history, customer_user_id, recent_ids),
            }
        except Exception:
            app.logger.exception('Chat processing failed')
            return {'success': False, 'error': 'Chưa thể kiểm tra dữ liệu cửa hàng. Bạn thử lại sau nhé.'}

    if any(mime == 'application/x-ndjson' and quality > 0 for mime, quality in request.accept_mimetypes):
        def events():
            yield '{"event":"retrieving"}\n'
            yield json.dumps({'event': 'answer', **result()}, ensure_ascii=False) + '\n'

        return Response(events(), mimetype='application/x-ndjson', headers={
            'Cache-Control': 'no-store',
            'X-Accel-Buffering': 'no',
        })
    payload = result()
    return jsonify(payload), 200 if payload['success'] else 503

@app.route('/api/ai/sync-rag', methods=['POST'])
@require_admin
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
    require_admin,
    require_csrf,
    rag_service
)
# Admin - Quan ly size, mau sac
from admin_variants import register_admin_variant_routes

register_admin_variant_routes(
    app,
    require_admin,
    require_csrf
)


# Admin - Quan ly don hang
from admin_orders import register_admin_order_routes

register_admin_order_routes(
    app,
    require_admin,
    require_csrf
)


# Admin Dashboard
from admin_dashboard import register_admin_dashboard_routes

register_admin_dashboard_routes(
    app,
    require_admin
)


# Customer Portal
from customer_portal import register_customer_routes

register_customer_routes(
    app,
    require_login,
    require_csrf
)




if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ĐANG KHỞI CHẠY HỆ THỐNG CỬA HÀNG THỜI TRANG TÍCH HỢP RAG AI")
    print("🔗 Địa chỉ truy cập: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
