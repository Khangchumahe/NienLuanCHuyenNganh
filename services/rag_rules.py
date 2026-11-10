"""Shared parsing and catalog rules for the two RAG paths."""

import math
import re
import unicodedata


HEIGHT = r"(?:\d\s*m\s*\d{1,2}|\d[.,]\d+\s*m|\d{2,3}\s*cm)"
WEIGHT = r"\d{2,3}(?:[.,]\d+)?\s*(?:kg|kí|ký|cân)"
NUMBER = r"\d{1,10}(?:[.,]\d{1,3}){0,3}"
MONEY = rf"(?:{NUMBER}\s*(?:triệu|nghìn|ngàn|vnđ|vnd|đồng|tr|k|đ)|\d{{1,3}}(?:[.,]\d{{3}}){{1,3}}|\d{{4,10}})"
BUDGET = (
    rf"(?<!\w)(?:dưới|tối đa|không quá|ngân sách|tầm|<=?)\s*[:=]?\s*({MONEY})(?!\w|[.,]\d)"
    rf"|(?<![\w.,])({MONEY})\s*(?:trở xuống|đổ lại)\b"
)
SIZE_LABEL = r"(?:[2-5]XL|XXXL|XXL|XL|XS|S|M|L|FREE\s*SIZE|\d{2})"
ORDER_CODE = re.compile(r"\bORD-[A-Z0-9-]+\b", re.IGNORECASE)
COLORS = r"xanh navy|xanh dương|xanh lá|xanh rêu|xanh nhạt|đen|trắng|xám|ghi|nâu|be|đỏ|hồng|tím|vàng|cam|kem|xanh"
FABRICS = re.compile(r"\b(?:modal|cotton|linen|denim|polyester|viscose|tencel|rayon|nylon|spandex|lyocell|lụa|đũi)\b")
STOCK_QUESTION = re.compile(
    rf"\b(?:tồn kho|hết hàng|còn hàng|còn (?:màu|size|mẫu nào|bán)|còn (?:{SIZE_LABEL})\b|còn (?:{COLORS})\b|còn không|có hàng|có sẵn)\b",
    re.IGNORECASE,
)


def fold(text):
    decomposed = unicodedata.normalize("NFD", str(text or "").casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c)).replace("đ", "d")


def _height_cm(value):
    compact = re.sub(r"\s+", "", value.casefold()).replace(",", ".")
    if compact.endswith("cm"):
        return float(compact[:-2])
    if "m" in compact:
        meters, centimeters = compact.split("m", 1)
        return float(meters) * 100 + int(centimeters.ljust(2, "0") or 0)
    return float(compact)


def _amount(value):
    number, unit = re.fullmatch(r"(\d+(?:[.,]\d+)*)\s*(.*)", value).groups()
    scale = {"k": 1000, "nghìn": 1000, "ngàn": 1000, "tr": 1000000, "triệu": 1000000}
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", number):
        number = number.replace(".", "").replace(",", "")
    try:
        return float(number.replace(",", ".")) * scale.get(unit, 1)
    except ValueError:
        return None


def query_constraints(query):
    query = unicodedata.normalize("NFC", query.casefold())
    height = re.search(rf"(?<!\w){HEIGHT}(?!\w)", query)
    weight = re.search(rf"(?<!\w)({WEIGHT})(?!\w)", query)
    budgets = [_amount(first or second) for first, second in re.findall(BUDGET, query)]
    size = re.search(rf"\bsize\s+({SIZE_LABEL})\b", query, re.IGNORECASE)
    color = re.search(rf"\bmàu\s+({COLORS})\b", query)
    # A size question uses measurements. A stated size in a stock query is a filter.
    return {
        "height": _height_cm(height.group()) if height else None,
        "weight": float(re.match(r"[\d.,]+", weight.group()).group().replace(",", ".")) if weight else None,
        "max_price": min((amount for amount in budgets if amount is not None), default=None),
        "size": normalize_size(size.group(1)) if size else "",
        "color": color.group(1) if color else "",
    }


def catalog_query(query):
    for pattern in (
        BUDGET, rf"(?<!\w){HEIGHT}(?!\w)", rf"(?<!\w){WEIGHT}(?!\w)",
        rf"\bsize\s+{SIZE_LABEL}\b", rf"\bmàu\s+(?:{COLORS})\b",
    ):
        query = re.sub(pattern, " ", query, flags=re.IGNORECASE)
    return query


def normalize_size(size):
    size = str(size or "").replace(" ", "").upper()
    return "3XL" if size == "XXXL" else "XXL" if size == "2XL" else size


def valid_measurements(height, weight):
    return (height is None or math.isfinite(height) and 60 < height < 240) and (
        weight is None or math.isfinite(weight) and 20 < weight < 250
    )


def matching_sizes(guide, height, weight):
    """Read size rows shipped with the catalog, including weight-only guides."""
    if height is None and weight is None or not valid_measurements(height, weight):
        return []
    labels = re.compile(rf"\b(?:size\s+)?({SIZE_LABEL})\s*(?:\([^)]*\))?\s*:", re.IGNORECASE)
    guide = str(guide or "")
    rows = list(labels.finditer(guide))
    matches = []
    for index, label in enumerate(rows):
        row = guide[label.end():rows[index + 1].start() if index + 1 < len(rows) else len(guide)]
        height_range = re.match(rf"\s*({HEIGHT}|\d{{3}})\s*[-–—]\s*({HEIGHT})", row, re.IGNORECASE)
        weight_range = re.search(r"(\d{2,3}(?:[.,]\d+)?)\s*[-–—]\s*(\d{2,3}(?:[.,]\d+)?)\s*kg\b", row, re.IGNORECASE)
        comparisons = []
        if height is not None and height_range:
            comparisons.append(_height_cm(height_range.group(1)) <= height <= _height_cm(height_range.group(2)))
        if weight is not None and weight_range:
            low, high = (float(value.replace(",", ".")) for value in weight_range.groups())
            comparisons.append(low <= weight <= high)
        if comparisons and all(comparisons):
            matches.append(normalize_size(label.group(1)))
    return list(dict.fromkeys(matches))


def matching_variants(variants, sizes=(), color=""):
    return [
        v for v in variants
        if (not sizes or normalize_size(v["size"]) in sizes)
        and (not color or fold(color) in fold(v["color"]))
    ]


def available_variants(variants, sizes=(), color=""):
    return [v for v in matching_variants(variants, sizes, color) if v["stock_quantity"] > 0]


def requested_fabrics(query):
    return list(dict.fromkeys(fold(fabric) for fabric in FABRICS.findall(query.casefold())))


def stock_summary(variants):
    """Show a short, verified size summary per color."""
    by_color = {}
    for variant in available_variants(variants):
        by_color.setdefault(variant["color"], set()).add(normalize_size(variant["size"]))
    size_order = ("XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL")
    colors_by_sizes = {}
    for color, sizes in list(by_color.items())[:2]:
        ordered = sorted(sizes, key=lambda size: (size_order.index(size) if size in size_order else len(size_order), size))
        colors_by_sizes.setdefault(", ".join(ordered), []).append(color)
    labels = [f"{', '.join(colors)}: {sizes}" for sizes, colors in colors_by_sizes.items()]
    if len(by_color) > 2:
        labels.append(f"+{len(by_color) - 2} màu khác")
    return " · ".join(labels)


def recommendation_intro(count, *, stock=False):
    if stock:
        return "Còn hàng nhé!" if count == 1 else f"Còn {count} mẫu phù hợp nhé!"
    return "Mình tìm được một mẫu phù hợp cho bạn." if count == 1 else f"Mình gợi ý {count} mẫu này cho bạn."


def selling_price(product):
    return product["price"] if product.get("discount_price") is None else product["discount_price"]


def format_price(price):
    return f"{price:,.0f}".replace(",", ".") + "đ"
