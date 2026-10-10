/**
 * AURA FASHION CLIENT APPLICATION
 * Tích hợp: Giỏ hàng, Cổng thanh toán ảo, RAG Chatbot AI & SQL Triggers Inspector
 */

let allProducts = [];
let currentCart = JSON.parse(localStorage.getItem('aura_cart') || '[]');
let activeCategory = '';
let currentSelectedProduct = null;
let currentPendingPayment = null;
let latestRagTrace = null;

// ========================================================
// 1. KHỞI TẠO & TẢI DỮ LIỆU
// ========================================================
document.addEventListener('DOMContentLoaded', () => {
  loadProducts();
  updateCartBadge();
  setupEventListeners();
});

function setupEventListeners() {
  // Tìm kiếm
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadProducts(activeCategory, e.target.value.trim());
      }, 300);
    });
  }

  // Lọc danh mục
  const catTabs = document.querySelectorAll('.category-tabs .tab-btn');
  catTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      catTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCategory = btn.getAttribute('data-cat') || '';
      loadProducts(activeCategory, searchInput ? searchInput.value.trim() : '');
    });
  });

  // Giỏ hàng
  document.getElementById('btnOpenCart').addEventListener('click', openCartModal);

  // Nút mở kiểm tra SQL & Triggers
  document.getElementById('btnOpenSqlAudit').addEventListener('click', openSqlAuditModal);

  // Nút đồng bộ RAG
  document.getElementById('btnSyncRag').addEventListener('click', syncRagVectorDB);

  // Chatbot Launcher & Actions
  const launcher = document.getElementById('chatbotLauncher');
  const chatWindow = document.getElementById('chatbotWindow');
  const btnCloseChat = document.getElementById('btnCloseChat');
  const btnSendChat = document.getElementById('btnSendChat');
  const chatInput = document.getElementById('chatInput');

  launcher.addEventListener('click', () => {
    chatWindow.classList.toggle('open');
    if (chatWindow.classList.contains('open')) {
      chatInput.focus();
    }
  });

  btnCloseChat.addEventListener('click', () => {
    chatWindow.classList.remove('open');
  });

  btnSendChat.addEventListener('click', sendChatMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChatMessage();
  });

  // Xem luồng RAG của câu trả lời gần nhất
  document.getElementById('btnOpenRagTraceHeader').addEventListener('click', () => {
    if (!latestRagTrace) {
      showToast('Hãy đặt một câu hỏi cho Chatbot trước để xem luồng RAG phân tích!', 'warning');
      return;
    }
    renderRagTraceModal(latestRagTrace);
  });

  // Đặt hàng & Thanh toán ảo
  document.getElementById('btnProceedCheckout').addEventListener('click', handleCheckout);
  document.getElementById('btnMockSuccess').addEventListener('click', () => handleMockPaymentCallback('SUCCESS'));
  document.getElementById('btnMockCancel').addEventListener('click', () => handleMockPaymentCallback('CANCELLED'));

  // Nút Thêm vào giỏ từ Modal Chi tiết
  document.getElementById('btnAddToCartModal').addEventListener('click', handleAddToCartFromModal);
}

// ========================================================
// 2. TẢI VÀ RENDER SẢN PHẨM
// ========================================================
async function loadProducts(categoryId = '', search = '') {
  try {
    let url = '/api/products';
    const params = new URLSearchParams();
    if (categoryId) params.append('category_id', categoryId);
    if (search) params.append('search', search);
    if (params.toString()) url += `?${params.toString()}`;

    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      allProducts = data.products;
      renderProductGrid(allProducts);
      document.getElementById('productCountText').innerText = `Tìm thấy ${allProducts.length} sản phẩm`;
    }
  } catch (err) {
    console.error('Lỗi tải sản phẩm:', err);
    showToast('Không thể kết nối đến máy chủ!', 'error');
  }
}

function renderProductGrid(products) {
  const grid = document.getElementById('productGrid');
  grid.innerHTML = '';

  if (products.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px; background: white; border-radius: 12px;">
        <i class="fa-solid fa-box-open" style="font-size: 40px; color: var(--slate-400); margin-bottom: 12px;"></i>
        <h4>Không tìm thấy sản phẩm nào!</h4>
        <p style="color: var(--slate-500); font-size: 14px;">Hãy thử tìm từ khóa khác hoặc bấm nút "Tất cả sản phẩm".</p>
      </div>
    `;
    return;
  }

  products.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    // Tính phần trăm giảm giá nếu có
    const hasDiscount = p.discount_price && p.discount_price < p.price;
    const discountPercent = hasDiscount ? Math.round(((p.price - p.discount_price) / p.price) * 100) : 0;
    const displayPrice = hasDiscount ? p.discount_price : p.price;

    card.innerHTML = `
      <div class="card-image-box">
        <img src="${p.image_url}" alt="${p.name}" loading="lazy">
        <div class="card-badges">
          ${hasDiscount ? `<span class="badge badge-discount">-${discountPercent}%</span>` : ''}
          <span class="badge badge-stock">Kho: ${p.total_stock}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="product-cat">${p.category_name}</div>
        <h4 class="product-title" title="${p.name}">${p.name}</h4>
        <div class="product-material"><i class="fa-solid fa-scroll"></i> ${p.material}</div>
        
        <div class="price-row">
          <span class="current-price">${displayPrice.toLocaleString('vi-VN')} đ</span>
          ${hasDiscount ? `<span class="old-price">${p.price.toLocaleString('vi-VN')} đ</span>` : ''}
        </div>

        <div class="card-actions">
          <button class="btn-view-detail" onclick="openProductDetailModal(${p.id})">
            <i class="fa-solid fa-circle-info"></i> Xem chi tiết
          </button>
          <button class="btn-quick-add" onclick="openProductDetailModal(${p.id})" title="Chọn size & mua">
            <i class="fa-solid fa-cart-plus"></i>
          </button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

// ========================================================
// 3. CHI TIẾT SẢN PHẨM & CHỌN SIZE/MÀU
// ========================================================
async function openProductDetailModal(productId) {
  try {
    const res = await fetch(`/api/products/${productId}`);
    const data = await res.json();
    if (!data.success) return;

    currentSelectedProduct = data.product;
    const p = currentSelectedProduct;

    document.getElementById('modalProdTitle').innerText = p.name;
    document.getElementById('modalProdImg').src = p.image_url;
    document.getElementById('modalProdCat').innerText = p.category_name;
    document.getElementById('modalProdName').innerText = p.name;
    
    const hasDiscount = p.discount_price && p.discount_price < p.price;
    document.getElementById('modalProdPrice').innerText = `${(hasDiscount ? p.discount_price : p.price).toLocaleString('vi-VN')} VNĐ`;
    document.getElementById('modalProdOldPrice').innerText = hasDiscount ? `${p.price.toLocaleString('vi-VN')} VNĐ` : '';
    document.getElementById('modalProdSizeGuide').innerText = p.size_guide || 'Liên hệ nhân viên để được tư vấn chính xác.';

    // Render danh sách biến thể
    const select = document.getElementById('modalVariantSelect');
    select.innerHTML = '';
    p.variants.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.innerText = `Màu ${v.color} - Size ${v.size} (Còn ${v.stock_quantity} chiếc)`;
      select.appendChild(opt);
    });

    select.onchange = updateSelectedVariantStock;
    updateSelectedVariantStock();

    openModal('productDetailModal');
  } catch (err) {
    console.error(err);
  }
}

function updateSelectedVariantStock() {
  const select = document.getElementById('modalVariantSelect');
  const variantId = parseInt(select.value);
  if (!currentSelectedProduct) return;
  const v = currentSelectedProduct.variants.find(x => x.id === variantId);
  const infoEl = document.getElementById('modalVariantStockInfo');
  if (v) {
    if (v.stock_quantity > 0) {
      infoEl.innerHTML = `<i class="fa-solid fa-check"></i> SKU: <strong>${v.sku}</strong> | Còn <strong>${v.stock_quantity}</strong> sản phẩm trong kho.`;
      infoEl.style.color = 'var(--success)';
      document.getElementById('btnAddToCartModal').disabled = false;
    } else {
      infoEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> SKU: <strong>${v.sku}</strong> | Biến thể này đã hết hàng!`;
      infoEl.style.color = 'var(--danger)';
      document.getElementById('btnAddToCartModal').disabled = true;
    }
  }
}

function handleAddToCartFromModal() {
  if (!currentSelectedProduct) return;
  const select = document.getElementById('modalVariantSelect');
  const variantId = parseInt(select.value);
  const qty = parseInt(document.getElementById('modalQuantity').value) || 1;
  const v = currentSelectedProduct.variants.find(x => x.id === variantId);
  
  if (!v || v.stock_quantity < qty) {
    showToast('Số lượng yêu cầu vượt quá tồn kho hiện tại!', 'error');
    return;
  }

  // Thêm vào giỏ
  const existingIndex = currentCart.findIndex(item => item.variant_id === variantId);
  const price = currentSelectedProduct.discount_price || currentSelectedProduct.price;

  if (existingIndex > -1) {
    currentCart[existingIndex].quantity += qty;
  } else {
    currentCart.push({
      product_id: currentSelectedProduct.id,
      variant_id: variantId,
      product_name: currentSelectedProduct.name,
      image_url: currentSelectedProduct.image_url,
      sku: v.sku,
      color: v.color,
      size: v.size,
      price: price,
      quantity: qty
    });
  }

  saveCart();
  closeModal('productDetailModal');
  showToast(`Đã thêm ${qty} x "${currentSelectedProduct.name} (${v.size})" vào giỏ hàng!`, 'success');
}

// ========================================================
// 4. GIỎ HÀNG & THANH TOÁN
// ========================================================
function saveCart() {
  localStorage.setItem('aura_cart', JSON.stringify(currentCart));
  updateCartBadge();
}

function updateCartBadge() {
  const badge = document.getElementById('cartBadge');
  const count = currentCart.reduce((sum, item) => sum + item.quantity, 0);
  badge.innerText = count;
}

function openCartModal() {
  const listEl = document.getElementById('cartItemsList');
  listEl.innerHTML = '';

  if (currentCart.length === 0) {
    listEl.innerHTML = `
      <div style="text-align: center; padding: 32px; color: var(--slate-500);">
        <i class="fa-solid fa-basket-shopping" style="font-size: 32px; margin-bottom: 8px;"></i>
        <p>Giỏ hàng của bạn đang trống.</p>
      </div>
    `;
    document.getElementById('cartTotalPrice').innerText = '0 VNĐ';
    document.getElementById('btnProceedCheckout').disabled = true;
  } else {
    let total = 0;
    currentCart.forEach((item, index) => {
      const itemSubtotal = item.price * item.quantity;
      total += itemSubtotal;

      const itemDiv = document.createElement('div');
      itemDiv.className = 'cart-item';
      itemDiv.innerHTML = `
        <img src="${item.image_url}" alt="${item.product_name}">
        <div class="cart-item-info">
          <div class="cart-item-title">${item.product_name}</div>
          <div class="cart-item-variant">Màu: ${item.color} | Size: ${item.size} (${item.sku})</div>
          <div class="cart-item-price">${item.price.toLocaleString('vi-VN')} đ x ${item.quantity} = ${itemSubtotal.toLocaleString('vi-VN')} đ</div>
        </div>
        <div>
          <button onclick="removeCartItem(${index})" style="background: none; border: none; color: var(--danger); cursor: pointer; font-size: 16px;">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      `;
      listEl.appendChild(itemDiv);
    });

    document.getElementById('cartTotalPrice').innerText = `${total.toLocaleString('vi-VN')} VNĐ`;
    document.getElementById('btnProceedCheckout').disabled = false;
  }

  openModal('cartModal');
}

function removeCartItem(index) {
  currentCart.splice(index, 1);
  saveCart();
  openCartModal();
}

// ========================================================
// 5. CHECKOUT & CỔNG THANH TOÁN ẢO (VIRTUAL SANDBOX)
// ========================================================
async function handleCheckout() {
  const name = document.getElementById('custName').value.trim();
  const phone = document.getElementById('custPhone').value.trim();
  const address = document.getElementById('custAddress').value.trim();

  if (!name || !phone || !address) {
    showToast('Vui lòng điền đầy đủ họ tên, số điện thoại và địa chỉ!', 'warning');
    return;
  }

  try {
    const payload = {
      customer: { name, phone, address },
      items: currentCart,
      payment_method: 'VIRTUAL_SANDBOX'
    };

    const res = await fetch('/api/orders/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.success) {
      currentPendingPayment = data;
      closeModal('cartModal');

      // Mở modal thanh toán ảo
      document.getElementById('mockOrderCode').innerText = data.order_code;
      document.getElementById('mockTransCode').innerText = data.transaction_code;
      document.getElementById('mockAmount').innerText = `${data.total_amount.toLocaleString('vi-VN')} VNĐ`;
      document.getElementById('mockChecksum').innerText = data.checksum;

      openModal('paymentModal');
    } else {
      showToast(`Lỗi đặt hàng: ${data.error}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Lỗi gửi yêu cầu thanh toán!', 'error');
  }
}

async function handleMockPaymentCallback(status) {
  if (!currentPendingPayment) return;

  try {
    const res = await fetch('/api/payment/simulate-callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transaction_code: currentPendingPayment.transaction_code,
        status: status
      })
    });

    const data = await res.json();
    closeModal('paymentModal');

    if (data.success) {
      if (status === 'SUCCESS') {
        showToast(`🎉 Thanh toán thành công! Đơn hàng #${currentPendingPayment.order_code} đã được xác nhận (Kích hoạt Trigger trừ kho & lưu lịch sử)`, 'success');
        currentCart = [];
        saveCart();
      } else {
        showToast(`Giao dịch đơn hàng #${currentPendingPayment.order_code} đã bị hủy! Đã hoàn lại số lượng tồn kho.`, 'warning');
      }
      currentPendingPayment = null;
      loadProducts(activeCategory); // Cập nhật lại tồn kho hiển thị
    } else {
      showToast(`Lỗi xử lý giao dịch: ${data.error}`, 'error');
    }
  } catch (err) {
    console.error(err);
  }
}

// ========================================================
// 6. CHATBOT AI VỚI CƠ CHẾ RAG (RETRIEVAL-AUGMENTED GENERATION)
// ========================================================
function sendQuickPrompt(promptText) {
  const chatInput = document.getElementById('chatInput');
  chatInput.value = promptText;
  sendChatMessage();
}

async function sendChatMessage() {
  const chatInput = document.getElementById('chatInput');
  const message = chatInput.value.trim();
  if (!message) return;

  chatInput.value = '';
  appendChatMessage(message, 'user');

  // Hiển thị bóng chat đang suy nghĩ
  const loadingBubble = appendChatMessage('<i class="fa-solid fa-spinner fa-spin"></i> Đang truy vấn Knowledge Base & tổng hợp câu trả lời...', 'bot', true);

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message })
    });

    const resData = await res.json();
    loadingBubble.remove();

    if (resData.success) {
      const { answer, recommended_products, rag_trace } = resData.data;
      latestRagTrace = rag_trace;

      // Render câu trả lời của AI
      const botMessageEl = appendChatMessage(answer.replace(/\n/g, '<br>'), 'bot');

      // Nếu có sản phẩm gợi ý từ RAG
      if (recommended_products && recommended_products.length > 0) {
        const prodCardsBox = document.createElement('div');
        prodCardsBox.className = 'chat-product-cards';

        recommended_products.forEach(p => {
          const itemLink = document.createElement('div');
          itemLink.className = 'chat-prod-item';
          itemLink.onclick = () => openProductDetailModal(p.id);
          itemLink.style.cursor = 'pointer';

          itemLink.innerHTML = `
            <img src="${p.image_url}" alt="${p.name}">
            <div class="chat-prod-item-info">
              <div class="chat-prod-name">${p.name}</div>
              <div class="chat-prod-price">${p.price.toLocaleString('vi-VN')} đ</div>
            </div>
            <div class="chat-prod-score">Khớp: ${Math.round(p.similarity_score * 100)}%</div>
          `;
          prodCardsBox.appendChild(itemLink);
        });

        botMessageEl.appendChild(prodCardsBox);
      }
    } else {
      appendChatMessage('Xin lỗi, đã xảy ra lỗi trong quá trình xử lý câu hỏi.', 'bot');
    }
  } catch (err) {
    loadingBubble.remove();
    appendChatMessage('Không thể kết nối với dịch vụ RAG AI.', 'bot');
  }
}

function appendChatMessage(htmlContent, sender, isTemporary = false) {
  const messagesContainer = document.getElementById('chatMessages');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble bubble-${sender}`;
  bubble.innerHTML = htmlContent;
  messagesContainer.appendChild(bubble);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return bubble;
}

// ========================================================
// 7. RAG TRACE INSPECTOR MODAL (GIẢI THÍCH LUỒNG RAG)
// ========================================================
function renderRagTraceModal(trace) {
  const container = document.getElementById('ragTraceContent');
  container.innerHTML = `
    <div style="font-size: 13px; color: var(--slate-600); margin-bottom: 16px;">
      💡 <strong>Minh chứng kỹ thuật:</strong> Bảng điều khiển này phân tích toàn bộ quy trình 4 bước của kỹ thuật RAG (Retrieval-Augmented Generation) khi xử lý câu hỏi thời trang của người dùng.
    </div>

    <!-- BƯỚC 1: TRUY VẤN & TÁCH TỪ -->
    <div class="rag-step-box">
      <div class="rag-step-header">
        <span class="step-num">1</span>
        <span>Truy Vấn Của Người Dùng & Token Extraction</span>
      </div>
      <div style="font-size: 13px; margin-bottom: 6px;"><strong>Câu hỏi:</strong> "${trace.query}"</div>
      <div style="font-size: 12px; color: var(--slate-600);">
        <strong>Từ khóa bóc tách (Query Tokens):</strong> 
        ${trace.query_tokens.map(t => `<span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; margin-right: 4px;">${t}</span>`).join('')}
      </div>
    </div>

    <!-- BƯỚC 2: TRÍCH XUẤT TÀI LIỆU (RETRIEVAL) -->
    <div class="rag-step-box">
      <div class="rag-step-header">
        <span class="step-num">2</span>
        <span>Semantic Retrieval (Cosine Similarity) Từ CSDL SQL</span>
      </div>
      <div style="font-size: 13px; margin-bottom: 8px;">
        Đã so khớp với Knowledge Base và trích xuất <strong>${trace.retrieved_count}</strong> sản phẩm phù hợp nhất:
      </div>
      ${trace.retrieved_chunks.map((c, idx) => `
        <div style="background: white; border: 1px solid var(--slate-200); padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 12px;">
          <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--slate-900);">
            <span>Top ${idx + 1}: ${c.product_name}</span>
            <span style="color: var(--primary);">Điểm tương đồng: ${c.similarity_score}</span>
          </div>
          <div style="color: var(--slate-600); margin-top: 4px;">${c.snippet}</div>
        </div>
      `).join('')}
    </div>

    <!-- BƯỚC 3: PROMPT ĐƯỢC TĂNG CƯỜNG (AUGMENTED PROMPT) -->
    <div class="rag-step-box">
      <div class="rag-step-header">
        <span class="step-num">3</span>
        <span>Prompt Được Tăng Cường (Augmented Prompt Gửi Cho LLM)</span>
      </div>
      <div style="font-size: 12px; color: var(--slate-600); margin-bottom: 6px;">
        Hệ thống tự động tiêm (inject) bối cảnh sản phẩm thực tế vào prompt để tránh hallucination:
      </div>
      <div class="rag-code-block">${escapeHtml(trace.augmented_prompt)}</div>
    </div>
  `;

  openModal('ragTraceModal');
}

async function syncRagVectorDB() {
  try {
    const res = await fetch('/api/ai/sync-rag', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
    }
  } catch (err) {
    showToast('Lỗi đồng bộ dữ liệu RAG!', 'error');
  }
}

// ========================================================
// 8. SQL DATABASE, TRIGGERS & AUDIT LOG MODAL
// ========================================================
async function openSqlAuditModal() {
  try {
    const res = await fetch('/api/admin/stats');
    const data = await res.json();
    if (!data.success) return;

    const stats = data.stats;
    const body = document.getElementById('sqlAuditBody');

    body.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px;">
        <div style="background: var(--slate-100); padding: 16px; border-radius: 8px; text-align: center;">
          <div style="font-size: 24px; font-weight: 800; color: var(--primary);">${stats.total_products}</div>
          <div style="font-size: 12px; color: var(--slate-600);">Tổng Sản Phẩm (SQL)</div>
        </div>
        <div style="background: var(--slate-100); padding: 16px; border-radius: 8px; text-align: center;">
          <div style="font-size: 24px; font-weight: 800; color: var(--accent);">${stats.total_variants}</div>
          <div style="font-size: 12px; color: var(--slate-600);">Tổng Biến Thể SKU</div>
        </div>
        <div style="background: var(--slate-100); padding: 16px; border-radius: 8px; text-align: center;">
          <div style="font-size: 24px; font-weight: 800; color: var(--success);">${stats.total_orders}</div>
          <div style="font-size: 12px; color: var(--slate-600);">Tổng Đơn Hàng Đã Tạo</div>
        </div>
      </div>

      <h4 style="font-size: 14px; margin: 16px 0 8px;"><i class="fa-solid fa-bolt"></i> Nhật Ký Kích Hoạt Trigger: 'trg_track_order_status'</h4>
      <p style="font-size: 12px; color: var(--slate-500); margin-bottom: 8px;">Trigger tự động ghi nhận khi đơn hàng chuyển từ PENDING_PAYMENT sang PAID hoặc CANCELLED:</p>
      <table class="sql-log-table">
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Trạng Thái Cũ</th>
            <th>Trạng Thái Mới</th>
            <th>Ghi Chú Trigger</th>
            <th>Thời Gian</th>
          </tr>
        </thead>
        <tbody>
          ${stats.recent_status_logs.length ? stats.recent_status_logs.map(log => `
            <tr>
              <td>#${log.order_id}</td>
              <td><span style="color: var(--slate-500);">${log.old_status}</span></td>
              <td><strong style="color: ${log.new_status === 'PAID' ? 'var(--success)' : 'var(--danger)'};">${log.new_status}</strong></td>
              <td>${log.note}</td>
              <td>${log.changed_at}</td>
            </tr>
          `).join('') : '<tr><td colspan="5" style="text-align: center; color: var(--slate-400);">Chưa có đơn hàng nào thay đổi trạng thái</td></tr>'}
        </tbody>
      </table>

      <h4 style="font-size: 14px; margin: 20px 0 8px;"><i class="fa-solid fa-boxes-stacked"></i> Nhật Ký Biến Động Kho: 'trg_log_inventory_change'</h4>
      <table class="sql-log-table">
        <thead>
          <tr>
            <th>Mã Biến Thể</th>
            <th>Biến Động</th>
            <th>Tồn Kho Còn Lại</th>
            <th>Lý Do</th>
            <th>Thời Gian</th>
          </tr>
        </thead>
        <tbody>
          ${stats.recent_inventory_logs.length ? stats.recent_inventory_logs.map(log => `
            <tr>
              <td>Variant #${log.variant_id}</td>
              <td style="color: ${log.change_quantity < 0 ? 'var(--danger)' : 'var(--success)'}; font-weight: 700;">
                ${log.change_quantity > 0 ? '+' : ''}${log.change_quantity}
              </td>
              <td><strong>${log.remaining_stock}</strong></td>
              <td>${log.reason}</td>
              <td>${log.created_at}</td>
            </tr>
          `).join('') : '<tr><td colspan="5" style="text-align: center; color: var(--slate-400);">Chưa có biến động kho gần đây</td></tr>'}
        </tbody>
      </table>
    `;

    openModal('sqlAuditModal');
  } catch (err) {
    console.error(err);
  }
}

// ========================================================
// 9. TIỆN ÍCH MODAL & TOAST
// ========================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('open');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('open');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  let icon = 'fa-info-circle';
  if (type === 'success') icon = 'fa-circle-check';
  if (type === 'error') icon = 'fa-circle-exclamation';
  if (type === 'warning') icon = 'fa-triangle-exclamation';

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 4000);
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
