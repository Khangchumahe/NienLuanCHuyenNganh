"""
Flask Application for Clothing Store
Tích hợp: RAG AI Chatbot, Virtual Payment Simulator, SQL Database (Triggers & Stored Procedures)
"""

from flask import Flask, render_template, request, jsonify
from database.db import (
    init_db, get_all_products, get_product_by_id, 
    sp_create_order_and_deduct_stock, get_db_stats
)
from services.rag_engine import rag_service
from services.payment_service import generate_checksum, process_mock_payment_callback

app = Flask(__name__)

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
    """API Đặt hàng mô phỏng Stored Procedure & trừ kho an toàn"""
    data = request.get_json() or {}
    customer_info = data.get('customer', {})
    cart_items = data.get('items', [])
    payment_method = data.get('payment_method', 'VIRTUAL_SANDBOX')

    if not cart_items:
        return jsonify({'success': False, 'error': 'Giỏ hàng đang trống!'}), 400

    result = sp_create_order_and_deduct_stock(customer_info, cart_items, payment_method)
    
    if result['success']:
        # Đồng bộ lại tồn kho mới nhất cho RAG
        rag_service.sync_knowledge_base()
        
        # Sinh checksum bảo mật cho giao dịch ảo
        checksum = generate_checksum(result['transaction_code'], result['total_amount'])
        result['checksum'] = checksum
        return jsonify(result)
    else:
        return jsonify(result), 400

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
def api_sync_rag():
    """Đồng bộ lại Knowledge Base của RAG từ SQL"""
    count = rag_service.sync_knowledge_base()
    return jsonify({'success': True, 'synced_count': count, 'message': f'Đã đồng bộ {count} tài liệu sản phẩm vào RAG!'})

@app.route('/api/admin/stats', methods=['GET'])
def api_admin_stats():
    """Lấy dữ liệu thống kê kiểm tra Trigger và Database"""
    stats = get_db_stats()
    return jsonify({'success': True, 'stats': stats})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ĐANG KHỞI CHẠY HỆ THỐNG CỬA HÀNG THỜI TRANG TÍCH HỢP RAG AI")
    print("🔗 Địa chỉ truy cập: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
