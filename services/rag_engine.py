"""
RAG engine cho cửa hàng thời trang.

Engine lập chỉ mục dữ liệu sản phẩm trong SQL, truy xuất bằng TF-IDF cosine
được tăng cường bởi các bộ lọc số đo có cấu trúc, rồi tạo phản hồi cục bộ.
Prompt được tạo để kiểm tra/tích hợp LLM về sau; hiện chưa có lời gọi LLM.
"""

import math
import re
import unicodedata

from database.db import get_all_products


class RAGEngine:
    FIELD_WEIGHTS = {
        'name': 3.0,
        'category': 2.0,
        'material': 1.5,
        'style': 1.5,
        'size_guide': 1.2,
        'description': 1.0,
        'variants': 0.8,
    }

    STOP_WORDS = {
        'ban', 'bao', 'bieu', 'cai', 'cho', 'co', 'cua', 'gi', 'giup',
        'hang', 'hay', 'la', 'minh', 'muon', 'nao', 'nay', 'nhe', 'shop',
        'toi', 'tim', 'va', 'voi', 'xin', 'y',
    }

    def __init__(self):
        self.knowledge_base = []
        self.document_frequency = {}
        self.sync_knowledge_base()

    @staticmethod
    def _normalize(text):
        text = str(text or '').lower().replace('đ', 'd')
        return ''.join(
            character
            for character in unicodedata.normalize('NFD', text)
            if unicodedata.category(character) != 'Mn'
        )

    def _tokenize(self, text):
        """Chuẩn hóa dấu tiếng Việt và giữ nguyên từ có số đo như 1m70, 65kg."""
        normalized = self._normalize(text)
        tokens = re.findall(
            r'\d+m\d{2}|[a-z]+\d+|\d+(?:[.,]\d+)?(?:kg|cm|m)?|[a-z]+',
            normalized,
        )
        return [
            token for token in tokens
            if len(token) > 1 and token not in self.STOP_WORDS
        ]

    @staticmethod
    def _format_variants(variants):
        return ', '.join(
            f"{variant['color']} (Size {variant['size']}: còn "
            f"{variant['stock_quantity']} cái)"
            for variant in variants
        ) or 'Chưa có thông tin biến thể.'

    def sync_knowledge_base(self):
        """Đọc lại sản phẩm đang hiển thị và lập chỉ mục trong bộ nhớ."""
        products = get_all_products()
        documents = []

        for product in products:
            variants = product.get('variants') or []
            size_guide = product.get('size_guide') or ''
            variant_text = self._format_variants(variants)
            content = (
                f"Sản phẩm: {product.get('name') or ''}.\n"
                f"Danh mục: {product.get('category_name') or ''}.\n"
                f"Giá bán: {(product.get('discount_price') or product.get('price') or 0):,.0f} VNĐ "
                f"(Giá gốc: {(product.get('price') or 0):,.0f} VNĐ).\n"
                f"Chất liệu: {product.get('material') or 'Chưa cập nhật'}.\n"
                f"Phong cách & Dịp mặc: {product.get('style') or 'Chưa cập nhật'}.\n"
                f"Bảng tư vấn size (Chiều cao & Cân nặng): "
                f"{size_guide or 'Chưa cập nhật'}.\n"
                f"Mô tả chi tiết: {product.get('description') or 'Chưa cập nhật'}.\n"
                f"Tồn kho các biến thể hiện tại: {variant_text}."
            )
            fields = {
                'name': product.get('name'),
                'category': product.get('category_name'),
                'material': product.get('material'),
                'style': product.get('style'),
                'size_guide': size_guide,
                'description': product.get('description'),
                'variants': variant_text,
            }
            term_weights = {}
            for field, value in fields.items():
                for token in self._tokenize(value):
                    term_weights[token] = (
                        term_weights.get(token, 0.0) + self.FIELD_WEIGHTS[field]
                    )

            documents.append({
                'product_id': product['id'],
                'product_name': product.get('name') or 'Sản phẩm',
                'category': product.get('category_name') or '',
                'price': product.get('discount_price') or product.get('price') or 0,
                'image_url': product.get('image_url'),
                'material': product.get('material') or '',
                'style': product.get('style') or '',
                'size_guide': size_guide,
                'variants': variants,
                'total_stock': product.get(
                    'total_stock',
                    sum(int(variant.get('stock_quantity') or 0) for variant in variants),
                ),
                'content': content,
                'term_weights': term_weights,
                'tokens': self._tokenize(content),
                'size_ranges': self._parse_size_ranges(size_guide),
            })

        self.knowledge_base = documents
        self.document_frequency = {}
        for document in documents:
            for token in document['term_weights']:
                self.document_frequency[token] = (
                    self.document_frequency.get(token, 0) + 1
                )
        return len(documents)

    @classmethod
    def _parse_size_ranges(cls, size_guide):
        """Đọc các khoảng size phổ biến trong size guide dạng văn bản của cửa hàng."""
        normalized = cls._normalize(size_guide)
        ranges = []
        pattern = re.compile(
            r'\bsize\s*(xxl|xxxl|xl|xs|s|m|l)\b[^:|]*:\s*([^|]*)',
            re.IGNORECASE,
        )
        for match in pattern.finditer(normalized):
            section = match.group(2)
            heights = [
                cls._height_to_cm(int(m.group(1)), int(m.group(2)))
                for m in re.finditer(r'(?<!\d)(\d{1,3})m(\d{2})(?!\d)', section)
            ]
            heights.extend(
                int(m.group(1))
                for m in re.finditer(r'(?<!\d)(\d{3})\s*cm\b', section)
            )
            weights = [
                (int(m.group(1)), int(m.group(2)))
                for m in re.finditer(
                    r'(\d{2,3})\s*[-–]\s*(\d{2,3})\s*kg\b', section
                )
            ]
            ranges.append({
                'size': match.group(1).upper(),
                'height_min_cm': min(heights) if heights else None,
                'height_max_cm': max(heights) if heights else None,
                'weight_min_kg': min((item[0] for item in weights), default=None),
                'weight_max_kg': max((item[1] for item in weights), default=None),
            })
        return ranges

    @staticmethod
    def _height_to_cm(meters, centimeters):
        return meters * 100 + centimeters

    @classmethod
    def _extract_measurements(cls, query):
        normalized = cls._normalize(query)
        height_cm = None
        height_match = re.search(r'(?<!\d)(\d{1,3})m(\d{2})(?!\d)', normalized)
        if height_match:
            height_cm = cls._height_to_cm(
                int(height_match.group(1)), int(height_match.group(2))
            )
        else:
            height_match = re.search(r'(?<!\d)(\d{3})\s*cm\b', normalized)
            if height_match:
                height_cm = int(height_match.group(1))

        weight_match = re.search(r'(?<!\d)(\d{2,3}(?:[.,]\d+)?)\s*kg\b', normalized)
        weight_kg = (
            float(weight_match.group(1).replace(',', '.'))
            if weight_match else None
        )
        return {'height_cm': height_cm, 'weight_kg': weight_kg}

    @staticmethod
    def _measurement_matches(size_range, measurements):
        height = measurements['height_cm']
        weight = measurements['weight_kg']
        has_height_range = size_range['height_min_cm'] is not None
        has_weight_range = size_range['weight_min_kg'] is not None
        if height is not None and has_height_range:
            if not size_range['height_min_cm'] <= height <= size_range['height_max_cm']:
                return False
        if weight is not None and has_weight_range:
            if not size_range['weight_min_kg'] <= weight <= size_range['weight_max_kg']:
                return False
        return (
            (height is None or has_height_range)
            and (weight is None or has_weight_range)
            and (has_height_range or has_weight_range)
        )

    def _idf(self, token):
        count = len(self.knowledge_base)
        frequency = self.document_frequency.get(token, 0)
        return math.log(1 + (count - frequency + 0.5) / (frequency + 0.5)) + 1

    def _compute_cosine_similarity(self, query_tokens, document):
        """Tính cosine trên vector TF-IDF, có trọng số trường cho từng sản phẩm."""
        query_weights = {}
        for token in query_tokens:
            query_weights[token] = query_weights.get(token, 0.0) + self._idf(token)
        document_weights = {
            token: weight * self._idf(token)
            for token, weight in document['term_weights'].items()
        }
        dot_product = sum(
            weight * document_weights.get(token, 0.0)
            for token, weight in query_weights.items()
        )
        query_norm = math.sqrt(sum(weight ** 2 for weight in query_weights.values()))
        document_norm = math.sqrt(sum(weight ** 2 for weight in document_weights.values()))
        if not query_norm or not document_norm:
            return 0.0
        return dot_product / (query_norm * document_norm)

    def _available_sizes(self, document):
        return sorted({
            str(variant.get('size', '')).upper()
            for variant in document['variants']
            if int(variant.get('stock_quantity') or 0) > 0
        })

    def retrieve(self, query, top_k=3):
        """Xếp hạng sản phẩm bằng TF-IDF và tăng điểm khi size phù hợp còn hàng."""
        query_tokens = self._tokenize(query)
        measurements = self._extract_measurements(query)
        has_measurements = any(value is not None for value in measurements.values())
        scored_docs = []

        for document in self.knowledge_base:
            if int(document['total_stock'] or 0) <= 0:
                continue

            lexical_score = self._compute_cosine_similarity(query_tokens, document)
            matching_sizes = [
                size_range for size_range in document['size_ranges']
                if self._measurement_matches(size_range, measurements)
            ] if has_measurements else []
            available_sizes = self._available_sizes(document)
            available_matches = [
                size_range for size_range in matching_sizes
                if size_range['size'] in available_sizes
            ]

            # Số đo có thể khớp khoảng trong bảng size dù không trùng các đầu mút.
            score = lexical_score
            if available_matches:
                score += 0.25
            elif matching_sizes:
                score += 0.08

            if score < 0.08:
                continue
            scored_docs.append({
                **{
                    key: document[key]
                    for key in (
                        'product_id', 'product_name', 'category', 'price',
                        'image_url', 'material', 'style', 'size_guide',
                        'variants', 'content',
                    )
                },
                'similarity_score': round(min(score, 1.0), 4),
                'lexical_score': round(lexical_score, 4),
                'matching_sizes': matching_sizes,
                'recommended_size': (
                    available_matches[0]['size'] if available_matches else None
                ),
                'available_sizes': available_sizes,
            })

        scored_docs.sort(
            key=lambda item: (
                item['similarity_score'],
                item['lexical_score'],
                item['product_id'],
            ),
            reverse=True,
        )
        return scored_docs[:max(0, top_k)]

    def build_augmented_prompt(self, query, retrieved_chunks):
        """Tạo prompt ngữ cảnh để kiểm tra hoặc dùng khi tích hợp LLM."""
        context_text = '\n---\n'.join(
            f"[Tài liệu {index + 1}]:\n{chunk['content']}"
            for index, chunk in enumerate(retrieved_chunks)
        )
        return (
            "BẠN LÀ TRỢ LÝ TƯ VẤN THỜI TRANG CỦA CỬA HÀNG.\n"
            "Chỉ sử dụng dữ liệu trong ngữ cảnh; không suy đoán size, giá hoặc tồn kho. "
            "Nếu dữ liệu không đủ, hãy nêu rõ điều đó.\n\n"
            "=== DỮ LIỆU SẢN PHẨM TRÍCH XUẤT ===\n"
            f"{context_text or 'Không tìm thấy sản phẩm phù hợp còn hàng.'}\n\n"
            f"=== CÂU HỎI KHÁCH HÀNG ===\n{query}\n\n"
            "=== CÂU TRẢ LỜI ==="
        )

    @staticmethod
    def _format_stock(variants):
        in_stock = [
            f"{variant['color']} - size {variant['size']} "
            f"(còn {variant['stock_quantity']})"
            for variant in variants
            if int(variant.get('stock_quantity') or 0) > 0
        ]
        return ', '.join(in_stock)

    def _build_answer(self, query, retrieved_chunks):
        if not retrieved_chunks:
            return (
                "Mình chưa tìm thấy sản phẩm còn hàng phù hợp với thông tin bạn đưa ra. "
                "Bạn thử cho biết loại trang phục, phong cách hoặc khoảng giá mong muốn nhé."
            )

        top_product = retrieved_chunks[0]
        answer = (
            f"Dạ, mình tìm được **{top_product['product_name']}** "
            f"({top_product['category']}) với giá "
            f"**{top_product['price']:,.0f} VNĐ**."
        )
        if top_product['material']:
            answer += f" Chất liệu: {top_product['material'].rstrip(' .')}."
        if top_product['style']:
            answer += f" Phong cách/dịp mặc: {top_product['style'].rstrip(' .')}."

        if top_product['recommended_size']:
            answer += (
                f" Theo bảng size và số đo bạn cung cấp, size "
                f"**{top_product['recommended_size']}** nằm trong khoảng phù hợp "
                "và hiện có hàng."
            )
        elif top_product['matching_sizes']:
            matching = ', '.join(
                size_range['size'] for size_range in top_product['matching_sizes']
            )
            answer += (
                f" Số đo nằm trong khoảng size {matching} theo bảng hướng dẫn, "
                "nhưng các size đó hiện không có hàng; vui lòng kiểm tra lại với shop."
            )

        stock = self._format_stock(top_product['variants'])
        if stock:
            answer += f" Tồn kho hiện ghi nhận: {stock}."
        else:
            answer += " Chưa có biến thể còn hàng được ghi nhận."
        return answer

    def generate_response(self, query):
        """Tạo phản hồi có căn cứ từ truy xuất; không gọi mô hình ngôn ngữ bên ngoài."""
        retrieved_chunks = self.retrieve(query, top_k=3)
        augmented_prompt = self.build_augmented_prompt(query, retrieved_chunks)
        measurements = self._extract_measurements(query)
        answer = self._build_answer(query, retrieved_chunks)
        recommended_products = [
            {
                'id': chunk['product_id'],
                'name': chunk['product_name'],
                'price': chunk['price'],
                'image_url': chunk['image_url'],
                'similarity_score': chunk['similarity_score'],
                'recommended_size': chunk['recommended_size'],
                'available_sizes': chunk['available_sizes'],
            }
            for chunk in retrieved_chunks
        ]

        return {
            'answer': answer,
            'recommended_products': recommended_products,
            'rag_trace': {
                'query': query,
                'query_tokens': self._tokenize(query),
                'retrieval_method': 'TF-IDF cosine + so khớp số đo và tồn kho',
                'measurements': measurements,
                'retrieved_count': len(retrieved_chunks),
                'retrieved_chunks': [
                    {
                        'product_name': chunk['product_name'],
                        'similarity_score': chunk['similarity_score'],
                        'lexical_score': chunk['lexical_score'],
                        'recommended_size': chunk['recommended_size'],
                        'available_sizes': chunk['available_sizes'],
                        'snippet': chunk['content'][:220] + '...',
                    }
                    for chunk in retrieved_chunks
                ],
                'augmented_prompt': augmented_prompt,
                'response_mode': 'deterministic_local_template',
            },
        }


rag_service = RAGEngine()
