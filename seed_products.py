"""
Thêm 25 sản phẩm mới cho mỗi danh mục.
Chạy sau khi dừng Flask.
Chạy lại không thêm trùng các sản phẩm mẫu đã tạo.
"""

from pathlib import Path
from datetime import datetime
import argparse
import os
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
            ('Áo Sơ Mi Nam Oxford', 'Cotton Oxford', 399000, 'Công sở, gặp gỡ', 'Kiểu sơ mi cổ điển, dễ phối cùng quần tây hoặc jeans cho ngày đi làm và dịp gặp gỡ.', 'nam'),
            ('Áo Thun Nam Cổ Tròn', 'Cotton Compact', 249000, 'Dạo phố, hằng ngày', 'Áo thun cổ tròn đơn giản, phù hợp mặc thường ngày và phối cùng quần jeans hoặc quần short.', 'nam'),
            ('Áo Polo Nam Pique', 'Cotton Pique', 329000, 'Đi làm, dạo phố', 'Áo polo gọn gàng, có thể mặc khi đi làm hoặc dạo phố và dễ phối với quần dài.', 'nam'),
            ('Áo Len Nam Cổ Tròn', 'Len pha cotton', 459000, 'Thời tiết se lạnh', 'Áo len cổ tròn giúp giữ ấm trong ngày se lạnh, có thể mặc riêng hoặc phối ngoài áo sơ mi.', 'nam'),
            ('Áo Sơ Mi Nam Linen', 'Linen pha cotton', 429000, 'Đi làm, du lịch', 'Áo sơ mi chất liệu linen pha cotton, kiểu dáng thoải mái cho ngày đi làm hoặc chuyến đi chơi.', 'nam'),
        ]
    ),
    (
        'Quần Nam', 'quan-nam', 'pants',
        [
            ('Quần Tây Nam Slimfit', 'Polyester pha Spandex', 499000, 'Công sở, sự kiện', 'Quần tây dáng gọn, phù hợp đi làm, dự sự kiện và phối cùng sơ mi hoặc áo polo.', 'nam'),
            ('Quần Jeans Nam Straight', 'Denim pha elastane', 549000, 'Dạo phố, đi chơi', 'Quần jeans dáng straight dễ phối đồ, phù hợp dạo phố và sử dụng thường ngày.', 'nam'),
            ('Quần Kaki Nam Regular', 'Cotton Twill', 429000, 'Đi làm, dạo phố', 'Quần kaki dáng regular có vẻ ngoài gọn gàng, phù hợp đi làm hoặc dạo phố.', 'nam'),
            ('Quần Short Nam Basic', 'Cotton', 279000, 'Hằng ngày, du lịch', 'Quần short cơ bản cho ngày thường hoặc chuyến đi chơi, dễ phối với áo thun.', 'nam'),
            ('Quần Jogger Nam Thể Thao', 'Cotton pha polyester', 359000, 'Vận động, dạo phố', 'Quần jogger có kiểu dáng thoải mái, phù hợp vận động nhẹ và dạo phố.', 'nam'),
        ]
    ),
    (
        'Áo Khoác', 'ao-khoac', 'jacket',
        [
            ('Áo Khoác Bomber Unisex', 'Polyester', 599000, 'Dạo phố, du lịch', 'Áo khoác bomber dáng gọn, tiện phối lớp ngoài khi dạo phố hoặc đi du lịch.', 'unisex'),
            ('Áo Khoác Jeans Unisex', 'Denim', 649000, 'Dạo phố, đi chơi', 'Áo khoác jeans dễ phối cùng áo thun, phù hợp dạo phố và những buổi gặp bạn bè.', 'unisex'),
            ('Áo Khoác Gió Unisex', 'Nylon', 459000, 'Đi phượt, du lịch', 'Áo khoác gió nhẹ, có thể gấp gọn và mang theo khi đi phượt; phù hợp cản gió và mưa nhỏ.', 'unisex'),
            ('Áo Khoác Blazer Unisex', 'Polyester pha viscose', 799000, 'Công sở, sự kiện', 'Áo blazer có phom lịch sự, phù hợp môi trường công sở và các dịp sự kiện.', 'unisex'),
            ('Áo Khoác Cardigan Unisex', 'Len pha cotton', 529000, 'Hằng ngày, se lạnh', 'Áo cardigan len pha cotton dùng khoác ngoài khi thời tiết se lạnh, dễ phối với áo trơn.', 'unisex'),
        ]
    ),
    (
        'Đầm & Váy Nữ', 'dam-vay-nu', 'dress',
        [
            ('Đầm Nữ Chữ A Thanh Lịch', 'Cotton pha polyester', 599000, 'Công sở, tiệc nhẹ', 'Đầm chữ A có vẻ ngoài thanh lịch, phù hợp đi làm hoặc tham dự tiệc nhẹ.', 'nữ'),
            ('Đầm Nữ Midi Công Sở', 'Polyester pha viscose', 649000, 'Văn phòng, sự kiện', 'Đầm midi kiểu dáng trang nhã, phù hợp môi trường văn phòng và các dịp gặp gỡ.', 'nữ'),
            ('Đầm Nữ Dáng Suông', 'Linen pha cotton', 549000, 'Hằng ngày, du lịch', 'Đầm dáng suông thoải mái, thích hợp mặc thường ngày hoặc khi đi du lịch.', 'nữ'),
            ('Chân Váy Nữ Xếp Ly', 'Polyester', 399000, 'Công sở, dạo phố', 'Chân váy xếp ly dễ phối cùng sơ mi hoặc áo len mỏng cho ngày đi làm và dạo phố.', 'nữ'),
            ('Chân Váy Nữ Chữ A', 'Cotton Twill', 379000, 'Văn phòng, hằng ngày', 'Chân váy chữ A kiểu dáng gọn gàng, phù hợp phối đồ đi làm hoặc sinh hoạt thường ngày.', 'nữ'),
        ]
    ),
    (
        'Áo Nữ', 'ao-nu', 'blouse',
        [
            ('Áo Sơ Mi Nữ Công Sở', 'Cotton Oxford', 359000, 'Văn phòng, sự kiện', 'Áo sơ mi kiểu dáng thanh lịch, phù hợp môi trường văn phòng và các dịp gặp gỡ.', 'nữ'),
            ('Áo Thun Nữ Basic', 'Cotton Compact', 219000, 'Hằng ngày, dạo phố', 'Áo thun cơ bản dễ phối với quần jeans, chân váy hoặc quần short.', 'nữ'),
            ('Áo Blouse Nữ Cổ V', 'Viscose', 389000, 'Công sở, tiệc nhẹ', 'Áo blouse cổ V tạo vẻ chỉn chu, phù hợp đi làm hoặc dự tiệc nhẹ.', 'nữ'),
            ('Áo Len Nữ Dệt Kim', 'Len pha cotton', 429000, 'Se lạnh, hằng ngày', 'Áo len dệt kim dùng trong ngày se lạnh, có thể phối cùng chân váy hoặc quần dài.', 'nữ'),
            ('Áo Polo Nữ Thanh Lịch', 'Cotton Pique', 299000, 'Đi làm, dạo phố', 'Áo polo nữ có vẻ ngoài gọn gàng, phù hợp đi làm và dạo phố.', 'nữ'),
        ]
    ),
    (
        'Quần Nữ', 'quan-nu', 'pants',
        [
            ('Quần Tây Nữ Ống Đứng', 'Polyester pha Spandex', 459000, 'Văn phòng, sự kiện', 'Quần tây ống đứng phù hợp đi làm, dự sự kiện và phối với sơ mi hoặc blouse.', 'nữ'),
            ('Quần Jeans Nữ Ống Rộng', 'Denim pha elastane', 499000, 'Dạo phố, đi chơi', 'Quần jeans ống rộng tạo phong cách thoải mái, phù hợp dạo phố và gặp gỡ bạn bè.', 'nữ'),
            ('Quần Culottes Nữ', 'Polyester pha viscose', 399000, 'Công sở, hằng ngày', 'Quần culottes dễ phối với áo sơ mi hoặc áo thun cho ngày đi làm và sinh hoạt thường ngày.', 'nữ'),
            ('Quần Short Nữ Cạp Cao', 'Cotton Twill', 279000, 'Du lịch, dạo phố', 'Quần short cạp cao phù hợp ngày thời tiết ấm và các chuyến đi chơi.', 'nữ'),
            ('Quần Jogger Nữ Thể Thao', 'Cotton pha polyester', 329000, 'Vận động, hằng ngày', 'Quần jogger có kiểu dáng thoải mái, phù hợp vận động nhẹ và mặc thường ngày.', 'nữ'),
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


def _size_guide(gender):
    if gender == 'nữ':
        rows = [('S', '1m50-1m58', '44-50kg'), ('M', '1m56-1m64', '51-57kg'), ('L', '1m62-1m70', '58-64kg'), ('XL', '1m68-1m76', '65-72kg')]
    elif gender == 'nam':
        rows = [('S', '1m58-1m66', '50-57kg'), ('M', '1m65-1m73', '58-66kg'), ('L', '1m72-1m80', '67-75kg'), ('XL', '1m78-1m86', '76-85kg')]
    else:
        rows = [('S', '1m55-1m64', '48-55kg'), ('M', '1m63-1m72', '56-65kg'), ('L', '1m70-1m79', '66-75kg'), ('XL', '1m76-1m85', '76-85kg')]
    return ' | '.join(f'{size}: {height} ({weight})' for size, height, weight in rows)


def seed_catalog(db_path, write_index_html=True,
                 image_dir=ROOT / 'static/images/demo-products',
                 refresh=False):
    """Seed the sample catalog into the supplied SQLite database."""
    db_path = Path(db_path)
    image_dir = Path(image_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    index_path = ROOT / 'templates/index.html'
    original_html = None
    pattern = (
        r'(<div\b(?=[^>]*\bid=["\x27]categoryTabs["\x27])[^>]*>)'
        r'.*?(</div>)'
    )
    if write_index_html:
        if not index_path.exists():
            raise FileNotFoundError(index_path)
        original_html = index_path.read_text(encoding='utf-8-sig')
        if len(re.findall(pattern, original_html, flags=re.S)) != 1:
            raise ValueError('Không tìm thấy duy nhất vùng categoryTabs.')

    schema_path = ROOT / 'database/schema.sql'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript(schema_path.read_text(encoding='utf-8-sig'))

    created_files = []
    inserted = 0
    refreshed = 0
    category_ids = {}
    try:
        conn.execute('BEGIN IMMEDIATE')
        tabs = ['<button type="button" class="tab-btn active" data-cat="">Tất cả sản phẩm</button>']

        for category, slug, kind, models in CATALOG:
            rows = conn.execute(
                'SELECT id FROM categories WHERE slug=? OR name=?',
                (slug, category)
            ).fetchall()
            if len(rows) > 1:
                raise ValueError('Tên và slug danh mục trỏ tới hai ID khác nhau: ' + category)
            if rows:
                category_id = rows[0]['id']
            else:
                category_id = conn.execute(
                    'INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)',
                    (category, slug, 'Bộ sưu tập ' + category)
                ).lastrowid
            category_ids[slug] = category_id
            tabs.append(
                f'<button type="button" class="tab-btn" data-cat="{category_id}">{escape(category)}</button>'
            )

            for model_index, model_data in enumerate(models):
                model, material, price, style, description, gender = model_data
                size_guide = _size_guide(gender)
                for color_index, (color_name, color_hex) in enumerate(COLORS):
                    number = model_index * len(COLORS) + color_index + 1
                    product_slug = f'aura-demo-{slug}-{number:02d}'
                    name = model + ' ' + color_name
                    image_name = product_slug + '.svg'
                    image_path = image_dir / image_name
                    existing = conn.execute(
                        'SELECT id FROM products WHERE slug=?', (product_slug,)
                    ).fetchone()

                    if existing and refresh:
                        conn.execute(
                            'UPDATE products SET material=?, style=?, size_guide=?, description=? WHERE id=?',
                            (material, style, size_guide, description, existing['id'])
                        )
                        refreshed += 1
                    elif not existing:
                        discount_price = price - (20000 + color_index * 5000)
                        product_id = conn.execute("""
                            INSERT INTO products (
                                category_id, name, slug, price, discount_price,
                                material, style, size_guide, description,
                                image_url, is_published
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """, (
                            category_id, name, product_slug, price,
                            discount_price, material, style, size_guide,
                            description, '/static/images/demo-products/' + image_name
                        )).lastrowid
                        for size_index, size in enumerate(SIZES):
                            stock = 10 + (number * 3 + size_index * 7) % 31
                            sku = f'DEMO-{slug.upper()}-{number:02d}-{size}'
                            conn.execute("""
                                INSERT INTO product_variants (
                                    product_id, sku, color, size, stock_quantity
                                ) VALUES (?, ?, ?, ?, ?)
                            """, (product_id, sku, color_name, size, stock))
                        inserted += 1

                    if not image_path.exists():
                        created_files.append(image_path)
                        image_path.write_text(
                            illustration(category, kind, color_hex, number, name),
                            encoding='utf-8'
                        )

        if write_index_html:
            replacement_html = '\n        ' + '\n        '.join(tabs) + '\n      '
            updated_html = re.sub(
                pattern,
                lambda match: match.group(1) + replacement_html + match.group(2),
                original_html,
                count=1,
                flags=re.S
            )
            index_path.write_text(updated_html, encoding='utf-8')
        conn.commit()
    except Exception:
        conn.rollback()
        if write_index_html and original_html is not None:
            index_path.write_text(original_html, encoding='utf-8')
        for image_path in created_files:
            image_path.unlink(missing_ok=True)
        raise
    finally:
        conn.close()

    return {'inserted': inserted, 'refreshed': refreshed, 'categories': category_ids}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Thêm catalog mẫu vào SQLite.')
    parser.add_argument('--db', default=str(ROOT / 'database/store.db'))
    parser.add_argument('--no-html', action='store_true', help='Không cập nhật templates/index.html.')
    parser.add_argument('--refresh', action='store_true', help='Cập nhật mô tả/style/size guide của aura-demo-* hiện có.')
    args = parser.parse_args(argv)
    db_path = Path(args.db)
    write_html = not args.no_html

    # Keep the historical safety backup for the default interactive project run.
    if (write_html and not os.environ.get('PYTEST_CURRENT_TEST')
            and db_path.resolve() == (ROOT / 'database/store.db').resolve()
            and db_path.exists()):
        backup = ROOT / ('backup_catalog_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        backup.mkdir()
        shutil.copy2(ROOT / 'templates/index.html', backup / 'index.html')
        conn = sqlite3.connect(db_path)
        saved = sqlite3.connect(backup / 'store.db')
        try:
            conn.backup(saved)
        finally:
            saved.close()
            conn.close()

    result = seed_catalog(db_path, write_index_html=write_html, refresh=args.refresh)
    print(f"Đã thêm {result['inserted']} sản phẩm mới.")
    if args.refresh:
        print(f"Đã cập nhật nội dung {result['refreshed']} sản phẩm aura-demo-*." )
    if write_html:
        print('Đã cập nhật bộ lọc danh mục trong templates/index.html.')


if __name__ == '__main__':
    main()
