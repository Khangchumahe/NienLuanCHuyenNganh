"""
Các hàm nghiệp vụ (Python Tools) kết nối CSDL SQLite store.db cho Agentic RAG.
Có Type Annotations + docstring rõ ràng để Google GenAI SDK tự sinh Function Schema.

Nâng cấp so với bản cũ:
- db_search_products: tách từ khóa, mở rộng từ đồng nghĩa (thể thao -> năng động...),
  chấm độ phủ từ khóa, áp ngưỡng gợi ý / hỏi làm rõ / không tìm thấy.
- db_recommend_size (MỚI): gợi ý size từ chiều cao/cân nặng, đối chiếu tồn kho thật.
- db_suggest_outfit (MỚI): gợi ý món phối cùng (cross-sell) cùng phong cách.
- Tất cả tool trả về dict (ổn định hơn với Function Response của Gemini).
"""
from collections import defaultdict
import re
import unicodedata
from typing import Dict, Any, List, Optional
from database.db import get_db_connection
from services.rag_rules import (
    available_variants, fold, matching_sizes, matching_variants, normalize_size, requested_fabrics, valid_measurements,
)

# ---------------------------------------------------------------- tiện ích
SYNONYMS = {
    "thể thao": ["thể thao", "sport", "năng động", "thoáng", "dry", "thun"],
    "công sở": ["công sở", "lịch sự", "sơ mi", "thanh lịch", "tây"],
    "đi chơi": ["đi chơi", "casual", "basic", "dạo phố", "streetwear"],
    "đi làm": ["công sở", "lịch sự", "sơ mi", "thanh lịch"],
    "dự tiệc": ["dự tiệc", "tiệc", "sang trọng", "đầm", "dạ hội"],
    "đi biển": ["đi biển", "linen", "đũi", "mát", "thoáng"],
    "mùa đông": ["khoác", "len", "nỉ", "dạ", "ấm"],
    "mùa mưa": ["chống nước", "khoác", "gió"],
    "thoáng mát": ["thoáng mát", "thoáng", "mỏng nhẹ", "thoáng khí"],
}

STOP_WORDS = {
    "tôi", "mình", "em", "anh", "chị", "bạn", "của", "và", "với", "thì",
    "nên", "mua", "nào", "gì", "cho", "có", "không", "k", "ko", "shop",
    "ạ", "nhé", "được", "tư", "vấn", "giúp", "muốn", "cần", "tìm", "xem",
    "cao", "nặng", "kí", "kg", "cm", "m", "hơi", "rất", "quá", "lắm",
    "thế", "sao", "đi", "lại", "đang", "đã", "sẽ", "là", "ở", "này", "đó",
    "một", "vài", "cái", "chiếc", "bộ", "mẫu"
}

PRODUCT_MATCH_THRESHOLD = 0.6
PRODUCT_CLARIFY_THRESHOLD = 0.4


def _norm(text: Any) -> str:
    return unicodedata.normalize("NFC", str(text or "")).lower().strip()


def _detect_gender(text: str) -> Optional[str]:
    txt = _norm(text)
    has_female = re.search(r"\b(?:nữ|nu|gái|vợ|mẹ|cô ấy|đầm|váy)\b", txt)
    has_male = re.search(r"\b(?:nam|trai|chồng|bố|anh ấy|ông)\b", txt)
    if has_male and not has_female:
        return "nam"
    if has_female and not has_male:
        return "nữ"
    return None


def _detect_category_hint(text: str) -> Optional[str]:
    txt = fold(text)
    original = _norm(text)
    if re.search(r"\bso mi\b", txt):
        return "sơ mi"
    if re.search(r"\b(?:khoac|blazer|bomber|cardigan)\b", txt):
        return "áo khoác"
    if re.search(r"\b(?:áo|ao|polo|thun)\b", original):
        return "áo"
    if re.search(r"\b(?:quần|quan|jeans?|kaki|jogger|short)\b", original):
        return "quần"
    if re.search(r"\b(?:đầm|dam|váy|vay)\b", original):
        return "đầm & váy"
    return None


def _connect():
    conn = get_db_connection()
    # SQLite LIKE folds ASCII only. Register the catalog normalizers.
    conn.create_function("fold_vn", 1, fold)
    conn.create_function("normalize_size", 1, normalize_size)
    return conn


def _expand_term_groups(keyword: str) -> List[List[str]]:
    kw = _norm(keyword)
    groups: List[List[str]] = []
    for key, vals in SYNONYMS.items():
        if key in kw:
            groups.append(list(dict.fromkeys(_norm(v) for v in vals)))
            kw = kw.replace(key, " ")

    # Synonyms are alternatives for one user concept, not separate requirements.
    raw_words = [w for w in re.findall(r"[^\W_]+", kw) if len(w) > 1 and w not in STOP_WORDS]
    groups.extend([[word] for word in raw_words])
    return groups[:10]


def _run_search(conn, category: str, terms: List[Any], max_price: float,
                limit: int, in_stock_only: bool,
                gender_hint: Optional[str] = None,
                cat_hint: Optional[str] = None, size: str = "", color: str = "",
                full_results: bool = False, fabrics=()) -> List[Dict[str, Any]]:
    params: List[Any] = []
    term_groups = [
        [fold(term) for term in group if fold(term)]
        if isinstance(group, (list, tuple)) else [fold(group)]
        for group in terms
    ]
    term_groups = [group for group in term_groups if group]
    if term_groups:
        per_term = ("(CASE "
                    "WHEN fold_vn(p.name) LIKE ? THEN 4 "
                    "WHEN fold_vn(c.name) LIKE ? THEN 3 "
                    "WHEN fold_vn(p.style) LIKE ? THEN 2 "
                    "WHEN fold_vn(p.material) LIKE ? THEN 1 "
                    "ELSE 0 END)")
        group_scores = []
        weighted_scores = []
        for group in term_groups:
            alternatives = []
            for term in group:
                weighted_scores.append(per_term)
                alternatives.append(
                    "(CASE WHEN fold_vn(p.name) LIKE ? "
                    "OR fold_vn(c.name) LIKE ? "
                    "OR fold_vn(p.style) LIKE ? "
                    "OR fold_vn(p.material) LIKE ? THEN 1 ELSE 0 END)"
                )
                params.extend([f"%{term}%"] * 4)
            group_scores.append(f"MAX({', '.join(alternatives)})")
        rank_sql = " + ".join(weighted_scores)
        coverage_sql = " + ".join(group_scores)
        rank_params = params
        coverage_params = [
            f"%{term}%"
            for group in term_groups
            for term in group
            for _ in range(4)
        ]
        params = rank_params + coverage_params
    else:
        rank_sql = "0"
        coverage_sql = "0"

    sql = f"""
        SELECT p.id, p.name, c.name AS category, p.price, p.discount_price,
               p.material, p.style, p.size_guide, p.image_url,
               COALESCE(SUM(pv.stock_quantity), 0) AS total_stock,
               GROUP_CONCAT(DISTINCT CASE WHEN pv.stock_quantity > 0 THEN pv.size END) AS sizes_in_stock,
               GROUP_CONCAT(DISTINCT CASE WHEN pv.stock_quantity > 0 THEN pv.color END) AS colors_in_stock,
               ({rank_sql}) AS rank_score,
               ({coverage_sql}) AS relevance
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_variants pv ON p.id = pv.product_id
        WHERE p.is_published = 1
    """

    # 1. Ràng buộc giới tính nghiêm ngặt (chống gợi ý đầm/váy cho nam)
    if gender_hint == "nam":
        sql += " AND c.name NOT LIKE '%Nữ%'"
    elif gender_hint == "nữ":
        sql += " AND c.name NOT LIKE '%Nam%'"

    # 2. Ràng buộc danh mục (áo, quần, đầm)
    if cat_hint == "sơ mi":
        sql += " AND (fold_vn(p.name) LIKE '%so mi%')"
    elif cat_hint == "áo khoác":
        sql += " AND (c.name LIKE '%Khoác%' OR fold_vn(p.name) LIKE '%khoac%' OR fold_vn(p.name) LIKE '%blazer%')"
    elif cat_hint == "áo":
        sql += " AND (c.name LIKE '%Áo%' OR fold_vn(p.name) LIKE '%ao%') AND c.name NOT LIKE '%Quần%' AND c.name NOT LIKE '%Đầm%'"
    elif cat_hint == "quần":
        sql += " AND (c.name LIKE '%Quần%' OR fold_vn(p.name) LIKE '%quan%') AND c.name NOT LIKE '%Áo%'"
    elif cat_hint == "đầm & váy":
        sql += " AND (c.name LIKE '%Đầm%' OR c.name LIKE '%Váy%' OR fold_vn(p.name) LIKE '%dam%' OR fold_vn(p.name) LIKE '%vay%')"

    if category and cat_hint not in ("sơ mi", "áo khoác", "đầm & váy"):
        sql += " AND fold_vn(c.name) LIKE ?"
        params.append(f"%{fold(category)}%")
    if max_price and max_price > 0:
        sql += " AND COALESCE(p.discount_price, p.price) <= ?"
        params.append(max_price)
    for fabric in fabrics:
        sql += " AND has_fabric(p.material, ?)"
        params.append(fabric)
    if size or color:
        sql += " AND EXISTS (SELECT 1 FROM product_variants v WHERE v.product_id = p.id"
        if in_stock_only:
            sql += " AND v.stock_quantity > 0"
        if size:
            sql += " AND normalize_size(v.size) = ?"
            params.append(normalize_size(size))
        if color:
            sql += " AND instr(fold_vn(v.color), ?) > 0"
            params.append(fold(color))
        sql += ")"

    sql += " GROUP BY p.id"
    having = []
    if term_groups:
        having.append("relevance > 0")
    if in_stock_only:
        having.append("total_stock > 0")
    if having:
        sql += " HAVING " + " AND ".join(having)
    sql += " ORDER BY relevance DESC, rank_score DESC, total_stock DESC, p.id ASC"
    if not full_results:
        sql += " LIMIT ?"
        params.append(max(1, min(int(limit or 4), 8)))

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    for r in rows:
        raw_score = r.get("relevance", 0)
        if term_groups and raw_score > 0:
            r["relevance"] = round(min(1.0, raw_score / len(term_groups)), 4)
        else:
            r["relevance"] = 1.0 if category else 0.0
        r.pop("rank_score", None)
    return rows


# ---------------------------------------------------------------- TOOLS
def db_search_products(category: str = "", keyword: str = "", max_price: float = 0.0,
                       limit: int = 4, in_stock_only: bool = True, size: str = "",
                       color: str = "", height_cm: Optional[float] = None,
                       weight_kg: Optional[float] = None, material: str = "") -> Dict[str, Any]:
    """Tìm sản phẩm thời trang. category: loại đồ (vd 'áo nam', 'quần nam', 'đầm nữ', 'áo khoác').
    keyword: phong cách / dịp / chất liệu (vd 'thể thao', 'công sở', 'linen'). max_price: giá tối đa VNĐ (0 = không giới hạn).
    size, color: biến thể yêu cầu. height_cm, weight_kg: số đo. material: chất liệu khách yêu cầu.
    Trả về OK, CLARIFY, NO_MATCH hoặc OUT_OF_STOCK theo dữ liệu."""
    conn = _connect()
    try:
        conn.execute("BEGIN")
        combined_text = f"{category} {keyword}".strip()
        gender_hint = _detect_gender(combined_text)
        cat_hint = _detect_category_hint(combined_text)

        term_groups = _expand_term_groups(keyword)
        if not term_groups and not category:
            return {
                "status": "CLARIFY",
                "found": False,
                "count": 0,
                "score": 0.5,
                "instruction": "Hỏi khách một câu về loại trang phục, phong cách, dịp hoặc ngân sách.",
                "products": [],
            }

        has_measurements = height_cm is not None or weight_kg is not None
        search_options = {}
        if size or color or has_measurements:
            search_options = {"size": size, "color": color, "full_results": has_measurements}
        fabrics = requested_fabrics(material or keyword)
        if fabrics:
            search_options["fabrics"] = fabrics
            conn.create_function(
                "has_fabric", 2,
                lambda value, fabric: bool(re.search(r"\b" + re.escape(fabric) + r"\b", fold(value))),
            )
        specificity = 1.0 if category or cat_hint or len(term_groups) > 1 else 0.5
        variants_by_product = defaultdict(list)
        if has_measurements:
            for variant in conn.execute("""
                SELECT v.product_id, v.color, v.size, v.stock_quantity
                FROM product_variants v JOIN products p ON p.id = v.product_id
                WHERE p.is_published = 1
            """):
                variants_by_product[variant["product_id"]].append(variant)

        def search(stock_only):
            rows = _run_search(
                conn, category, term_groups, max_price, limit, stock_only,
                gender_hint, cat_hint, **search_options
            )
            results = []
            for row in rows:
                if has_measurements:
                    fits = matching_sizes(row.get("size_guide"), height_cm, weight_kg)
                    if size:
                        fits = [fit for fit in fits if fit == normalize_size(size)]
                    if not fits:
                        continue
                    variants = matching_variants(variants_by_product[row["id"]], fits, color)
                    if stock_only:
                        variants = [v for v in variants if v["stock_quantity"] > 0]
                    if not variants:
                        continue
                    row = {**row, "fit_sizes": list(dict.fromkeys(normalize_size(v["size"]) for v in variants))}
                results.append({**row, "relevance": round(row["relevance"] * specificity, 4)})
            return results

        rows = search(in_stock_only)
        best_score = max((row["relevance"] for row in rows), default=0.0)
        matches = [
            row for row in rows
            if row["relevance"] >= PRODUCT_MATCH_THRESHOLD
        ][:min(max(int(limit or 3), 1), 3)]

        if matches:
            return {
                "status": "OK",
                "found": True,
                "count": len(matches),
                "score": best_score,
                "instruction": "Chỉ giới thiệu các sản phẩm trong products, không thêm mẫu khác.",
                "products": matches,
            }
        if in_stock_only and any(row["relevance"] >= PRODUCT_MATCH_THRESHOLD for row in search(False)):
            return {
                "status": "OUT_OF_STOCK", "found": False, "count": 0,
                "score": best_score, "products": [],
            }
        if best_score >= PRODUCT_CLARIFY_THRESHOLD:
            return {
                "status": "CLARIFY",
                "found": False,
                "count": 0,
                "score": best_score,
                "instruction": "Không gợi ý sản phẩm. Hỏi một câu để làm rõ yêu cầu.",
                "products": [],
            }
        return {
            "status": "NO_MATCH",
            "found": False,
            "count": 0,
            "score": best_score,
            "instruction": "Không gợi ý sản phẩm thay thế. Báo chưa có mẫu phù hợp.",
            "products": [],
        }
    finally:
        conn.close()


def _find_public_product(conn, product_name):
    name = fold(product_name).strip()
    if not name:
        return None
    rows = conn.execute(
        """SELECT id, name, category_id, style, size_guide FROM products
           WHERE is_published = 1 AND instr(fold_vn(name), ?) > 0
           ORDER BY (fold_vn(name) = ?) DESC, id LIMIT 2""",
        (name, name),
    ).fetchall()
    if rows and (len(rows) == 1 or fold(rows[0]["name"]) == name != fold(rows[1]["name"])):
        return rows[0]
    return None


def db_stock_for_products(product_ids):
    """Return only public products and current variants, in card order."""
    if not product_ids:
        return []
    placeholders = ", ".join("?" for _ in product_ids)
    conn = get_db_connection()
    try:
        rows = conn.execute(f"""
            SELECT p.id, p.name, v.color, v.size, v.stock_quantity
            FROM products p LEFT JOIN product_variants v ON v.product_id = p.id
            WHERE p.is_published = 1 AND p.id IN ({placeholders})
            ORDER BY v.id
        """, product_ids)
        products = {}
        for row in rows:
            product = products.setdefault(row["id"], {"id": row["id"], "name": row["name"], "variants": []})
            if row["stock_quantity"] is not None:
                product["variants"].append(dict(row))
        return [products[product_id] for product_id in product_ids if product_id in products]
    finally:
        conn.close()


def db_stock_by_sku(sku):
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT p.name, v.color, v.size, v.stock_quantity
            FROM product_variants v JOIN products p ON p.id = v.product_id
            WHERE p.is_published = 1 AND v.sku = ? COLLATE NOCASE
        """, (sku,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def db_check_variant_stock(product_name: str, color: str = "", size: str = "") -> Dict[str, Any]:
    """Kiểm tra tồn kho theo màu và size của một mẫu đang hiển thị."""
    conn = _connect()
    try:
        conn.execute("BEGIN")
        product = _find_public_product(conn, product_name)
        if product is None:
            return {"status": "NO_MATCH", "found": False, "message": "Cửa hàng chưa tìm thấy mẫu theo tên bạn nêu. Bạn kiểm tra lại tên sản phẩm giúp mình nhé."}
        sql = """
            SELECT p.name, pv.sku, pv.color, pv.size, pv.stock_quantity,
                   COALESCE(p.discount_price, p.price) AS current_price
            FROM product_variants pv
            JOIN products p ON pv.product_id = p.id
            WHERE p.id = ? AND p.is_published = 1
        """
        params: List[Any] = [product["id"]]
        if color:
            sql += " AND instr(fold_vn(pv.color), ?) > 0"
            params.append(fold(color))
        if size:
            sql += " AND normalize_size(pv.size) = ?"
            params.append(normalize_size(size))
        rows = conn.execute(sql, params).fetchall()
        if not rows:
            return {"status": "NO_VARIANT", "found": False, "message": f"Mẫu {product['name']} không có màu hoặc size bạn hỏi."}
        status = "IN_STOCK" if any(row["stock_quantity"] > 0 for row in rows) else "OUT_OF_STOCK"
        return {"status": status, "found": True, "variants": [dict(r) for r in rows]}
    finally:
        conn.close()


def db_recommend_size(height_cm: float, weight_kg: float, gender: str = "",
                      product_name: str = "", color: str = "") -> Dict[str, Any]:
    """Đối chiếu số đo (cm, kg) với bảng size và tồn kho của mẫu được nêu."""
    if not valid_measurements(height_cm, weight_kg):
        return {
            "invalid_measurements": True,
            "recommended_size": None,
            "note": "Bạn kiểm tra lại chiều cao và cân nặng giúp mình nhé.",
        }
    conn = _connect()
    try:
        conn.execute("BEGIN")
        product = _find_public_product(conn, product_name)
        if product is None:
            return {"recommended_size": None, "note": "Bạn muốn đối chiếu số đo với mẫu nào trong cửa hàng ạ?"}
        fits = matching_sizes(product["size_guide"], height_cm, weight_kg)
        if not fits:
            return {"recommended_size": None, "note": f"Mình chưa xác nhận được size theo bảng của {product['name']}."}
        variants = conn.execute(
            "SELECT size, color, stock_quantity FROM product_variants WHERE product_id = ?", (product["id"],)
        ).fetchall()
    finally:
        conn.close()
    in_stock = list(dict.fromkeys(normalize_size(v["size"]) for v in available_variants(variants, fits, color)))
    recommended = in_stock[0] if in_stock else fits[0]
    sizes = ", ".join(fits)
    color_context = f" với màu {color}" if color else ""
    availability = (
        f"Size phù hợp còn hàng{color_context}: {', '.join(in_stock)}."
        if in_stock else f"Hiện chưa có size phù hợp còn hàng{color_context}."
    )
    return {
        "recommended_size": recommended,
        "matching_sizes": fits,
        "sizes_in_stock": in_stock,
        "note": f"Theo bảng size của {product['name']}, size khớp số đo là {sizes}. {availability}",
    }


def db_suggest_outfit(product_name: str, limit: int = 3) -> Dict[str, Any]:
    """Gợi ý các món phối cùng (khác loại, cùng phong cách, còn hàng) với một sản phẩm đã chọn để bán kèm."""
    conn = _connect()
    try:
        conn.execute("BEGIN")
        base = _find_public_product(conn, product_name)
        if not base:
            return {"found": False, "products": [], "message": "Bạn cho mình tên đầy đủ của mẫu cần phối nhé."}

        def fetch(same_style: bool):
            sql = """
                SELECT p.id, p.name, c.name AS category, p.price, p.discount_price, p.style, p.image_url,
                       COALESCE(SUM(pv.stock_quantity), 0) AS total_stock
                FROM products p
                JOIN categories c ON p.category_id = c.id
                LEFT JOIN product_variants pv ON p.id = pv.product_id
                WHERE p.is_published = 1 AND p.category_id != ?
            """
            params: List[Any] = [base["category_id"]]
            gender = _detect_gender(base["name"])
            if gender:
                sql += " AND instr(fold_vn(c.name), ?) = 0"
                params.append("nu" if gender == "nam" else "nam")
            if same_style and base["style"]:
                sql += " AND p.style = ?"
                params.append(base["style"])
            sql += " GROUP BY p.id HAVING total_stock > 0 ORDER BY p.id ASC LIMIT ?"
            params.append(max(1, min(int(limit or 3), 5)))
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

        rows = fetch(True) or fetch(False)
        return {"found": bool(rows), "base_product": base["name"], "products": rows}
    finally:
        conn.close()


def db_lookup_order_for_customer(order_code: str, customer_user_id: Optional[int]) -> Dict[str, Any]:
    """Tra cứu đơn hàng chỉ khi người dùng đã đăng nhập và sở hữu đơn hàng."""
    if customer_user_id is None:
        return {"found": False, "message": "Vui lòng đăng nhập để tra cứu đơn hàng của bạn."}

    conn = _connect()
    try:
        order = conn.execute("""
            SELECT o.* FROM orders o
            JOIN customer_order_links l ON l.order_id = o.id
            WHERE o.order_code = ? AND l.user_id = ?
        """, (order_code.strip(), customer_user_id)).fetchone()
        if not order:
            return {"found": False, "message": "Không tìm thấy đơn hàng của bạn với mã này."}
        items = conn.execute("""
            SELECT p.name, pv.color, pv.size, oi.quantity, oi.unit_price, oi.subtotal
            FROM order_items oi
            JOIN product_variants pv ON oi.variant_id = pv.id
            JOIN products p ON pv.product_id = p.id
            WHERE oi.order_id = ?
        """, (order["id"],)).fetchall()
        history = conn.execute("""
            SELECT old_status, new_status, changed_at, note
            FROM order_status_history WHERE order_id = ? ORDER BY id ASC
        """, (order["id"],)).fetchall()
        name = order["customer_name"] or ""
        return {
            "found": True,
            "order_code": order["order_code"],
            "status": order["status"],
            "total_amount": order["total_amount"],
            # Che bớt tên khách để tránh lộ thông tin khi chỉ cần mã đơn
            "customer_name": (name[:1] + "***" + name[-1:]) if len(name) > 2 else name,
            "items": [dict(it) for it in items],
            "timeline": [dict(h) for h in history],
        }
    finally:
        conn.close()


def db_lookup_order(order_code: str) -> Dict[str, Any]:
    """Tra cứu trạng thái đơn hàng của khách đã đăng nhập bằng mã đơn hàng."""
    return db_lookup_order_for_customer(order_code, None)


ALL_TOOLS = [db_search_products, db_check_variant_stock, db_recommend_size,
         db_suggest_outfit, db_lookup_order]
