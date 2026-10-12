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

// Biến trạng thái ZaloPay Gateway & Thẻ test
let officialTestCards = [];
let officialTestWallets = [];
let zpCountdownInterval = null;
let currentPaymentType = 'CREDIT';
let pendingPaymentData = null;
let expectedOtp = '111111';

// ========================================================
// 1. KHỞI TẠO & TẢI DỮ LIỆU
// ========================================================
document.addEventListener('DOMContentLoaded', () => {
  initZaloPayBridge();
  loadProducts();
  updateCartBadge();
  setupEventListeners();
  loadOfficialTestCards();
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

  // Đặt hàng & Thanh toán
  const btnProceed = document.getElementById('btnProceedCheckout');
  if (btnProceed) {
    btnProceed.addEventListener('click', handleCheckout);
  }

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
// 5. CỔNG THANH TOÁN ZALOPAY SANDBOX GATEWAY & THẺ TÍN DỤNG MẪU
// ========================================================

/**
 * Khởi tạo ZaloPay JSBridge Adapter mô phỏng môi trường ZaloPay Client
 * Tương thích trực tiếp với file zalopay.js (ZaloPay.payOrder, ZaloPay.showLoading,...)
 */
function initZaloPayBridge() {
  if (!window.ZaloPayJSBridge) {
    window.ZaloPayJSBridge = {
      call: function(name, opt, cb) {
        console.log("⚡ [ZaloPayJSBridge.call]", name, opt);
        if (name === "payOrder") {
          window._zpPayOrderCallback = cb;
          openZaloPayGatewayModal(opt);
        } else if (name === "showLoading") {
          console.log("ZaloPay: Show Loading");
        } else if (name === "hideLoading") {
          console.log("ZaloPay: Hide Loading");
        } else if (typeof cb === 'function') {
          cb({ error: 1, errorCode: 1, errorMessage: "Success" });
        }
      }
    };
  }
  // Kích hoạt sự kiện Ready cho zalopay.js
  document.dispatchEvent(new Event("ZaloPayJSBridgeReady"));
}

/**
 * Tải danh sách thẻ tín dụng mẫu có sẵn từ backend
 */
async function loadOfficialTestCards() {
  try {
    const res = await fetch('/api/payment/test-cards');
    const data = await res.json();
    if (data.success) {
      officialTestCards = data.cards || [];
      officialTestWallets = data.wallets || [];
      renderSampleCards();
    }
  } catch (err) {
    console.error("Lỗi tải thẻ test:", err);
  }
}

/**
 * Render các thẻ tín dụng mẫu và thẻ ATM lên giao diện ZaloPay Gateway
 */
function renderSampleCards() {
  const creditContainer = document.getElementById('sampleCreditCardsList');
  const napasContainer = document.getElementById('sampleNapasCardsList');

  if (creditContainer) {
    const creditCards = officialTestCards.filter(c => c.category === 'CREDIT');
    creditContainer.innerHTML = creditCards.map(card => `
      <div class="sample-card-item" id="sampleCard_${card.id}" onclick="selectSampleCreditCard('${card.id}')">
        <div class="sample-card-top">
          <span class="sample-card-brand-tag" style="color: ${card.badge_color};">
            <i class="${card.icon}"></i> ${card.brand}
          </span>
          <span style="font-size: 10px; color: ${card.behavior === 'SUCCESS' ? '#16a34a' : '#dc2626'}; font-weight: 700;">
            ${card.behavior === 'SUCCESS' ? '✔ Thành công' : '✖ Demo Lỗi'}
          </span>
        </div>
        <div class="sample-card-num">${formatCardNumberMasked(card.card_number)}</div>
        <div class="sample-card-meta">
          <span>EXP: ${card.expiry_date}</span>
          <span>CVV: ${card.cvv}</span>
        </div>
        <div class="sample-card-badge-action">
          <i class="fa-solid fa-arrow-pointer"></i> Bấm để dùng thẻ này
        </div>
      </div>
    `).join('');
  }

  if (napasContainer) {
    const atmCards = officialTestCards.filter(c => c.category === 'ATM');
    napasContainer.innerHTML = atmCards.map(card => `
      <div class="sample-card-item" id="sampleCard_${card.id}" onclick="selectSampleNapasCard('${card.id}')">
        <div class="sample-card-top">
          <span class="sample-card-brand-tag" style="color: ${card.badge_color};">
            <i class="${card.icon}"></i> ${card.issuer}
          </span>
          <span style="font-size: 10px; color: #16a34a; font-weight: 700;">✔ Thành công</span>
        </div>
        <div class="sample-card-num">${formatCardNumberMasked(card.card_number)}</div>
        <div class="sample-card-meta">
          <span>Chủ thẻ: ${card.card_holder}</span>
          <span>Hạn: ${card.expiry_date}</span>
        </div>
        <div class="sample-card-badge-action">
          <i class="fa-solid fa-arrow-pointer"></i> Bấm để dùng thẻ này
        </div>
      </div>
    `).join('');
  }
}

function formatCardNumberMasked(num) {
  const clean = num.replace(/\s+/g, '');
  if (clean.length >= 16) {
    return `${clean.slice(0, 4)} •••• •••• ${clean.slice(-4)}`;
  }
  return num;
}

/**
 * Tự động điền dữ liệu khi người dùng chọn thẻ tín dụng mẫu
 */
function selectSampleCreditCard(cardId) {
  const card = officialTestCards.find(c => c.id === cardId);
  if (!card) return;

  document.querySelectorAll('#sampleCreditCardsList .sample-card-item').forEach(el => el.classList.remove('selected'));
  const el = document.getElementById(`sampleCard_${cardId}`);
  if (el) el.classList.add('selected');

  document.getElementById('ccNumber').value = card.card_number;
  document.getElementById('ccHolder').value = card.card_holder;
  document.getElementById('ccExpiry').value = card.expiry_date;
  document.getElementById('ccCvv').value = card.cvv;

  // Cập nhật icon thương hiệu
  const brandIconEl = document.getElementById('ccBrandIcon');
  if (brandIconEl) {
    brandIconEl.innerHTML = `<i class="${card.icon}" style="color: ${card.badge_color}"></i>`;
  }

  showToast(`Đã chọn thẻ mẫu: ${card.issuer} (${card.description})`, 'info');
}

/**
 * Tự động điền dữ liệu khi người dùng chọn thẻ ATM Napas mẫu
 */
function selectSampleNapasCard(cardId) {
  const card = officialTestCards.find(c => c.id === cardId);
  if (!card) return;

  document.querySelectorAll('#sampleNapasCardsList .sample-card-item').forEach(el => el.classList.remove('selected'));
  const el = document.getElementById(`sampleCard_${cardId}`);
  if (el) el.classList.add('selected');

  document.getElementById('napasNumber').value = card.card_number;
  document.getElementById('napasHolder').value = card.card_holder;
  document.getElementById('napasExpiry').value = card.expiry_date;

  const bankSelect = document.getElementById('napasBankSelect');
  if (bankSelect) {
    bankSelect.value = card.id.includes('vcb') ? 'VCB' : 'NCB';
  }

  showToast(`Đã chọn thẻ ATM Napas: ${card.issuer}`, 'info');
}

/**
 * Chuyển tab trong ZaloPay Gateway
 */
function switchZpTab(tabId) {
  document.querySelectorAll('.zp-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.zp-tab-content').forEach(content => content.classList.remove('active'));

  const activeContent = document.getElementById(tabId);
  if (activeContent) activeContent.classList.add('active');

  const btnIndex = tabId === 'tabCredit' ? 0 : tabId === 'tabNapas' ? 1 : 2;
  const buttons = document.querySelectorAll('.zp-tab-btn');
  if (buttons[btnIndex]) buttons[btnIndex].classList.add('active');
}

/**
 * Xử lý tiến hành đặt hàng (Checkout)
 */
async function handleCheckout() {
  const name = document.getElementById('custName').value.trim();
  const phone = document.getElementById('custPhone').value.trim();
  const address = document.getElementById('custAddress').value.trim();

  if (!name || !phone || !address) {
    showToast('Vui lòng điền đầy đủ họ tên, số điện thoại và địa chỉ!', 'warning');
    return;
  }

  if (!currentCart || currentCart.length === 0) {
    showToast('Giỏ hàng đang trống!', 'warning');
    return;
  }

  try {
    const payload = {
      customer: { name, phone, address },
      items: currentCart,
      payment_method: 'ZALOPAY_SANDBOX'
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

      // Điền thông tin vào Header của ZaloPay Gateway Modal
      document.getElementById('mockOrderCode').innerText = data.order_code;
      document.getElementById('mockAmount').innerText = `${data.total_amount.toLocaleString('vi-VN')} VNĐ`;
      
      if (data.zalopay) {
        document.getElementById('zpAppId').innerText = data.zalopay.appid;
        document.getElementById('zpAppTransId').innerText = data.zalopay.apptransid;
        document.getElementById('mockChecksum').innerText = data.zalopay.mac;
      } else {
        document.getElementById('mockChecksum').innerText = data.checksum;
      }

      // Khởi động đếm ngược 15 phút
      startZpCountdown(15);

      // Reset các view trong modal
      resetZpViews();

      // Nếu có thẻ mẫu đầu tiên, tự động chọn sẵn để tiện lợi
      if (officialTestCards.length > 0) {
        selectSampleCreditCard(officialTestCards[0].id);
      }

      // Mở modal ZaloPay Gateway
      openModal('paymentModal');

      // Gọi SDK ZaloPay.payOrder theo file zalopay.js để kích hoạt SDK chính thức
      if (window.ZaloPay && typeof window.ZaloPay.payOrder === 'function') {
        window.ZaloPay.payOrder(data.zalopay || {
          appid: 2553,
          amount: data.total_amount,
          apptransid: data.transaction_code,
          mac: data.checksum
        }, function(sdkResult) {
          console.log("⚡ [ZaloPay SDK Callback Result]:", sdkResult);
        });
      }
    } else {
      showToast(`Lỗi đặt hàng: ${data.error}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Lỗi gửi yêu cầu thanh toán!', 'error');
  }
}

/**
 * Bắt đầu luồng thanh toán thẻ (Credit Card hoặc Napas ATM) -> Chuyển sang OTP 3D-Secure
 */
function initiateCardPayment(type) {
  if (!currentPendingPayment) {
    showToast('Không tìm thấy thông tin đơn hàng hiện tại!', 'error');
    return;
  }

  currentPaymentType = type;

  if (type === 'CREDIT') {
    const num = document.getElementById('ccNumber').value.trim();
    const holder = document.getElementById('ccHolder').value.trim();
    const exp = document.getElementById('ccExpiry').value.trim();
    const cvv = document.getElementById('ccCvv').value.trim();

    if (!num || !holder || !exp || !cvv) {
      showToast('Vui lòng điền đầy đủ số thẻ, tên chủ thẻ, ngày hết hạn và mã CVV!', 'warning');
      return;
    }

    pendingPaymentData = {
      card_number: num,
      card_holder: holder,
      expiry_date: exp,
      cvv: cvv,
      brand: detectCardBrand(num)
    };

    expectedOtp = '111111';
    document.getElementById('otpCardBrandTitle').innerText = 'Verified by VISA / Mastercard ID Check';
  } else if (type === 'ATM') {
    const num = document.getElementById('napasNumber').value.trim();
    const holder = document.getElementById('napasHolder').value.trim();
    const exp = document.getElementById('napasExpiry').value.trim();
    const bank = document.getElementById('napasBankSelect').value;

    if (!num || !holder || !exp) {
      showToast('Vui lòng điền đầy đủ số thẻ ATM Napas, tên chủ thẻ và ngày phát hành!', 'warning');
      return;
    }

    pendingPaymentData = {
      card_number: num,
      card_holder: holder,
      expiry_date: exp,
      bank: bank,
      brand: 'Napas'
    };

    expectedOtp = '123456';
    document.getElementById('otpCardBrandTitle').innerText = `Xác thực Napas Smart OTP (${bank})`;
  }

  // Chuyển sang view xác thực 3D Secure OTP
  showOtpVerificationView();
}

/**
 * Thanh toán qua Ví ZaloPay QR
 */
function initiateWalletPayment() {
  if (!currentPendingPayment) return;

  currentPaymentType = 'WALLET';
  pendingPaymentData = {
    phone: '0912345678',
    name: 'ZaloPay Sandbox User'
  };
  expectedOtp = '111111';
  document.getElementById('otpCardBrandTitle').innerText = 'Xác thực Ví Điện Tử ZaloPay';

  showOtpVerificationView();
}

function detectCardBrand(num) {
  const clean = num.replace(/\s+/g, '');
  if (clean.startsWith('4')) return 'Visa';
  if (clean.startsWith('5')) return 'Mastercard';
  if (clean.startsWith('35')) return 'JCB';
  if (clean.startsWith('9704')) return 'Napas';
  return 'Credit Card';
}

function showOtpVerificationView() {
  document.getElementById('zpGatewayMainView').style.display = 'none';
  document.getElementById('zpOtpVerificationView').style.display = 'block';
  document.getElementById('zpSuccessView').style.display = 'none';

  document.getElementById('displaySampleOtp').innerText = expectedOtp;
  document.getElementById('zpOtpInput').value = '';
  document.getElementById('otpErrorMessage').style.display = 'none';
  document.getElementById('zpOtpInput').focus();
}

function fillSampleOtp() {
  document.getElementById('zpOtpInput').value = expectedOtp;
}

function cancelOtpVerification() {
  document.getElementById('zpOtpVerificationView').style.display = 'none';
  document.getElementById('zpGatewayMainView').style.display = 'block';
}

function resetZpViews() {
  document.getElementById('zpGatewayMainView').style.display = 'block';
  document.getElementById('zpOtpVerificationView').style.display = 'none';
  document.getElementById('zpSuccessView').style.display = 'none';
  switchZpTab('tabCredit');
}

/**
 * Xác nhận OTP và gửi yêu cầu thanh toán đến Backend
 */
async function submitOtpVerification() {
  if (!currentPendingPayment) return;

  const enteredOtp = document.getElementById('zpOtpInput').value.trim();
  const errorEl = document.getElementById('otpErrorMessage');

  if (!enteredOtp) {
    errorEl.innerText = 'Vui lòng nhập mã OTP để tiếp tục!';
    errorEl.style.display = 'block';
    return;
  }

  try {
    const payload = {
      transaction_code: currentPendingPayment.transaction_code,
      payment_type: currentPaymentType,
      card_data: pendingPaymentData,
      wallet_data: currentPaymentType === 'WALLET' ? pendingPaymentData : null,
      otp: enteredOtp
    };

    const res = await fetch('/api/payment/process-card', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.success) {
      // Thành công!
      errorEl.style.display = 'none';
      
      // Hiển thị view hoàn tất thành công trong modal
      document.getElementById('zpOtpVerificationView').style.display = 'none';
      document.getElementById('zpSuccessView').style.display = 'block';
      document.getElementById('zpSuccessReceipt').innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <span>Mã đơn hàng:</span> <strong>#${currentPendingPayment.order_code}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <span>Mã giao dịch ZaloPay:</span> <code>${currentPendingPayment.transaction_code}</code>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <span>Hình thức thanh toán:</span> <strong>${data.card_brand || 'ZaloPay'} (${currentPaymentType})</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <span>Số tiền thanh toán:</span> <strong style="color: #16a34a;">${currentPendingPayment.total_amount.toLocaleString('vi-VN')} VNĐ</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span>Trạng thái:</span> <span class="badge" style="background: #dcfce7; color: #16a34a; font-weight: 700;">ĐÃ THANH TOÁN (PAID)</span>
        </div>
      `;

      showToast(`🎉 Thanh toán thành công qua ZaloPay! Đơn hàng #${currentPendingPayment.order_code} đã được xác nhận (Kích hoạt Trigger trừ kho & lưu lịch sử)`, 'success');

      // Callback ZaloPay SDK nếu có
      if (window._zpPayOrderCallback) {
        window._zpPayOrderCallback({ error: 1, errorCode: 1, errorMessage: "Payment Success" });
        window._zpPayOrderCallback = null;
      }

      // Xóa giỏ hàng và cập nhật tồn kho
      currentCart = [];
      saveCart();
      loadProducts(activeCategory);

      // Đóng modal sau 2.5 giây để người dùng kịp nhìn biên lai
      setTimeout(() => {
        closeModal('paymentModal');
        currentPendingPayment = null;
        if (zpCountdownInterval) clearInterval(zpCountdownInterval);
      }, 2500);

    } else {
      // Thất bại (OTP sai, hoặc thẻ từ chối)
      errorEl.innerText = data.message || 'Giao dịch không thành công!';
      errorEl.style.display = 'block';
      showToast(data.message || 'Lỗi xác thực thanh toán!', 'error');
    }
  } catch (err) {
    console.error(err);
    errorEl.innerText = 'Lỗi kết nối tới cổng thanh toán!';
    errorEl.style.display = 'block';
  }
}

/**
 * Hủy giao dịch (Mô phỏng Rollback kho và Trigger)
 */
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
    if (zpCountdownInterval) clearInterval(zpCountdownInterval);

    if (data.success) {
      if (status === 'SUCCESS') {
        showToast(`🎉 Đã xác nhận thanh toán đơn #${currentPendingPayment.order_code}`, 'success');
        currentCart = [];
        saveCart();
      } else {
        showToast(`Giao dịch đơn hàng #${currentPendingPayment.order_code} đã bị hủy! Hệ thống đã tự động hoàn lại số lượng tồn kho (Rollback Trigger).`, 'warning');
      }
      currentPendingPayment = null;
      loadProducts(activeCategory);
    } else {
      showToast(`Lỗi xử lý giao dịch: ${data.error}`, 'error');
    }
  } catch (err) {
    console.error(err);
  }
}

/**
 * Đếm ngược thời gian hết hạn giao dịch (15 phút)
 */
function startZpCountdown(minutes) {
  if (zpCountdownInterval) clearInterval(zpCountdownInterval);
  let totalSeconds = minutes * 60;
  const countdownEl = document.getElementById('zpCountdown');

  zpCountdownInterval = setInterval(() => {
    if (totalSeconds <= 0) {
      clearInterval(zpCountdownInterval);
      if (countdownEl) countdownEl.innerText = '00:00 (Hết hạn)';
      handleMockPaymentCallback('CANCELLED');
      return;
    }

    totalSeconds--;
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    if (countdownEl) {
      countdownEl.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  }, 1000);
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
