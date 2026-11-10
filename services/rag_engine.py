"""
RAG (Retrieval-Augmented Generation) Engine cho Cửa Hàng Thời Trang
Cơ chế hoạt động 4 bước chuẩn Kỹ thuật phần mềm:
1. Ingestion / Knowledge Base: Lập chỉ mục tài liệu sản phẩm từ CSDL SQL.
2. Retrieval: Phân tích vector / Cosine Similarity để tìm Top-K sản phẩm khớp với nhu cầu (size, cân nặng, phong cách, giá).
3. Augmentation: Đóng gói tài liệu trích xuất vào Prompt bối cảnh.
4. Generation: Sinh câu trả lời tư vấn thời trang và trả về Trace log phục vụ kiểm tra/bảo vệ đồ án.
"""

from collections import Counter
import math
import re
import unicodedata
from database.db import get_all_products
from services.agentic_tools import _detect_category_hint, _detect_gender, _expand_term_groups
from services.rag_rules import (
    HEIGHT, STOCK_QUESTION, WEIGHT, catalog_query, fold, matching_sizes, matching_variants,
    normalize_size, query_constraints, recommendation_intro, requested_fabrics, selling_price,
    stock_summary, valid_measurements,
)


STOP_WORDS = {
    "tôi", "mình", "em", "anh", "chị", "bạn", "của", "và", "với", "thì",
    "nên", "mua", "nào", "gì", "cho", "có", "không", "k", "ko", "shop",
    "ạ", "nhé", "được", "tư", "vấn", "giúp", "muốn", "cần", "tìm", "xem",
    "cao", "nặng", "kí", "kg", "cm", "m", "hơi", "rất", "quá", "lắm",
    "thế", "sao", "đi", "lại", "đang", "đã", "sẽ", "là", "ở", "này", "đó",
    "một", "vài", "cái", "chiếc", "bộ", "mẫu"
}
MIN_COSINE_MATCH_SCORE = 0.15
MIN_COSINE_CLARIFY_SCORE = 0.1

class RAGEngine:
    def __init__(self):
        self.knowledge_base = []
        self.idf = {}
        self.sync_knowledge_base()

    def sync_knowledge_base(self):
        """
        Bước 1: Ingestion & Chunking
        Đồng bộ dữ liệu sản phẩm mới nhất từ CSDL SQL vào bộ nhớ Knowledge Base của RAG.
        """
        products = get_all_products()
        chunks = []
        for p in products:
            variant_str = ", ".join([f"{v['color']} (Size {v['size']}: còn {v['stock_quantity']} cái)" for v in p['variants']])
            price = selling_price(p)
            weights = Counter()
            for field, weight in ((p['name'], 3), (p['category_name'], 2), (p['material'], 1.5),
                                  (p['style'], 1.5), (p['size_guide'], 1.2), (p['description'], 1)):
                for token in self._tokenize(field):
                    weights[token] += weight
            content = (
                f"Sản phẩm: {p['name']}.\n"
                f"Danh mục: {p['category_name']}.\n"
                f"Giá bán: {price:,.0f} VNĐ (Giá gốc: {p['price']:,.0f} VNĐ).\n"
                f"Chất liệu: {p['material']}.\n"
                f"Phong cách & Dịp mặc: {p['style']}.\n"
                f"Bảng tư vấn size (Chiều cao & Cân nặng): {p['size_guide']}.\n"
                f"Mô tả chi tiết: {p['description']}.\n"
                f"Tồn kho các biến thể hiện tại: {variant_str}."
            )
            chunks.append({
                'product_id': p['id'],
                'product_name': p['name'],
                'category': p['category_name'],
                'price': price,
                'image_url': p['image_url'],
                'material': p['material'],
                'style': p['style'],
                'size_guide': p['size_guide'],
                'variants': p['variants'],
                'content': content,
                'tokens': weights
            })
        frequency = Counter(token for chunk in chunks for token in chunk["tokens"])
        self.idf = {token: 1 + math.log((len(chunks) + 1) / (count + 1)) for token, count in frequency.items()}
        self.knowledge_base = chunks
        return len(chunks)

    @staticmethod
    def _tokenize(text):
        """Tách từ ngữ tiếng Việt chuẩn hóa NFC và lọc bỏ Stop Words"""
        normalized = unicodedata.normalize("NFC", str(text or "")).casefold()
        token_pattern = rf"(?<!\w)(?:{HEIGHT}|{WEIGHT}|size\s+[0-9a-z]+)(?!\w)|[^\W_]+"
        return [
            fold(token) for token in re.findall(token_pattern, normalized)
            if len(token) > 1 and token not in STOP_WORDS
        ]

    def _compute_cosine_similarity(self, query_tokens, doc_tokens):
        query = Counter(query_tokens)
        document = Counter(doc_tokens)
        if not query or not document:
            return 0.0
        unseen = 1 + math.log(len(self.knowledge_base) + 1)
        query_vector = {word: count * self.idf.get(word, unseen) for word, count in query.items()}
        doc_vector = {word: count * self.idf.get(word, 1) for word, count in document.items()}
        dot = sum(weight * doc_vector.get(word, 0) for word, weight in query_vector.items())
        length = math.hypot(*query_vector.values()) * math.hypot(*doc_vector.values())
        return round(dot / length, 4)

    def retrieve(self, query, top_k=3, *, in_stock_only=True):
        constraints = query_constraints(query)
        clean_query = catalog_query(query)
        query_tokens = self._tokenize(clean_query)
        groups = _expand_term_groups(clean_query)
        gender = _detect_gender(clean_query)
        category_hint = _detect_category_hint(clean_query)
        fabrics = requested_fabrics(clean_query)
        height, weight = constraints["height"], constraints["weight"]
        has_measurements = height is not None or weight is not None
        if not valid_measurements(height, weight):
            return []

        named = self.named_products(query)
        scored = []
        for doc in self.knowledge_base:
            if named and doc["product_name"] not in named:
                continue
            material = fold(doc["material"])
            if any(not re.search(r"\b" + re.escape(fabric) + r"\b", material) for fabric in fabrics):
                continue
            category = fold(doc["category"])
            name = fold(doc["product_name"])
            if (gender == "nam" and "nu" in category) or (gender == "nữ" and "nam" in category):
                continue
            if category_hint == "sơ mi" and "so mi" not in name:
                continue
            if category_hint == "áo khoác" and "khoac" not in category and not re.search(r"\b(khoac|blazer|bomber|cardigan)\b", name):
                continue
            if category_hint in ("áo", "quần", "đầm & váy"):
                prefixes = {"áo": ("ao",), "quần": ("quan",), "đầm & váy": ("dam", "vay")}
                if not category.startswith(prefixes[category_hint]):
                    continue
            budget = constraints["max_price"]
            if budget is not None and doc["price"] > budget:
                continue

            sizes = [constraints["size"]] if constraints["size"] else []
            if has_measurements:
                fits = matching_sizes(doc.get("size_guide"), height, weight)
                sizes = [size for size in fits if not sizes or size in sizes]
                if not sizes:
                    continue
            variants = matching_variants(doc["variants"], sizes, constraints["color"])
            if in_stock_only:
                variants = [variant for variant in variants if variant["stock_quantity"] > 0]
            if not variants:
                continue

            matched_tokens = list(query_tokens)
            for group in groups:
                if len(group) < 2:
                    continue
                alternatives = [self._tokenize(alias) for alias in group]
                best = max(alternatives, key=lambda words: sum(word in doc["tokens"] for word in words))
                if best and any(word in doc["tokens"] for word in best):
                    original = self._tokenize(group[0])
                    matched_tokens = [word for word in matched_tokens if word not in original] + best
            similarity = self._compute_cosine_similarity(matched_tokens, doc["tokens"])
            if similarity >= MIN_COSINE_CLARIFY_SCORE:
                score = similarity + (0.05 if has_measurements else 0) + min(len(variants), 5) * 0.005
                scored.append({
                    **doc, "similarity_score": similarity, "rank_score": score,
                    "variants": variants, "fit_sizes": list(dict.fromkeys(normalize_size(v["size"]) for v in variants)) if has_measurements else [],
                })

        scored.sort(key=lambda doc: doc["rank_score"], reverse=True)
        qualified = [doc for doc in scored if doc["similarity_score"] >= MIN_COSINE_MATCH_SCORE]
        return (qualified or scored)[:top_k]

    def named_products(self, query):
        normalized = fold(query)
        names = [
            doc["product_name"] for doc in self.knowledge_base
            if re.search(r"(?<!\w)" + re.escape(fold(doc["product_name"])) + r"(?!\w)", normalized)
        ]
        # Prefer the full title when another product has a name that is part of it.
        return {name for name in names if not any(name != other and fold(name) in fold(other) for other in names)}

    def build_augmented_prompt(self, query, retrieved_chunks):
        """
        Bước 3: Augmentation (Ghép Context vào Prompt)
        """
        context_text = "\n---\n".join([f"[Tài liệu {i+1}]:\n{c['content']}" for i, c in enumerate(retrieved_chunks)])
        
        system_prompt = (
            "BẠN LÀ TRỢ LÝ TƯ VẤN THỜI TRANG AI THÔNG MINH CỦA CỬA HÀNG.\n"
            "Nhiệm vụ của bạn là: Tư vấn kích thước (size) chuẩn xác dựa vào chiều cao và cân nặng của khách, "
            "gợi ý phong cách phối đồ phù hợp và cung cấp thông tin sản phẩm dựa ĐÚNG vào các tài liệu trong kho.\n\n"
            "QUY TẮC:\n"
            "1. Chỉ gợi ý những sản phẩm và thông tin có trong phần 'DỮ LIỆU SẢN PHẨM TRÍCH XUẤT (RETRIEVED CONTEXT)'.\n"
            "2. Luôn nói rõ lý do chọn size (ví dụ: 'Với chiều cao 1m70, nặng 64kg, quý khách vừa vặn nhất với Size M...').\n"
            "3. Giọng điệu thân thiện, chu đáo, chuyên nghiệp."
        )
        
        full_prompt = (
            f"{system_prompt}\n\n"
            f"=== DỮ LIỆU SẢN PHẨM TRÍCH XUẤT TỪ CSDL (RETRIEVED CONTEXT) ===\n"
            f"{context_text if context_text else 'Không tìm thấy sản phẩm nào khớp chính xác trong kho.'}\n\n"
            f"=== CÂU HỎI CỦA KHÁCH HÀNG ===\n"
            f"{query}\n\n"
            f"=== CÂU TRẢ LỜI CỦA BẠN ==="
        )
        return full_prompt

    def generate_response(self, query):
        """
        Bước 4: Generation & Tạo RAG Trace (Minh chứng trực quan luồng RAG)
        """
        # Trích xuất sản phẩm liên quan
        retrieved_chunks = self.retrieve(query, top_k=3)
        augmented_prompt = self.build_augmented_prompt(query, retrieved_chunks)
        
        # Nếu không có tài liệu nào đủ tương đồng
        if not retrieved_chunks:
            candidates = self.retrieve(query, in_stock_only=False)
            sold_out = bool(candidates) and all(
                item["similarity_score"] >= MIN_COSINE_MATCH_SCORE
                and all(variant["stock_quantity"] <= 0 for variant in item["variants"])
                for item in candidates
            )
            if sold_out:
                answer = "Dạ, các mẫu hoặc biến thể khớp yêu cầu của bạn hiện đã hết hàng."
            else:
                answer = "Dạ, cửa hàng chưa tìm thấy mẫu quần áo khớp với yêu cầu của bạn."
            return {
                'answer': answer,
                'recommended_products': [],
                'rag_trace': {
                    'query': query,
                    'query_tokens': self._tokenize(query),
                    'retrieved_count': 0,
                    'retrieved_chunks': [],
                    'augmented_prompt': augmented_prompt,
                    'outcome': 'OUT_OF_STOCK' if sold_out else 'NO_MATCH',
                }
            }

        if retrieved_chunks[0]['similarity_score'] < MIN_COSINE_MATCH_SCORE:
            return {
                'answer': (
                    "Mình chưa đủ chắc để gợi ý sản phẩm phù hợp. "
                    "Bạn cho mình biết rõ hơn loại trang phục hoặc dịp sử dụng nhé?"
                ),
                'recommended_products': [],
                'rag_trace': {
                    'query': query,
                    'query_tokens': self._tokenize(query),
                    'retrieved_count': 0,
                    'retrieved_chunks': [],
                    'augmented_prompt': augmented_prompt,
                    'outcome': 'CLARIFY',
                }
            }

        qualified_chunks = [
            c for c in retrieved_chunks
            if c['similarity_score'] >= MIN_COSINE_MATCH_SCORE
        ]
        stock_question = bool(STOCK_QUESTION.search(query))
        answer = recommendation_intro(len(qualified_chunks), stock=stock_question)
        recommended_products = [
            {
                'id': c['product_id'],
                'name': c['product_name'],
                'price': c['price'],
                'image_url': c['image_url'],
                'material': c['material'],
                'fit_sizes': c.get('fit_sizes', []),
                'stock_summary': stock_summary(c['variants']) if stock_question else '',
                'similarity_score': c['similarity_score']
            }
            for c in qualified_chunks
        ]

        return {
            'answer': answer,
            'recommended_products': recommended_products,
            'rag_trace': {
                'query': query,
                'outcome': 'OK',
                'query_tokens': self._tokenize(query),
                'retrieved_count': len(qualified_chunks),
                'retrieved_chunks': [
                    {
                        'product_name': c['product_name'],
                        'similarity_score': c['similarity_score'],
                        'snippet': c['content'][:180] + "..."
                    }
                    for c in qualified_chunks
                ],
                'augmented_prompt': augmented_prompt
            }
        }

# Khởi tạo singleton RAG instance
rag_service = RAGEngine()
