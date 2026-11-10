"""Reference shirt measurements transcribed from the supplied size-chart image."""

from services.rag_rules import fold, nearest_size, valid_measurements


# Each row is (size, minimum cm, maximum cm, minimum kg, maximum kg).
# A missing minimum or maximum weight represents a strict inequality in the image.
SHIRT_SIZE_CHART = {
    "nam": (
        ("XS", 148, 154, None, 45),
        ("S", 155, 160, 46, 55),
        ("M", 161, 167, 56, 65),
        ("L", 168, 175, 66, 75),
        ("XL", 176, 181, 76, 85),
        ("2XL", 182, 187, 86, 95),
        ("3XL", 188, 193, 96, 100),
        ("4XL", 188, 194, 101, 115),
        ("5XL", 188, 195, 115, 120),
        ("6XL", 188, 196, 135, None),
    ),
    "nu": (
        ("XS", 141, 147, None, 40),
        ("S", 148, 154, 41, 45),
        ("M", 155, 160, 46, 55),
        ("L", 161, 167, 55, 65),
        ("XL", 168, 175, 66, 75),
        ("2XL", 176, 181, 76, 85),
        ("3XL", 182, 187, 86, 90),
        ("4XL", 182, 188, 91, 105),
        ("5XL", 182, 189, 106, 110),
        ("6XL", 188, 190, 120, None),
    ),
}


def recommend_shirt_size(height_cm: float | None = None, weight_kg: float | None = None,
                         gender: str = "") -> dict:
    """Tư vấn size áo tham khảo theo chiều cao (cm), cân nặng (kg) và bảng nam/nữ."""
    result = {"source": "shirt_size_chart_image", "recommended_size": None}
    gender = fold(gender).strip()
    if not valid_measurements(height_cm, weight_kg):
        return {**result, "status": "CLARIFY", "note": "Bạn kiểm tra lại chiều cao và cân nặng giúp mình nhé."}

    if height_cm is not None and weight_kg is not None and gender not in SHIRT_SIZE_CHART:
        charts = {label: recommend_shirt_size(height_cm, weight_kg, label) for label in ("nam", "nữ")}
        advice = [
            f"Áo {label}: " + (
                f"tham khảo size {fit['recommended_size']}."
                if fit["recommended_size"] else "cần bảng size riêng của mẫu."
            )
            for label, fit in charts.items()
        ]
        return {**result, "status": "CLARIFY", "charts": charts,
                "note": f"Với {height_cm:g} cm và {weight_kg:g} kg: " + " ".join(advice)}

    missing = []
    if height_cm is None:
        missing.append("chiều cao")
    if weight_kg is None:
        missing.append("cân nặng")
    if gender not in SHIRT_SIZE_CHART:
        missing.append("bảng áo nam hay nữ")
    if missing:
        given = ""
        if height_cm is not None and weight_kg is not None:
            given = f"Mình đã có số đo {height_cm:g} cm và {weight_kg:g} kg. "
        return {**result, "status": "CLARIFY", "note": given + f"Bạn cho mình biết {', '.join(missing)} nhé."}

    height_sizes, weight_sizes = [], []
    for size, min_cm, max_cm, min_kg, max_kg in SHIRT_SIZE_CHART[gender]:
        if min_cm <= height_cm <= max_cm:
            height_sizes.append(size)
        if min_kg is None:
            matches_weight = weight_kg < max_kg
        elif max_kg is None:
            matches_weight = weight_kg > min_kg
        else:
            matches_weight = min_kg <= weight_kg <= max_kg
        if matches_weight:
            weight_sizes.append(size)

    result.update(height_sizes=height_sizes, weight_sizes=weight_sizes)
    matches = [size for size in height_sizes if size in weight_sizes]
    if matches:
        size = matches[0]
        return {
            **result, "status": "OK", "recommended_size": size,
            "note": f"Size {size} theo bảng áo {'nam' if gender == 'nam' else 'nữ'} tham khảo. "
                    f"Cả {height_cm:g} cm và {weight_kg:g} kg đều khớp size này.",
        }
    if height_sizes and weight_sizes:
        rows = [
            (size, (min_cm, max_cm), (min_kg, max_kg))
            for size, min_cm, max_cm, min_kg, max_kg in SHIRT_SIZE_CHART[gender]
            if min_kg is not None and max_kg is not None
        ]
        bounded = {size for size, _, _ in rows}
        size = nearest_size(rows, height_cm, weight_kg) if bounded.intersection(height_sizes) and bounded.intersection(weight_sizes) else None
        intro = f"Bạn có thể thử size {size} trước. " if size else ""
        return {
            **result, "status": "MEASUREMENT_CONFLICT", "recommended_size": size,
            "note": intro + f"Chiều cao khớp size {', '.join(height_sizes)}, cân nặng khớp size {', '.join(weight_sizes)}. "
                    "Đây là size tham khảo, bạn có thể đối chiếu thêm bảng của mẫu áo.",
        }
    return {
        **result, "status": "NO_MATCH",
        "note": "Bảng áo XS–6XL chưa có khoảng phù hợp với số đo này. Bạn gửi mẫu áo đang xem để mình đối chiếu bảng riêng nhé.",
    }
