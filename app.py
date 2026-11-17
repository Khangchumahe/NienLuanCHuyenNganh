"""
Flask Application for Clothing Store
Tích hợp: RAG AI Chatbot, Virtual Payment Simulator, SQL Database (Triggers & Stored Procedures)
"""

from collections import OrderedDict
from threading import Lock
from time import monotonic
import json
import hashlib
import math

from dotenv import load_dotenv
from flask import (
    Flask, Response, abort, render_template, request, jsonify, session, g,
    redirect, url_for,
)
from functools import wraps
import os
import secrets
from werkzeug.exceptions import HTTPException

load_dotenv()

from database.db import (
    init_db, get_all_products, get_product_by_id, 
    sp_create_order_and_deduct_stock, get_db_stats,
    create_user, verify_user, get_db_connection, ensure_schema
)
ensure_schema()
init_db()
from services.rag_engine import rag_service
from services.payment_service import (
    generate_checksum, verify_checksum, process_mock_payment_callback,
    create_zalopay_order_payload, OFFICIAL_TEST_CARDS, OFFICIAL_WALLETS,
    process_card_or_wallet_payment
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key and os.environ.get('APP_ENV', '').lower() == 'development':
    app.secret_key = secrets.token_hex(32)
if not app.secret_key:
    raise RuntimeError('SECRET_KEY phải được cấu hình trong môi trường.')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_COOKIE_SECURE') == '1',
    MAX_CONTENT_LENGTH=1024 * 1024,
)


def debug_enabled(value=None):
    """Enable Flask debug only for the explicit value FLASK_DEBUG=1."""
    if value is None:
        value = os.environ.get('FLASK_DEBUG')
    return value == '1'


@app.errorhandler(HTTPException)
def handle_http_error(error):
    messages = {
        400: 'Yêu cầu không hợp lệ.', 403: 'Bạn không có quyền thực hiện thao tác này.',
        404: 'Không tìm thấy nội dung yêu cầu.',
        405: 'Phương thức yêu cầu không được hỗ trợ.', 429: 'Bạn gửi yêu cầu quá nhanh. Vui lòng thử lại sau.',
    }
    return jsonify(success=False, error=messages.get(error.code, 'Yêu cầu không thể xử lý.')), error.code


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception('Unhandled request error')
    return jsonify(success=False, error='Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.'), 500


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


def require_customer_payment(view):
    @wraps(view)
    @require_login
    @require_csrf
    def wrapped(*args, **kwargs):
        if g.user['role'] != 'CUSTOMER':
            return jsonify(success=False, error='Bạn cần dùng tài khoản khách hàng để thanh toán.'), 403
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
    address = request.remote_addr
    retry_after = _register_attempt_retry_after(address)
    if retry_after:
        return jsonify(
            success=False,
            error='Bạn gửi yêu cầu đăng ký quá nhiều lần. Vui lòng thử lại sau.',
        ), 429, {'Retry-After': str(retry_after)}
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ'), 400
    result = create_user(data.get('email'), data.get('password'),
                         data.get('full_name'), data.get('phone'))
    return jsonify(result), (201 if result['success'] else 400)


_LOGIN_FAILURE_LIMIT = 5
_LOGIN_WINDOW_SECONDS = 5 * 60
_LOGIN_RATE_MAX_ENTRIES = 8192
_login_failures = OrderedDict()
_login_failures_lock = Lock()


def _login_rate_now():
    return monotonic()


def _login_rate_keys(address, email):
    address = str(address or 'unknown')[:128]
    normalized_email = email.strip().lower() if isinstance(email, str) else ''
    if len(normalized_email) > 254:
        normalized_email = 'oversize:' + hashlib.sha256(
            normalized_email.encode('utf-8', errors='replace')
        ).hexdigest()
    return (f'ip:{address}', f'email:{normalized_email}')


def _prune_login_failures(now):
    expired = [
        key for key, (expires, _) in _login_failures.items()
        if expires <= now
    ]
    for key in expired:
        _login_failures.pop(key, None)


def _login_retry_after(address, email):
    now = _login_rate_now()
    keys = _login_rate_keys(address, email)
    return _rate_retry_after(keys, _LOGIN_FAILURE_LIMIT, now)


def _rate_retry_after(keys, limit, now=None):
    now = _login_rate_now() if now is None else now
    with _login_failures_lock:
        _prune_login_failures(now)
        blocked_expiries = [
            _login_failures[key][0]
            for key in keys
            if key in _login_failures
            and _login_failures[key][1] >= limit
        ]
        return max(0, math.ceil(max(blocked_expiries) - now)) if blocked_expiries else 0


def _record_login_failure(address, email):
    now = _login_rate_now()
    _record_rate_attempt(_login_rate_keys(address, email), _LOGIN_FAILURE_LIMIT,
                         _LOGIN_WINDOW_SECONDS, now)


def _record_rate_attempt(keys, limit, window_seconds, now):
    with _login_failures_lock:
        _prune_login_failures(now)
        for key in keys:
            expires, count = _login_failures.get(
                key, (now + window_seconds, 0)
            )
            if key not in _login_failures:
                while len(_login_failures) >= _LOGIN_RATE_MAX_ENTRIES:
                    _login_failures.popitem(last=False)
                expires = now + window_seconds
                count = 0
            _login_failures[key] = (expires, count + 1)
            _login_failures.move_to_end(key)


def _register_rate_keys(address):
    return (f'register-ip:{str(address or "unknown")[:128]}',)


def _register_attempt_retry_after(address):
    now = _login_rate_now()
    key = _register_rate_keys(address)[0]
    with _login_failures_lock:
        _prune_login_failures(now)
        expires, count = _login_failures.get(key, (now + 10 * 60, 0))
        if count >= 5:
            return max(1, math.ceil(expires - now))
        if key not in _login_failures:
            while len(_login_failures) >= _LOGIN_RATE_MAX_ENTRIES:
                _login_failures.popitem(last=False)
            expires = now + 10 * 60
            count = 0
        _login_failures[key] = (expires, count + 1)
        _login_failures.move_to_end(key)
        return 0


def _clear_login_failures(address, email):
    with _login_failures_lock:
        for key in _login_rate_keys(address, email):
            _login_failures.pop(key, None)


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ'), 400
    raw_email = data.get('email')
    email = raw_email.strip().lower() if isinstance(raw_email, str) else ''
    password = data.get('password')
    address = request.remote_addr
    retry_after = _login_retry_after(address, email)
    if retry_after:
        return jsonify(
            success=False,
            error='Bạn đăng nhập quá nhiều lần. Vui lòng thử lại sau.',
        ), 429, {'Retry-After': str(retry_after)}

    user = None
    if isinstance(password, str) and len(email) <= 254 and len(password) <= 1024:
        user = verify_user(email, password)
    if not user:
        _record_login_failure(address, email)
        return jsonify(success=False, error='Email hoặc mật khẩu không đúng'), 401
    _clear_login_failures(address, email)
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
    if not product['is_published']:
        user = current_user()
        if not user or user['role'] not in ('ADMIN', 'STAFF'):
            return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm'}), 404
    return jsonify({'success': True, 'product': product})


@app.route('/api/orders/checkout', methods=['POST'])
@require_customer_payment
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

    # Tao don, tru kho va lien ket Customer trong transaction
    from database.db import expire_pending_orders
    expire_pending_orders()
    result = sp_create_order_and_deduct_stock(
        customer_info,
        cart_items,
        payment_method,
        customer_user_id=g.user['id']
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
@require_customer_payment
def api_process_card_payment():
    """API xác thực và xử lý thanh toán qua thẻ tín dụng/ATM hoặc ví ZaloPay kèm OTP 3D-Secure"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ.'), 400
    transaction_code = data.get('transaction_code')
    payment_type = data.get('payment_type', 'CREDIT_CARD')
    card_data = data.get('card_data')
    wallet_data = data.get('wallet_data')
    otp = data.get('otp', '')

    if not isinstance(transaction_code, str) or not transaction_code.strip():
        return jsonify({'success': False, 'message': 'Thiếu mã giao dịch!'}), 400
    if not isinstance(otp, str) or any(item is not None and not isinstance(item, dict) for item in (card_data, wallet_data)):
        return jsonify(success=False, error='Dữ liệu xác thực thanh toán không hợp lệ.'), 400
    if card_data and not isinstance(card_data.get('card_number', ''), str):
        return jsonify(success=False, error='Số thẻ không hợp lệ.'), 400

    result = process_card_or_wallet_payment(
        transaction_code=transaction_code.strip(),
        payment_type=payment_type,
        card_data=card_data,
        wallet_data=wallet_data,
        otp=otp.strip(),
        customer_user_id=g.user['id'],
    )

    if result.get('success'):
        # Cập nhật lại kho cho RAG
        rag_service.sync_knowledge_base()

    return jsonify(result), _payment_http_status(result)


@app.route('/api/payment/simulate-callback', methods=['POST'])
@require_customer_payment
def api_payment_callback():
    """API Webhook mô phỏng phản hồi từ cổng thanh toán ảo"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Cần gửi JSON hợp lệ.'), 400
    transaction_code = data.get('transaction_code')
    status = data.get('status', 'SUCCESS') # SUCCESS hoặc CANCELLED

    if not isinstance(transaction_code, str) or not transaction_code.strip():
        return jsonify({'success': False, 'error': 'Thiếu mã giao dịch!'}), 400
    if status not in ('SUCCESS', 'CANCELLED', 'FAILED'):
        return jsonify(success=False, error='Trạng thái thanh toán không hợp lệ.'), 400

    amount = data.get('amount')
    checksum = data.get('checksum')
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not isinstance(checksum, str):
        return jsonify(success=False, error='Thiếu chữ ký hoặc số tiền giao dịch.'), 403
    if not verify_checksum(transaction_code.strip(), amount, checksum):
        return jsonify(success=False, error='Chữ ký giao dịch không hợp lệ.'), 403

    result = process_mock_payment_callback(transaction_code.strip(), status, customer_user_id=g.user['id'])
    # Cập nhật lại kho cho RAG
    if result['success']:
        rag_service.sync_knowledge_base()
    return jsonify(result), _payment_http_status(result)


def _payment_http_status(result):
    return {'PAYMENT_NOT_FOUND': 404, 'PAYMENT_ALREADY_PROCESSED': 409}.get(result.get('error_code'), 200)

from services.agentic_rag import AgenticRAGEngine

agentic_ai = AgenticRAGEngine()

_chat_requests = OrderedDict()
_chat_requests_lock = Lock()


def _chat_rate_allowed(address):
    now = monotonic()
    with _chat_requests_lock:
        expired_addresses = [
            address for address, (expires, _) in _chat_requests.items()
            if expires <= now
        ]
        for expired_address in expired_addresses:
            _chat_requests.pop(expired_address, None)
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
    if len(message) > 500:
        return jsonify(success=False, error='Tin nhắn tối đa 500 ký tự'), 400
    if not _chat_rate_allowed(request.remote_addr):
        return jsonify(success=False, error='Bạn gửi nhiều tin nhắn quá nhanh. Hãy thử lại sau ít phút.'), 429, {
            'Retry-After': '60',
        }

    history = data.get('conversation_history', [])
    if not isinstance(history, list):
        history = []
    history = [
        {'role': entry['role'], 'content': entry['content'].strip()[:500]}
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
    product_id = data.get('product_id')
    if type(product_id) is not int or not 0 < product_id < 2**63:
        product_id = None
    user = current_user()
    customer_user_id = user['id'] if user and user['role'] == 'CUSTOMER' else None

    def result():
        try:
            return {
                'success': True,
                'data': agentic_ai.chat_with_agent(message, history, customer_user_id, recent_ids, product_id),
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
    app.logger.info("Đang khởi chạy AURA Fashion tại http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=debug_enabled())
