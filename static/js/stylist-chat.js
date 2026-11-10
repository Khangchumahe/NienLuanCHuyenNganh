(() => {
'use strict';

const launcher = document.getElementById('chatbotLauncher');
if (!launcher) return;
const panel = document.getElementById('chatbotWindow');
const input = document.getElementById('chatInput');
const messages = document.getElementById('chatMessages');
const traceModal = document.getElementById('ragTraceModal');
const traceButton = document.getElementById('btnOpenRagTraceHeader');
const productId = Number(document.body.dataset.productId) || null;
const key = 'aura.stylist.chat.v1';
const state = { turns: [], recentIds: [], trace: null, open: false };
let pending = false;

try {
  const saved = JSON.parse(sessionStorage.getItem(key));
  if (saved && Array.isArray(saved.turns)) {
    state.turns = saved.turns.filter(turn => turn && ['user', 'assistant'].includes(turn.role) &&
      typeof turn.content === 'string').slice(-24);
    state.recentIds = Array.isArray(saved.recentIds) ? saved.recentIds.slice(0, 3) : [];
    state.trace = saved.trace;
    state.open = saved.open === true;
  }
} catch (error) {
  // The chat remains usable when browser storage is unavailable.
}

function save() {
  try {
    sessionStorage.setItem(key, JSON.stringify({
      ...state,
      turns: state.turns.filter(turn => !turn.private),
      trace: state.trace?.intent === 'ORDER_LOOKUP' ? null : state.trace
    }));
  } catch (error) {
    // Keep the in-memory conversation if storage is blocked or full.
  }
}

function setOpen(open, focus = false) {
  state.open = open;
  panel.classList.toggle('open', open);
  launcher.setAttribute('aria-expanded', String(open));
  if (open && focus) input.focus();
  save();
}

function renderTurn(turn) {
  const botMessage = appendChatMessage(turn.content, turn.role === 'user' ? 'user' : 'bot', turn.time);
  if (turn.products?.length) renderCards(botMessage, turn.products);
  return botMessage;
}

function record(turn) {
  state.turns.push(turn);
  state.turns = state.turns.slice(-24);
  save();
  return renderTurn(turn);
}

async function send() {
  const message = input.value.trim();
  if (!message || pending) return;
  pending = true;
  input.value = '';
  const conversation = state.turns.slice(-12).map(({role, content}) => ({role, content}));
  const safeMessage = /(?:\d[ -]?){13,19}/.test(message) && /(?:thẻ|card)/i.test(message)
    ? '[Đã ẩn thông tin thẻ]' : message;
  record({ role: 'user', content: safeMessage, time: Date.now(), private: /\bORD-[A-Z0-9-]+\b/i.test(message) });
  const loading = appendChatMessage('Đang gửi câu hỏi…', 'bot');
  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/x-ndjson' },
      body: JSON.stringify({ message, conversation_history: conversation,
        recent_product_ids: state.recentIds, product_id: productId })
    });
    const result = await readChatResult(response, loading);
    if (!result.success) throw new Error(result.error || 'Chưa thể kiểm tra dữ liệu cửa hàng.');
    const { answer, recommended_products: products, rag_trace: trace } = result.data;
    state.trace = trace;
    if (products?.length) {
      state.recentIds = products.slice(0, 3).map(product => product.id);
    } else if (['PRODUCT_SEARCH', 'OUTFIT'].includes(trace?.intent)) {
      state.recentIds = [];
    }
    const bubble = record({
      role: 'assistant', content: answer, products, time: Date.now(), private: trace?.intent === 'ORDER_LOOKUP'
    });
    if (products?.length) messages.scrollTop = bubble.parentElement.offsetTop;
  } catch (error) {
    appendChatMessage(error.message || 'Không thể kết nối với dịch vụ tư vấn.', 'bot');
  } finally {
    loading.parentElement.remove();
    pending = false;
  }
}

launcher.addEventListener('click', () => setOpen(!state.open, true));
document.getElementById('btnCloseChat').addEventListener('click', () => setOpen(false));
document.getElementById('btnSendChat').addEventListener('click', send);
input.addEventListener('keydown', event => { if (event.key === 'Enter') send(); });
panel.querySelectorAll('[data-chat-prompt]').forEach(chip => {
  chip.addEventListener('click', () => { input.value = chip.dataset.chatPrompt; send(); });
});
traceButton.addEventListener('click', () => {
  if (state.trace) renderRagTraceModal(state.trace);
  else if (typeof window.showToast === 'function') window.showToast('Hãy đặt câu hỏi trước để xem kết quả RAG.', 'warning');
});
traceModal.querySelector('.btn-close-modal').addEventListener('click', () => traceModal.classList.remove('open'));

state.turns.forEach(renderTurn);
setOpen(state.open);
if (new URLSearchParams(location.search).get('choose') === '1') {
  setOpen(false);
  document.getElementById('productVariant')?.focus();
}

async function readChatResult(response, loadingBubble) {
  if (!response.ok || !response.headers.get('Content-Type')?.includes('application/x-ndjson')) {
    return response.json();
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let pending = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) throw new Error('Luồng chat kết thúc trước khi có câu trả lời');
    pending += decoder.decode(value, { stream: true });
    const lines = pending.split('\n');
    pending = lines.pop();
    for (const line of lines) {
      const event = JSON.parse(line);
      if (event.event === 'retrieving') loadingBubble.textContent = 'Aura đang kiểm tra dữ liệu cửa hàng…';
      if (event.event === 'answer') return event;
    }
  }
}

function appendChatMessage(content, sender, timestamp = Date.now()) {
  const messagesContainer = document.getElementById('chatMessages');
  const row = document.createElement('div');
  row.className = 'chat-message chat-message-' + sender;
  const meta = document.createElement('div');
  meta.className = 'chat-message-meta';
  const time = new Date(timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  meta.textContent = (sender === 'user' ? 'Bạn' : 'AURA Stylist') + ' · ' + time;
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble bubble-' + sender;
  bubble.textContent = content;
  row.append(meta, bubble);
  messagesContainer.appendChild(row);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return bubble;
}

function renderCards(botMessage, recommended_products) {
  const box = document.createElement('div');
  box.className = 'chat-product-cards';
  for (const product of recommended_products) {
    const card = document.createElement('article');
    card.className = 'chat-prod-item';
    const media = document.createElement('div');
    media.className = 'chat-prod-media';
    media.textContent = 'AURA';
    const img = document.createElement('img');
    const imagePath = typeof product.image_url === 'string' ? product.image_url : '';
    if (/^(\/(?!\/)[^\\]|https?:\/\/)/i.test(imagePath)) {
      img.alt = '';
      img.addEventListener('error', () => img.remove(), { once: true });
      img.src = imagePath;
      media.appendChild(img);
    }
    const info = document.createElement('div');
    info.className = 'chat-prod-item-info';
    const name = document.createElement('div');
    name.className = 'chat-prod-name';
    name.textContent = product.name;
    name.title = product.name;
    const price = document.createElement('div');
    price.className = 'chat-prod-price';
    price.textContent = Number(product.price).toLocaleString('vi-VN') + ' đ';
    info.append(name, price);
    const note = document.createElement('p');
    note.className = 'chat-prod-note';
    if (product.fit_sizes?.length) {
      note.textContent = 'Size phù hợp: ' + product.fit_sizes.join(', ');
    } else if (product.material && !product.stock_summary) {
      note.textContent = product.material;
    }
    if (note.textContent) info.appendChild(note);
    const actions = document.createElement('div');
    actions.className = 'chat-prod-actions';
    const view = document.createElement('button');
    view.type = 'button';
    view.textContent = 'Xem sản phẩm';
    view.addEventListener('click', () => location.assign('/products/' + product.id));
    const add = document.createElement('button');
    add.type = 'button';
    add.className = 'chat-prod-add';
    add.textContent = 'Thêm vào giỏ';
    add.addEventListener('click', () => {
      if (typeof window.showProductDetailModal === 'function') {
        window.showProductDetailModal(product.id, { chooseVariant: true });
      } else if (document.body.hasAttribute('data-cart-on-storefront')) {
        location.assign('/?product=' + product.id);
      } else if (product.id === productId && document.getElementById('productVariant')) {
        setOpen(false);
        document.getElementById('productVariant').focus();
      } else {
        location.assign('/products/' + product.id + '?choose=1');
      }
    });
    actions.append(view, add);
    card.append(media, info);
    if (product.stock_summary) {
      const stock = document.createElement('p');
      stock.className = 'chat-prod-stock';
      stock.textContent = product.stock_summary;
      card.appendChild(stock);
    }
    card.appendChild(actions);
    box.appendChild(card);
  }
  botMessage.appendChild(box);
}

function renderRagTraceModal(trace) {
  const container = document.getElementById('ragTraceContent');
  const intents = {
    OUT_OF_SCOPE: 'Ngoài phạm vi cửa hàng', GREETING: 'Chào hỏi', CLARIFY: 'Cần làm rõ',
    PRODUCT_SEARCH: 'Tìm sản phẩm', STOCK_CHECK: 'Kiểm tra tồn kho', SIZE_ADVICE: 'Tư vấn size',
    OUTFIT: 'Phối đồ', STORE_POLICY: 'Chính sách cửa hàng', ORDER_LOOKUP: 'Tra cứu đơn hàng'
  };
  const outcomes = {
    OK: 'Khớp yêu cầu', IN_STOCK: 'Còn hàng', OUT_OF_STOCK: 'Hết hàng',
    MEASUREMENT_CONFLICT: 'Chiều cao và cân nặng khớp hai size khác nhau',
    NO_MATCH: 'Chưa có mẫu phù hợp', NO_VARIANT: 'Chưa có màu hoặc size này', CLARIFY: 'Cần làm rõ'
  };
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
      <div style="font-size: 13px; margin-bottom: 6px;"><strong>Câu hỏi:</strong> "${escapeHtml(trace.query)}"</div>
      <div style="font-size: 13px; margin-bottom: 6px;">
        <strong>Phân loại:</strong> ${escapeHtml(intents[trace.intent] ?? '—')}
        · <strong>Kết quả:</strong> ${escapeHtml(outcomes[trace.outcome] ?? '—')}
      </div>
      <div style="font-size: 12px; color: var(--slate-600);">
        <strong>Từ khóa bóc tách (Query Tokens):</strong>
        ${trace.query_tokens.map(t => `<span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; margin-right: 4px;">${escapeHtml(t)}</span>`).join('')}
      </div>
    </div>

    <!-- BƯỚC 2: TRÍCH XUẤT TÀI LIỆU (RETRIEVAL) -->
    <div class="rag-step-box">
      <div class="rag-step-header">
        <span class="step-num">2</span>
        <span>Truy xuất từ CSDL · ${escapeHtml(trace.mode || "local")}</span>
      </div>
      <div style="font-size: 13px; margin-bottom: 8px;">
        Đã so khớp với Knowledge Base và trích xuất <strong>${escapeHtml(trace.retrieved_count)}</strong> sản phẩm phù hợp nhất:
      </div>
      ${trace.retrieved_chunks.map((c, idx) => `
        <div style="background: white; border: 1px solid var(--slate-200); padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 12px;">
          <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--slate-900);">
            <span>Top ${idx + 1}: ${escapeHtml(c.product_name)}</span>
            <span style="color: var(--primary);">Điểm tương đồng: ${escapeHtml(c.similarity_score ?? "—")}</span>
          </div>
          <div style="color: var(--slate-600); margin-top: 4px;">${escapeHtml(c.snippet)}</div>
        </div>
      `).join('')}
    </div>

    <!-- BƯỚC 3: PROMPT ĐƯỢC TĂNG CƯỜNG (AUGMENTED PROMPT) -->
    <div class="rag-step-box">
      <div class="rag-step-header">
        <span class="step-num">3</span>
        <span>Ngữ cảnh dùng để trả lời</span>
      </div>
      <div style="font-size: 12px; color: var(--slate-600); margin-bottom: 6px;">
        Dữ liệu sản phẩm hoặc kết quả công cụ truy xuất được trong lượt này.
      </div>
      <div class="rag-code-block">${escapeHtml(trace.augmented_prompt)}</div>
    </div>
  `;

  traceModal.classList.add('open');
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
})();
