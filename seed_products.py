"""
Thêm 25 sản phẩm mới cho mỗi danh mục.
Chạy sau khi dừng Flask.
Chạy lại không thêm trùng các sản phẩm mẫu đã tạo.
"""

from pathlib import Path
from datetime import datetime
from html import escape
import re
import shutil
import sqlite3


ROOT = Path(__file__).resolve().parent

COLORS = [
    ('Đen', '#343b49'),
    ('Trắng', '#e5e8ed'),
    ('Be', '#c7b499'),
    ('Xanh Navy', '#354e73'),
    ('Nâu', '#8e6e59')
]

SIZES = ['S', 'M', 'L', 'XL']

# Mỗi danh mục: 5 mẫu x 5 màu = 25 sản phẩm.
CATALOG = [
    (
        'Áo Nam', 'ao-nam', 'shirt',
        [
            ('Áo Sơ Mi Nam Oxford', 'Cotton Oxford', 399000),
            ('Áo Thun Nam Cổ Tròn', 'Cotton Compact', 249000),
            ('Áo Polo Nam Pique', 'Cotton Pique', 329000),
            ('Áo Len Nam Cổ Tròn', 'Len pha cotton', 459000),
            ('Áo Sơ Mi Nam Linen', 'Linen pha cotton', 429000),
        ]
    ),
    (
        'Quần Nam', 'quan-nam', 'pants',
        [
            ('Quần Tây Nam Slimfit', 'Polyester pha Spandex', 499000),
            ('Quần Jeans Nam Straight', 'Denim pha elastane', 549000),
            ('Quần Kaki Nam Regular', 'Cotton Twill', 429000),
            ('Quần Short Nam Basic', 'Cotton', 279000),
            ('Quần Jogger Nam Thể Thao', 'Cotton pha polyester', 359000),
        ]
    ),
    (
        'Áo Khoác', 'ao-khoac', 'jacket',
        [
            ('Áo Khoác Bomber Unisex', 'Polyester', 599000),
            ('Áo Khoác Jeans Unisex', 'Denim', 649000),
            ('Áo Khoác Gió Unisex', 'Nylon', 459000),
            ('Áo Khoác Blazer Unisex', 'Polyester pha viscose', 799000),
            ('Áo Khoác Cardigan Unisex', 'Len pha cotton', 529000),
        ]
    ),
    (
        'Đầm & Váy Nữ', 'dam-vay-nu', 'dress',
        [
            ('Đầm Nữ Chữ A Thanh Lịch', 'Cotton pha polyester', 599000),
            ('Đầm Nữ Midi Công Sở', 'Polyester pha viscose', 649000),
            ('Đầm Nữ Dáng Suông', 'Linen pha cotton', 549000),
            ('Chân Váy Nữ Xếp Ly', 'Polyester', 399000),
            ('Chân Váy Nữ Chữ A', 'Cotton Twill', 379000),
        ]
    ),
    (
        'Áo Nữ', 'ao-nu', 'blouse',
        [
            ('Áo Sơ Mi Nữ Công Sở', 'Cotton Oxford', 359000),
            ('Áo Thun Nữ Basic', 'Cotton Compact', 219000),
            ('Áo Blouse Nữ Cổ V', 'Viscose', 389000),
            ('Áo Len Nữ Dệt Kim', 'Len pha cotton', 429000),
            ('Áo Polo Nữ Thanh Lịch', 'Cotton Pique', 299000),
        ]
    ),
    (
        'Quần Nữ', 'quan-nu', 'pants',
        [
            ('Quần Tây Nữ Ống Đứng', 'Polyester pha Spandex', 459000),
            ('Quần Jeans Nữ Ống Rộng', 'Denim pha elastane', 499000),
            ('Quần Culottes Nữ', 'Polyester pha viscose', 399000),
            ('Quần Short Nữ Cạp Cao', 'Cotton Twill', 279000),
            ('Quần Jogger Nữ Thể Thao', 'Cotton pha polyester', 329000),
        ]
    ),
]


def illustration(category, kind, color, number, name):
    """Tạo ảnh minh họa SVG, không phụ thuộc ảnh từ Internet."""

    if kind == 'pants':
        shape = (
            '<path d="M180 125H340L360 420H280'
            'L260 250L240 420H160Z"/>'
        )

    elif kind == 'dress':
        shape = (
            '<path d="M225 125Q260 148 295 125'
            'L315 210L365 420H155L205 210Z"/>'
        )

    else:
        shape = (
            '<path d="M205 130L155 150L115 235L170 260'
            'L195 215V410H325V215L350 260L405 235'
            'L365 150L315 130Q260 175 205 130Z"/>'
        )

        if kind == 'jacket':
            shape += (
                '<path d="M260 157V410M200 325H235M285 325H320"'
                ' fill="none" stroke="#ffffff"'
                ' stroke-opacity=".6" stroke-width="4"/>'
            )

        elif kind == 'blouse':
            shape += (
                '<path d="M225 142L260 195L295 142"'
                ' fill="none" stroke="#ffffff"'
                ' stroke-opacity=".6" stroke-width="4"/>'
            )

    return f'''<svg
        xmlns="http://www.w3.org/2000/svg"
        width="520"
        height="600"
        viewBox="0 0 520 600"
    >
        <title>{escape(name)}</title>

        <rect width="520" height="600" fill="#f1eee9"/>

        <circle
            cx="260" cy="265" r="180"
            fill="#e8e3db"
        />

        <ellipse
            cx="260" cy="445" rx="100" ry="13"
            fill="#29364b" opacity=".08"
        />

        <g
            fill="{color}"
            stroke="#29364b"
            stroke-opacity=".15"
            stroke-width="2"
            stroke-linejoin="round"
        >
            {shape}
        </g>

        <text
            x="260" y="510"
            text-anchor="middle"
            font-family="Arial,sans-serif"
            font-size="22"
            font-weight="700"
            fill="#273b58"
        >AURA FASHION</text>

        <text
            x="260" y="545"
            text-anchor="middle"
            font-family="Arial,sans-serif"
            font-size="17"
            fill="#78818e"
        >{escape(category)} · {number:02d}</text>
    </svg>'''


def main():
    db_path = ROOT / 'database/store.db'
    index_path = ROOT / 'templates/index.html'

    if not db_path.exists() or not index_path.exists():
        raise SystemExit(
            'Đặt seed_products.py cạnh app.py '
            'và chạy web ít nhất một lần trước.'
        )

    original = index_path.read_text(encoding='utf-8-sig')

    # Chỉ thay vùng nút lọc danh mục.
    pattern = (
        r'(<div\b(?=[^>]*\bid=["\x27]categoryTabs["\x27])[^>]*>)'
        r'.*?(</div>)'
    )

    if len(re.findall(pattern, original, flags=re.S)) != 1:
        raise SystemExit(
            'Không tìm thấy duy nhất vùng categoryTabs. '
            'Chưa thay đổi dữ liệu.'
        )

    # Sao lưu trước khi thêm dữ liệu.
    backup = ROOT / (
        'backup_catalog_'
        + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    )
    backup.mkdir()

    shutil.copy2(index_path, backup / 'index.html')

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    saved = sqlite3.connect(backup / 'store.db')
    conn.backup(saved)
    saved.close()

    conn.execute('PRAGMA foreign_keys=ON')

    created_files = []
    summaries = []

    try:
        conn.execute('BEGIN IMMEDIATE')

        tabs = [
            '<button type="button" class="tab-btn active" '
            'data-cat="">Tất cả sản phẩm</button>'
        ]

        for category, slug, kind, models in CATALOG:
            rows = conn.execute(
                'SELECT id FROM categories WHERE slug=? OR name=?',
                (slug, category)
            ).fetchall()

            if len(rows) > 1:
                raise ValueError(
                    'Tên và slug danh mục trỏ tới hai ID khác nhau: '
                    + category
                )

            if rows:
                category_id = rows[0]['id']
            else:
                category_id = conn.execute(
                    '''
                    INSERT INTO categories (
                        name, slug, description
                    )
                    VALUES (?, ?, ?)
                    ''',
                    (
                        category,
                        slug,
                        'Bộ sưu tập ' + category
                    )
                ).lastrowid

            tabs.append(
                f'<button type="button" class="tab-btn" '
                f'data-cat="{category_id}">'
                f'{escape(category)}</button>'
            )

            added = 0

            for model_index, (model, material, price) in enumerate(models):
                for color_index, (color_name, color_hex) in enumerate(COLORS):
                    number = model_index * 5 + color_index + 1
                    product_slug = f'aura-demo-{slug}-{number:02d}'
                    name = model + ' ' + color_name

                    existing = conn.execute(
                        'SELECT id FROM products WHERE slug=?',
                        (product_slug,)
                    ).fetchone()

                    image = (
                        ROOT
                        / 'static/images/demo-products'
                        / (product_slug + '.svg')
                    )

                    # Không ghi đè giá, kho hoặc dữ liệu sản phẩm đã có.
                    if not existing:
                        female = slug in (
                            'ao-nu',
                            'quan-nu',
                            'dam-vay-nu'
                        )

                        if female:
                            size_guide = (
                                'S: 40-46kg; M: 47-53kg; '
                                'L: 54-60kg; XL: 61-68kg.'
                            )
                        else:
                            size_guide = (
                                'S: 48-55kg; M: 56-64kg; '
                                'L: 65-73kg; XL: 74-83kg.'
                            )

                        size_guide += (
                            ' Bảng size tham khảo cho dữ liệu mẫu, '
                            'cần đối chiếu số đo thực tế.'
                        )

                        style = [
                            'Công sở, thanh lịch',
                            'Dạo phố, năng động',
                            'Hằng ngày, tối giản',
                            'Du lịch, thoải mái',
                            'Cuối tuần, trẻ trung'
                        ][model_index]

                        discount_price = price - (
                            20000 + color_index * 5000
                        )

                        description = (
                            f'{name}. Chất liệu {material}. '
                            f'Phù hợp {style.lower()}. '
                            'Sản phẩm mẫu phục vụ kiểm thử cửa hàng.'
                        )

                        product_id = conn.execute(
                            '''
                            INSERT INTO products (
                                category_id,
                                name,
                                slug,
                                price,
                                discount_price,
                                material,
                                style,
                                size_guide,
                                description,
                                image_url,
                                is_published
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                            ''',
                            (
                                category_id,
                                name,
                                product_slug,
                                price,
                                discount_price,
                                material,
                                style,
                                size_guide,
                                description,
                                '/static/images/demo-products/' + image.name
                            )
                        ).lastrowid

                        for size_index, size in enumerate(SIZES):
                            stock = (
                                10
                                + (number * 3 + size_index * 7) % 31
                            )

                            sku = (
                                f'DEMO-{slug.upper()}-'
                                f'{number:02d}-{size}'
                            )

                            conn.execute(
                                '''
                                INSERT INTO product_variants (
                                    product_id,
                                    sku,
                                    color,
                                    size,
                                    stock_quantity
                                )
                                VALUES (?, ?, ?, ?, ?)
                                ''',
                                (
                                    product_id,
                                    sku,
                                    color_name,
                                    size,
                                    stock
                                )
                            )

                        added += 1

                    # Tạo ảnh nếu chưa có.
                    if not image.exists():
                        image.parent.mkdir(
                            parents=True,
                            exist_ok=True
                        )

                        created_files.append(image)

                        image.write_text(
                            illustration(
                                category,
                                kind,
                                color_hex,
                                number,
                                name
                            ),
                            encoding='utf-8'
                        )

            summaries.append((category, added))

        # Cập nhật nút lọc bằng ID danh mục thực tế trong database.
        replacement = (
            '\n        '
            + '\n        '.join(tabs)
            + '\n      '
        )

        updated = re.sub(
            pattern,
            lambda match: (
                match.group(1)
                + replacement
                + match.group(2)
            ),
            original,
            count=1,
            flags=re.S
        )

        index_path.write_text(updated, encoding='utf-8')
        conn.commit()

    except Exception:
        conn.rollback()

        # Khôi phục giao diện nếu quá trình thêm dữ liệu gặp lỗi.
        index_path.write_text(original, encoding='utf-8')

        for image in created_files:
            image.unlink(missing_ok=True)

        raise

    finally:
        conn.close()

    for category, added in summaries:
        print(f'{category}: thêm {added} sản phẩm mới')

    print(
        'Tổng sản phẩm mới:',
        sum(count for _, count in summaries)
    )

    print('Bản sao lưu:', backup.name)
    print('Chạy lại app.py, mở trang chủ rồi nhấn Ctrl + F5.')


if __name__ == '__main__':
    main()