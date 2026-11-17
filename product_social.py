"""Chạy một lần để cài trang sản phẩm, Review và Yêu thích."""

from pathlib import Path
from datetime import datetime
from functools import wraps
import shutil
import sqlite3

from flask import (
    jsonify, request, g, Response,
    render_template_string, abort
)

from database.db import get_db_connection


SCHEMA = '''
CREATE TABLE IF NOT EXISTS product_favorites (
    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, product_id)
);

CREATE TABLE IF NOT EXISTS product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL CHECK(length(comment) BETWEEN 1 AND 2000),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_product_reviews_product
ON product_reviews(product_id, id);

CREATE INDEX IF NOT EXISTS idx_product_favorites_product
ON product_favorites(product_id);
'''


def register_product_social(
    app, require_login, require_csrf, current_user
):
    conn = get_db_connection()
    try:
        conn.executescript('BEGIN;\n' + SCHEMA + '\nCOMMIT;')
    finally:
        conn.close()

    def customer_only(view):
        @wraps(view)
        @require_login
        def wrapped(*args, **kwargs):
            if g.user['role'] != 'CUSTOMER':
                return jsonify(
                    success=False,
                    error='Chỉ dành cho tài khoản Customer'
                ), 403
            return view(*args, **kwargs)
        return wrapped

    def published(conn, product_id):
        return conn.execute(
            'SELECT 1 FROM products '
            'WHERE id=? AND is_published=1',
            (product_id,)
        ).fetchone()

    @app.get('/social-assets/social.js')
    def social_script():
        return Response(
            SOCIAL_JS,
            mimetype='application/javascript'
        )

    @app.get('/social-assets/social.css')
    def social_style():
        return Response(SOCIAL_CSS, mimetype='text/css')

    @app.get('/products/<int:product_id>')
    def product_page(product_id):
        conn = get_db_connection()

        try:
            row = conn.execute('''
                SELECT p.*, c.name AS category_name
                FROM products p
                JOIN categories c ON c.id=p.category_id
                WHERE p.id=? AND p.is_published=1
            ''', (product_id,)).fetchone()

            if row is None:
                abort(404)

            product = dict(row)

            product['variants'] = [
                dict(variant)
                for variant in conn.execute(
                    'SELECT * FROM product_variants '
                    'WHERE product_id=? ORDER BY id',
                    (product_id,)
                )
            ]

            price = (
                product['discount_price']
                if product['discount_price'] is not None
                else product['price']
            )

            return render_template_string(
                PRODUCT_PAGE,
                product=product,
                selling_price=price
            )
        finally:
            conn.close()

    @app.get('/api/products/social-summary')
    def social_summary():
        conn = get_db_connection()

        try:
            rows = conn.execute('''
                SELECT
                    p.id,
                    COUNT(r.id) AS review_count,
                    COALESCE(
                        ROUND(AVG(r.rating), 1), 0
                    ) AS average_rating
                FROM products p
                LEFT JOIN product_reviews r
                    ON r.product_id=p.id
                WHERE p.is_published=1
                GROUP BY p.id
            ''').fetchall()

            return jsonify(
                success=True,
                products=[dict(row) for row in rows]
            )
        finally:
            conn.close()

    @app.get('/api/customer/favorites')
    @customer_only
    def get_favorites():
        conn = get_db_connection()

        try:
            rows = conn.execute('''
                SELECT
                    p.id, p.name, p.price,
                    p.discount_price, p.image_url
                FROM product_favorites f
                JOIN products p ON p.id=f.product_id
                WHERE f.user_id=? AND p.is_published=1
                ORDER BY f.created_at DESC, f.product_id DESC
            ''', (g.user['id'],)).fetchall()

            return jsonify(
                success=True,
                products=[dict(row) for row in rows]
            )
        finally:
            conn.close()

    @app.route(
        '/api/customer/favorites/<int:product_id>',
        methods=['PUT', 'DELETE']
    )
    @customer_only
    @require_csrf
    def set_favorite(product_id):
        conn = get_db_connection()

        try:
            with conn:
                conn.execute('BEGIN IMMEDIATE')

                if request.method == 'PUT':
                    if not published(conn, product_id):
                        return jsonify(
                            success=False,
                            error='Sản phẩm không còn bán'
                        ), 404

                    conn.execute('''
                        INSERT OR IGNORE INTO product_favorites
                            (user_id, product_id)
                        VALUES (?, ?)
                    ''', (g.user['id'], product_id))
                else:
                    conn.execute('''
                        DELETE FROM product_favorites
                        WHERE user_id=? AND product_id=?
                    ''', (g.user['id'], product_id))

            return jsonify(
                success=True,
                is_favorite=request.method == 'PUT'
            )
        finally:
            conn.close()

    @app.get('/api/products/<int:product_id>/reviews')
    def get_reviews(product_id):
        try:
            page = int(request.args.get('page', '1'))
        except (ValueError, TypeError):
            return jsonify(
                success=False,
                error='Trang không hợp lệ'
            ), 400

        if not 1 <= page <= 100000:
            return jsonify(
                success=False,
                error='Trang không hợp lệ'
            ), 400

        user = current_user()
        uid = user['id'] if user else -1

        conn = get_db_connection()

        try:
            conn.execute('BEGIN')

            if not published(conn, product_id):
                return jsonify(
                    success=False,
                    error='Sản phẩm không còn bán'
                ), 404

            summary = dict(conn.execute('''
                SELECT
                    COUNT(*) AS review_count,
                    COALESCE(
                        ROUND(AVG(rating), 1), 0
                    ) AS average_rating
                FROM product_reviews
                WHERE product_id=?
            ''', (product_id,)).fetchone())

            rows = conn.execute('''
                SELECT
                    r.id,
                    u.full_name AS reviewer_name,
                    r.rating,
                    r.comment,
                    r.created_at,
                    r.updated_at,
                    (r.user_id=?) AS is_owner
                FROM product_reviews r
                JOIN users u ON u.id=r.user_id
                WHERE r.product_id=?
                ORDER BY r.id DESC
                LIMIT 20 OFFSET ?
            ''', (
                uid,
                product_id,
                (page - 1) * 20
            )).fetchall()

            own = conn.execute('''
                SELECT rating, comment
                FROM product_reviews
                WHERE user_id=? AND product_id=?
            ''', (uid, product_id)).fetchone()

            return jsonify(
                success=True,
                summary=summary,
                reviews=[dict(row) for row in rows],
                own_review=dict(own) if own else None,
                can_review=bool(
                    user and user['role'] == 'CUSTOMER'
                ),
                page=page,
                pages=max(
                    1,
                    (summary['review_count'] + 19) // 20
                )
            )
        finally:
            conn.close()

    @app.route(
        '/api/products/<int:product_id>/review',
        methods=['PUT', 'DELETE']
    )
    @customer_only
    @require_csrf
    def save_review(product_id):
        data = request.get_json(silent=True)

        if request.method == 'PUT':
            if (
                not isinstance(data, dict)
                or type(data.get('rating')) is not int
                or not 1 <= data['rating'] <= 5
            ):
                return jsonify(
                    success=False,
                    error='Chọn số sao từ 1 đến 5'
                ), 400

            if (
                not isinstance(data.get('comment'), str)
                or not 1 <= len(data['comment'].strip()) <= 2000
            ):
                return jsonify(
                    success=False,
                    error='Nhận xét phải có 1–2000 ký tự'
                ), 400

        conn = get_db_connection()

        try:
            with conn:
                conn.execute('BEGIN IMMEDIATE')

                if request.method == 'PUT':
                    if not published(conn, product_id):
                        return jsonify(
                            success=False,
                            error='Sản phẩm không còn bán'
                        ), 404

                    conn.execute('''
                        INSERT INTO product_reviews (
                            user_id, product_id, rating, comment
                        )
                        VALUES (?, ?, ?, ?)

                        ON CONFLICT(user_id, product_id)
                        DO UPDATE SET
                            rating=excluded.rating,
                            comment=excluded.comment,
                            updated_at=CURRENT_TIMESTAMP
                    ''', (
                        g.user['id'],
                        product_id,
                        data['rating'],
                        data['comment'].strip()
                    ))
                else:
                    conn.execute('''
                        DELETE FROM product_reviews
                        WHERE user_id=? AND product_id=?
                    ''', (g.user['id'], product_id))

            return jsonify(success=True)
        finally:
            conn.close()


PRODUCT_PAGE = r'''
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{{ product.name }} · AURA FASHION</title>
    <link rel="stylesheet" href="/social-assets/social.css">
</head>

<body class="social-product-page" data-product-id="{{ product.id }}">
<header class="product-header">
    <a class="product-brand" href="/">
        AURA FASHION
        <small>THỜI TRANG CHO MỖI NGÀY</small>
    </a>

    <nav>
        <a href="/">Cửa hàng</a>
        <a href="/customer?tab=favorites">♡ Yêu thích</a>
        <a href="/customer">Tài khoản</a>
        <a href="/?cart=1" id="productCartLink">Giỏ hàng</a>
    </nav>
</header>

<main class="product-main">
    <p class="product-breadcrumb">
        <a href="/">Trang chủ</a> /
        {{ product.category_name }} /
        {{ product.name }}
    </p>

    <article class="product-hero">
        <div class="product-photo">
            <img
                src="{{ product.image_url or '' }}"
                alt="{{ product.name }}"
            >
        </div>

        <div class="product-info">
            <p class="product-category">{{ product.category_name }}</p>
            <h1>{{ product.name }}</h1>

            <a href="#reviews"
               class="product-review-link"
               id="productRatingLink">
                Xem đánh giá sản phẩm
            </a>

            <div class="product-price">
                {{ '{:,.0f}'.format(selling_price).replace(',', '.') }} đ

                {% if product.discount_price is not none
                      and product.discount_price < product.price %}
                <del>
                    {{ '{:,.0f}'.format(product.price).replace(',', '.') }} đ
                </del>
                {% endif %}
            </div>

            <p class="product-material">
                <strong>Chất liệu:</strong>
                {{ product.material or 'Đang cập nhật' }}
            </p>

            <div class="product-size-guide">
                <strong>Hướng dẫn chọn size</strong>
                <p>
                    {{ product.size_guide
                       or 'Liên hệ cửa hàng để được tư vấn.' }}
                </p>
            </div>

            <label class="product-label" for="productVariant">
                Chọn màu sắc / kích thước
            </label>

            <select id="productVariant"></select>

            <p id="productStock"
               class="social-muted"
               aria-live="polite"></p>

            <div class="product-buy-row">
                <label class="product-quantity">
                    Số lượng
                    <input
                        id="productQuantity"
                        type="number"
                        min="1"
                        max="100"
                        value="1"
                    >
                </label>

                <button
                    type="button"
                    id="productAddCart"
                    class="social-action primary"
                >
                    Thêm vào giỏ hàng
                </button>

                <span id="socialPageHeart"></span>
            </div>

            <a class="product-cart-link" href="/?cart=1">
                Xem giỏ hàng →
            </a>
        </div>
    </article>

    <section class="product-description">
        <h2>Thông tin sản phẩm</h2>
        <p>
            {{ product.description
               or 'Thông tin đang được cập nhật.' }}
        </p>
        <p>
            <strong>Phong cách:</strong>
            {{ product.style or 'Hằng ngày' }}
        </p>
    </section>

    <div id="reviews">
        <div id="socialProductReviewMount"></div>
    </div>
</main>

<script type="application/json" id="socialProductData">
    {{ product|tojson }}
</script>

<script src="/social-assets/social.js" defer></script>
</body>
</html>
'''


SOCIAL_CSS = r'''
.social-product-page{margin:0;background:#f6f8fc;color:#1b2942;font-family:Inter,system-ui,Arial,sans-serif}
.social-product-page *{box-sizing:border-box}
.product-header{padding:22px max(22px,calc((100vw - 1140px)/2));background:white;border-bottom:1px solid #e6eaf2;display:flex;align-items:center;justify-content:space-between;gap:22px;flex-wrap:wrap}
.product-brand{font-size:21px;font-weight:850;text-decoration:none;color:#1b2942;letter-spacing:-.5px}
.product-brand small{display:block;font-size:9px;color:#8390a6;letter-spacing:2px;margin-top:4px}
.product-header nav{display:flex;gap:22px;flex-wrap:wrap}
.product-header nav a{font-size:13px;color:#465775;text-decoration:none}
.product-main{max-width:1140px;padding:0 22px;margin:25px auto 60px}
.product-breadcrumb{font-size:12px;color:#8190a6;line-height:1.8;margin:0 0 24px}
.product-breadcrumb a{color:#596c8c;text-decoration:none}
.product-hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:40px;background:white;padding:28px;border:1px solid #e7ecf4;border-radius:22px}
.product-photo{background:#f2f0ec;border-radius:15px;overflow:hidden;align-self:start}
.product-photo img{display:block;width:100%;height:490px;object-fit:contain}
.product-category{margin:3px 0 10px;color:#6358e9;font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:1px}
.product-info h1{font-size:28px;line-height:1.35;letter-spacing:-.6px;margin:0 0 12px}
.product-review-link{color:#b77b14;font-size:13px;text-underline-offset:3px}
.product-price{font-size:29px;font-weight:800;color:#5145dc;margin:23px 0 18px}
.product-price del{font-size:15px;font-weight:400;color:#94a0b3;margin-left:12px}
.product-material{font-size:14px;color:#63718a;line-height:1.6}
.product-size-guide{background:#f8f9fd;border:1px solid #e7eaf4;border-radius:12px;padding:15px;margin:20px 0;color:#52627d;font-size:13px;line-height:1.7}
.product-size-guide p{margin:7px 0 0}
.product-label{display:block;font-size:13px;font-weight:650;margin:0 0 9px}
#productVariant{width:100%;border:1px solid #d7deeb;border-radius:9px;padding:11px;font:14px system-ui;background:white;color:#33466c}
.product-buy-row{display:flex;align-items:end;gap:12px;margin:20px 0 14px}
.product-quantity{display:grid;gap:6px;font-size:12px;color:#6b7a91;width:85px;flex-shrink:0}
.product-quantity input{width:100%;padding:12px;border:1px solid #d7deeb;border-radius:9px;font:14px system-ui}
#productAddCart{flex:1;min-height:45px;font-weight:700}
.product-buy-row .social-heart{width:45px;height:45px}
.product-cart-link{font-size:13px;color:#687999;text-decoration:none}
.product-description,#socialProductReviewMount{background:white;border:1px solid #e7ecf4;border-radius:18px;margin:24px 0;overflow:hidden}
.product-description{padding:25px}
.product-description h2{font-size:18px;margin:0 0 12px}
.product-description p{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px;line-height:1.8;color:#68758c}
.social-product-page .social-reviews{border-top:0}
.social-product-page #socialModalHeart{display:none}
#reviews{scroll-margin-top:20px}
.social-reviews [hidden],#socialFavoriteMenu[hidden]{display:none!important}
.social-heart{border:1px solid #e5e7eb;background:white;color:#8b95a7;border-radius:50%;width:40px;height:40px;font-size:27px;line-height:1;cursor:pointer;display:inline-grid;place-items:center;padding:0;flex-shrink:0}
.social-heart[aria-pressed=true]{color:#e54e76;background:#fff0f4;border-color:#f8cbd7}
.card-image-box>.social-heart{position:absolute;top:12px;right:12px;z-index:3;box-shadow:0 3px 12px #1e293b18}
.social-heart:disabled{opacity:.5;cursor:wait}
.social-heart:focus-visible,.social-action:focus-visible{outline:3px solid #a5b4fc;outline-offset:3px}
.social-rating{border:0;background:transparent;color:#b47712;font:inherit;font-size:12px;cursor:pointer;padding:5px 0;text-align:left}
.social-reviews{padding:24px;border-top:1px solid #e5e9f1;color:#1e293b}
.social-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}
.social-heading h3{font-size:18px;margin:0}
.social-summary{color:#a46c0d;font-size:14px;margin:10px 0 18px}
.social-muted{font-size:13px;color:#718096;line-height:1.6}
.social-review{padding:15px 0;border-bottom:1px solid #edf0f5}
.social-review strong{font-size:14px}
.social-review p{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px;line-height:1.6;margin:8px 0}
.social-stars{color:#d89b24;font-size:15px;margin:5px 0}
.social-review time{font-size:12px;color:#8290a4}
.social-editor{margin:20px 0;padding:18px;background:#f7f9fd;border:1px solid #e6eaf3;border-radius:12px}
.social-editor fieldset{border:0;padding:0;margin:0;min-width:0}
.social-editor label{display:grid;gap:7px;margin:0 0 12px;font-size:13px;font-weight:600}
.social-editor select,.social-editor textarea{font:inherit;padding:10px;border:1px solid #d4ddea;border-radius:8px;background:white;width:100%}
.social-editor textarea{resize:vertical;min-height:90px}
.social-action{padding:9px 13px;border:1px solid #d4ddea;border-radius:8px;background:white;color:#33466c;font:inherit;font-size:13px;cursor:pointer;text-decoration:none;display:inline-block}
.social-action.primary{background:#4f46e5;color:white;border-color:#4f46e5}
.social-action:disabled{opacity:.5;cursor:wait}
.social-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:12px}
.social-favorites-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin-top:18px}
.social-favorite-card{border:1px solid #e1e7f1;border-radius:14px;overflow:hidden;background:white}
.social-favorite-card img{width:100%;height:190px;object-fit:cover;background:#edf1f7}
.social-favorite-body{padding:15px}
.social-favorite-body h3{font-size:15px;margin:0 0 9px;line-height:1.5}
.social-toast{position:fixed;left:20px;bottom:25px;z-index:10000;max-width:min(400px,calc(100vw - 40px));background:#243654;color:white;padding:13px 18px;border-radius:12px;font:14px/1.6 system-ui;box-shadow:0 8px 25px #0f172a30}
@media(max-width:750px){.product-header{padding:18px}.product-header nav{gap:15px}.product-main{padding:0 14px}.product-hero{grid-template-columns:1fr;gap:25px;padding:18px}.product-photo img{height:350px}.product-info h1{font-size:24px}.product-price{font-size:26px}}
@media(max-width:380px){.product-buy-row{gap:8px}.product-quantity{width:65px}#productAddCart{padding:9px 8px;font-size:12px}}
'''


SOCIAL_JS = r'''
(() => {
'use strict';

const $ = id => document.getElementById(id);

const node = (tag, cls='', text='') => {
    const element = document.createElement(tag);
    element.className = cls;
    element.textContent = text;
    return element;
};

const money = n =>
    Number(n || 0).toLocaleString('vi-VN') + ' đ';

let user = null;
let csrf = '';
let favorites = new Set();
let ratings = new Map();
let favoritesData = [];
let refreshId = 0;
let panelId = null;
let reviewVersion = 0;
let toastTimer;
let favoriteQueue = Promise.resolve();

const busy = new Set();

function notice(text) {
    let element = $('socialToast');

    if (!element) {
        element = node('div', 'social-toast');
        element.id = 'socialToast';
        element.setAttribute('role', 'status');
        document.body.append(element);
    }

    element.hidden = false;
    element.textContent = text;

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        element.hidden = true;
    }, 5000);
}

async function api(path, method='GET', body) {
    const response = await fetch(path, {
        method,
        credentials: 'same-origin',
        cache: 'no-store',
        headers: {
            ...(body !== undefined
                ? {'Content-Type': 'application/json'}
                : {}),
            ...(method !== 'GET'
                ? {'X-CSRF-Token': csrf}
                : {})
        },
        body: body !== undefined
            ? JSON.stringify(body)
            : undefined
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        const error = Error(
            data.error || data.message
            || 'Không thực hiện được thao tác'
        );
        error.status = response.status;
        throw error;
    }

    return data;
}

function ratingText(id) {
    const rating = ratings.get(Number(id));

    return rating && rating.review_count
        ? '★ '
            + Number(rating.average_rating).toLocaleString('vi-VN')
            + '/5 · '
            + rating.review_count
            + ' đánh giá'
        : '☆ Chưa có đánh giá';
}

function heart(id) {
    const button = node('button', 'social-heart');

    button.type = 'button';
    button.dataset.socialFavorite = id;
    button.onclick = () => toggleFavorite(Number(id));

    paintHeart(button);
    return button;
}

function paintHeart(button) {
    const id = Number(button.dataset.socialFavorite);
    const liked = favorites.has(id);

    button.textContent = liked ? '♥' : '♡';
    button.setAttribute('aria-pressed', String(liked));

    const label = liked
        ? 'Bỏ yêu thích'
        : 'Thêm vào yêu thích';

    button.setAttribute('aria-label', label);
    button.title = label;
    button.disabled = busy.has(id);
}

function paintHearts() {
    document.querySelectorAll('[data-social-favorite]')
        .forEach(paintHeart);

    const tab = $('socialFavoriteTab');

    if (tab) {
        tab.textContent = '♡ Yêu thích (' + favorites.size + ')';
    }
}

function enhance() {
    const grid = $('productGrid');

    if (grid) {
        grid.querySelectorAll('.product-card').forEach(card => {
            const action = card.querySelector('.btn-view-detail');

            const match = action
                ?.getAttribute('onclick')
                ?.match(/openProductDetailModal\((\d+)\)/);

            if (!match) return;

            const id = Number(match[1]);

            if (!card.querySelector('[data-social-favorite]')) {
                card.querySelector('.card-image-box')
                    ?.append(heart(id));
            }

            const image = card.querySelector('.card-image-box img');

            if (image) {
                image.style.cursor = 'pointer';
                image.onclick = () =>
                    location.assign('/products/' + id);
            }

            let rating = card.querySelector('.social-rating');

            if (!rating) {
                rating = node('button', 'social-rating');
                rating.type = 'button';
                rating.onclick = () =>
                    window.openProductDetailModal(id);

                card.querySelector('.product-cat')?.after(rating);
            }

            rating.textContent = ratingText(id);
        });
    }

    const products = $('products');

    if ($('portal') && products) {
        products.querySelectorAll('[data-product]').forEach(button => {
            const id = Number(button.dataset.product);
            const cell = button.parentElement;

            if (!cell.querySelector('[data-social-favorite]')) {
                cell.append(' ', heart(id));

                const link = node(
                    'a', 'social-action', 'Đánh giá'
                );
                link.href = '/products/' + id;

                cell.append(' ', link);
            }
        });
    }

    paintHearts();
}

function renderFavorites() {
    const list = $('socialFavoriteList');
    if (!list) return;

    list.replaceChildren();

    if (!favoritesData.length) {
        list.append(node(
            'p',
            'social-muted',
            'Bạn chưa lưu sản phẩm nào. Nhấn ♡ ở sản phẩm bạn thích.'
        ));
        return;
    }

    for (const product of favoritesData) {
        const card = node('article', 'social-favorite-card');

        const image = node('img');
        image.src = product.image_url || '';
        image.alt = product.name;
        image.loading = 'lazy';

        const body = node('div', 'social-favorite-body');

        body.append(
            node('h3', '', product.name),
            node(
                'p',
                'social-muted',
                money(product.discount_price ?? product.price)
            ),
            node('p', 'social-muted', ratingText(product.id))
        );

        const actions = node('div', 'social-controls');
        const link = node(
            'a', 'social-action', 'Xem / Đánh giá'
        );

        link.href = '/products/' + product.id;

        actions.append(link, heart(product.id));
        body.append(actions);
        card.append(image, body);
        list.append(card);
    }
}

function showFavorites() {
    if (!user || user.role !== 'CUSTOMER') return;

    ['shop', 'orders', 'profile'].forEach(id => {
        $(id)?.classList.add('hidden');
    });

    document.querySelectorAll('#portal [data-tab]')
        .forEach(button => {
            button.classList.toggle(
                'active',
                button.id === 'socialFavoriteTab'
            );
        });

    $('socialFavorites').classList.remove('hidden');
    renderFavorites();
}

async function refresh() {
    const version = ++refreshId;
    let auth;

    try {
        auth = await api('/api/auth/me');
    } catch (error) {
        if (error.status !== 401) throw error;
        auth = null;
    }

    const [summary, saved] = await Promise.all([
        api('/api/products/social-summary'),

        auth?.user.role === 'CUSTOMER'
            ? api('/api/customer/favorites')
            : Promise.resolve({products: []})
    ]);

    if (version !== refreshId) return;

    user = auth?.user || null;
    csrf = auth?.csrf_token || '';

    favoritesData = saved.products;
    favorites = new Set(favoritesData.map(product => product.id));

    ratings = new Map(
        summary.products.map(product => [product.id, product])
    );

    enhance();
    renderFavorites();

    const menu = $('socialFavoriteMenu');

    if (menu) {
        menu.hidden = user?.role !== 'CUSTOMER';
    }
}

function toggleFavorite(id) {
    if (busy.has(id)) return;

    busy.add(id);
    paintHearts();

    favoriteQueue = favoriteQueue
        .then(async () => {
            await refresh();

            if (!user) {
                location.href = '/customer?tab=favorites';
                return;
            }

            if (user.role !== 'CUSTOMER') {
                throw Error(
                    'Chỉ tài khoản Customer được lưu sản phẩm yêu thích.'
                );
            }

            await api(
                '/api/customer/favorites/' + id,
                favorites.has(id) ? 'DELETE' : 'PUT'
            );

            await refresh();
        })
        .catch(error => notice(error.message))
        .finally(() => {
            busy.delete(id);
            paintHearts();
        });

    return favoriteQueue;
}

function createPanel() {
    if ($('socialReviewPanel')) return;

    const modal = $('productDetailModal');
    const mount = $('socialProductReviewMount');

    if (!modal && !mount) return;

    const panel = node('section', 'social-reviews');
    panel.id = 'socialReviewPanel';

    panel.innerHTML = `
        <div class="social-heading">
            <h3>Đánh giá sản phẩm</h3>
            <div id="socialModalHeart"></div>
        </div>

        <p id="socialReviewSummary" class="social-summary"></p>
        <p id="socialReviewHint" class="social-muted"></p>

        <form
            id="socialReviewForm"
            class="social-editor"
            hidden
        >
            <fieldset id="socialReviewFields">
                <label>
                    Số sao
                    <select id="socialReviewRating" required>
                        <option value="5">★★★★★ — Rất hài lòng</option>
                        <option value="4">★★★★☆ — Hài lòng</option>
                        <option value="3">★★★☆☆ — Bình thường</option>
                        <option value="2">★★☆☆☆ — Chưa hài lòng</option>
                        <option value="1">★☆☆☆☆ — Không hài lòng</option>
                    </select>
                </label>

                <label>
                    Nhận xét
                    <textarea
                        id="socialReviewComment"
                        maxlength="2000"
                        required
                        placeholder="Chia sẻ cảm nhận của bạn về sản phẩm..."
                    ></textarea>
                </label>

                <div class="social-controls">
                    <button
                        type="submit"
                        class="social-action primary"
                        id="socialReviewSave"
                    >
                        Gửi đánh giá
                    </button>

                    <button
                        type="button"
                        class="social-action"
                        id="socialReviewDelete"
                        hidden
                    >
                        Xóa đánh giá của tôi
                    </button>
                </div>
            </fieldset>
        </form>

        <div id="socialReviewList"></div>
        <div id="socialReviewPages" class="social-controls"></div>
    `;

    (mount || modal.querySelector('.modal-card')).append(panel);

    $('socialReviewForm').onsubmit = event => {
        event.preventDefault();
        writeReview(false);
    };

    $('socialReviewDelete').onclick = () => {
        if (confirm('Xóa đánh giá của bạn cho sản phẩm này?')) {
            writeReview(true);
        }
    };
}

async function loadReviews(id, page=1, reset=true) {
    createPanel();

    if (!$('socialReviewPanel')) return;

    const version = ++reviewVersion;
    panelId = id;

    $('socialReviewFields').disabled = true;

    if (reset) {
        $('socialReviewList').textContent = 'Đang tải đánh giá…';
        $('socialReviewSummary').textContent = '';
        $('socialReviewForm').hidden = true;
        $('socialReviewHint').textContent = '';
        $('socialReviewPages').replaceChildren();
        $('socialModalHeart').replaceChildren(heart(id));
    }

    try {
        await refresh();

        const data = await api(
            '/api/products/' + id + '/reviews?page=' + page
        );

        if (version !== reviewVersion || panelId !== id) return;

        const summary = data.summary.review_count
            ? '★ '
                + Number(data.summary.average_rating)
                    .toLocaleString('vi-VN')
                + '/5 · '
                + data.summary.review_count
                + ' đánh giá'
            : 'Chưa có đánh giá. Hãy chia sẻ cảm nhận đầu tiên!';

        $('socialReviewSummary').textContent = summary;

        const productRating = $('productRatingLink');

        if (productRating) {
            productRating.textContent = data.summary.review_count
                ? summary
                : '☆ Chưa có đánh giá';
        }

        $('socialReviewForm').hidden = !data.can_review;

        const hint = $('socialReviewHint');
        hint.replaceChildren();

        if (!data.can_review) {
            hint.append(document.createTextNode(
                user
                    ? 'Chỉ tài khoản Customer được viết đánh giá.'
                    : 'Đăng nhập tài khoản Customer để viết đánh giá. '
            ));

            if (!user) {
                const link = node('a', '', 'Đăng nhập');
                link.href = '/customer?return_product=' + id;
                hint.append(link);
            }
        } else {
            hint.textContent =
                'Mỗi khách hàng có một đánh giá cho sản phẩm; '
                + 'bạn có thể sửa hoặc xóa.';
        }

        if (reset) {
            $('socialReviewRating').value =
                String(data.own_review?.rating || 5);

            $('socialReviewComment').value =
                data.own_review?.comment || '';

            $('socialReviewSave').textContent = data.own_review
                ? 'Cập nhật đánh giá'
                : 'Gửi đánh giá';

            $('socialReviewDelete').hidden = !data.own_review;
        }

        const list = $('socialReviewList');
        list.replaceChildren();

        for (const review of data.reviews) {
            const card = node('article', 'social-review');

            card.append(
                node(
                    'strong',
                    '',
                    review.reviewer_name
                    + (review.is_owner ? ' (Bạn)' : '')
                ),
                node(
                    'div',
                    'social-stars',
                    '★'.repeat(review.rating)
                    + '☆'.repeat(5 - review.rating)
                ),
                node('p', '', review.comment)
            );

            const date = node(
                'time',
                '',
                new Date(
                    review.updated_at.replace(' ', 'T') + 'Z'
                ).toLocaleDateString('vi-VN')
            );

            card.append(date);
            list.append(card);
        }

        const pages = $('socialReviewPages');
        pages.replaceChildren();

        if (data.pages > 1) {
            for (const [label, number] of [
                ['← Trước', page - 1],
                ['Sau →', page + 1]
            ]) {
                const button = node(
                    'button', 'social-action', label
                );

                button.type = 'button';
                button.disabled =
                    number < 1 || number > data.pages;

                button.onclick = () =>
                    loadReviews(id, number, false);

                pages.append(button);
            }

            pages.append(node(
                'span',
                'social-muted',
                'Trang ' + page + '/' + data.pages
            ));
        }
    } catch (error) {
        if (version === reviewVersion) {
            $('socialReviewList').textContent = error.message;
            $('socialReviewForm').hidden = true;
        }
    } finally {
        if (version === reviewVersion) {
            $('socialReviewFields').disabled = false;
        }
    }
}

async function writeReview(remove) {
    const id = panelId;

    if (!id || $('socialReviewFields').disabled) return;

    const payload = {
        rating: Number($('socialReviewRating').value),
        comment: $('socialReviewComment').value.trim()
    };

    $('socialReviewFields').disabled = true;

    try {
        await refresh();

        if (!user || user.role !== 'CUSTOMER') {
            throw Error('Vui lòng đăng nhập tài khoản Customer.');
        }

        await api(
            '/api/products/' + id + '/review',
            remove ? 'DELETE' : 'PUT',
            remove ? undefined : payload
        );

        notice(remove ? 'Đã xóa đánh giá.' : 'Đã lưu đánh giá.');

        if (panelId === id) {
            await loadReviews(id);
        } else {
            await refresh();
        }
    } catch (error) {
        notice(error.message);
    } finally {
        if (panelId === id) {
            $('socialReviewFields').disabled = false;
        }
    }
}

function returnToProduct() {
    const id = new URLSearchParams(location.search)
        .get('return_product');

    if (
        user?.role === 'CUSTOMER'
        && /^\d+$/.test(id || '')
    ) {
        location.replace('/products/' + id + '#reviews');
    }
}

function setupProductPage() {
    const product = JSON.parse(
        $('socialProductData').textContent
    );

    const select = $('productVariant');
    const quantity = $('productQuantity');
    const add = $('productAddCart');

    function cart() {
        try {
            const value = JSON.parse(
                localStorage.getItem('aura_cart') || '[]'
            );
            return Array.isArray(value) ? value : [];
        } catch {
            return [];
        }
    }

    function cartBadge() {
        const count = cart().reduce(
            (sum, item) => sum + (
                Number.isInteger(item.quantity)
                && item.quantity > 0
                    ? item.quantity
                    : 0
            ),
            0
        );

        $('productCartLink').textContent =
            'Giỏ hàng (' + count + ')';
    }

    for (const variant of product.variants) {
        const option = node(
            'option',
            '',
            variant.color
            + ' / Size ' + variant.size
            + ' — còn ' + variant.stock_quantity
        );

        option.value = variant.id;
        option.disabled = variant.stock_quantity < 1;
        select.append(option);
    }

    const first = product.variants.find(
        variant => variant.stock_quantity > 0
    );

    if (first) {
        select.value = String(first.id);
    }

    function stock() {
        const variant = product.variants.find(
            item => item.id === Number(select.value)
        );

        add.disabled = !variant || variant.stock_quantity < 1;

        quantity.max = String(
            Math.min(100, variant?.stock_quantity || 1)
        );

        $('productStock').textContent = variant
            ? 'SKU: ' + variant.sku
                + ' · Còn ' + variant.stock_quantity
                + ' sản phẩm'
            : 'Sản phẩm chưa có biến thể.';
    }

    select.onchange = stock;
    stock();
    cartBadge();

    add.onclick = () => {
        try {
            const variant = product.variants.find(
                item => item.id === Number(select.value)
            );

            const qty = Number(quantity.value);

            if (
                !variant
                || !Number.isInteger(qty)
                || qty < 1
                || qty > 100
            ) {
                throw Error(
                    'Số lượng phải là số nguyên từ 1 đến 100.'
                );
            }

            const items = cart();

            const old = items.find(
                item => item.variant_id === variant.id
            );

            const oldQty = old ? Number(old.quantity) : 0;

            if (
                !Number.isInteger(oldQty)
                || oldQty < 0
                || oldQty + qty > variant.stock_quantity
            ) {
                throw Error(
                    'Số lượng trong giỏ vượt quá tồn kho.'
                );
            }

            const item = {
                product_id: product.id,
                variant_id: variant.id,
                product_name: product.name,
                image_url: product.image_url,
                sku: variant.sku,
                color: variant.color,
                size: variant.size,
                price: product.discount_price ?? product.price,
                quantity: oldQty + qty
            };

            if (old) {
                Object.assign(old, item);
            } else {
                items.push(item);
            }

            localStorage.setItem(
                'aura_cart',
                JSON.stringify(items)
            );

            cartBadge();
            notice('Đã thêm ' + qty + ' sản phẩm vào giỏ hàng.');
        } catch (error) {
            notice(error.message);
        }
    };
}

function setup() {
    const portal = $('portal');

    if (portal) {
        const tab = node('button', '', '♡ Yêu thích');

        tab.type = 'button';
        tab.id = 'socialFavoriteTab';
        tab.dataset.tab = 'favorites';
        tab.onclick = showFavorites;

        portal.querySelector('nav')?.append(tab);

        const section = node('div', 'card hidden');
        section.id = 'socialFavorites';

        section.append(node('h2', '', 'Sản phẩm yêu thích'));

        const list = node('div', 'social-favorites-grid');
        list.id = 'socialFavoriteList';

        section.append(list);
        portal.append(section);

        portal.addEventListener('click', event => {
            const button = event.target.closest('[data-tab]');

            if (button && button !== tab) {
                section.classList.add('hidden');
            }
        });

        const observer = new MutationObserver(() => {
            refresh()
                .then(() => {
                    if (
                        !portal.classList.contains('hidden')
                        && new URLSearchParams(location.search)
                            .get('tab') === 'favorites'
                    ) {
                        showFavorites();
                    }

                    returnToProduct();
                })
                .catch(error => notice(error.message));
        });

        observer.observe(portal, {
            attributes: true,
            attributeFilter: ['class']
        });

        if ($('products')) {
            new MutationObserver(enhance)
                .observe($('products'), {childList: true});
        }
    }

    const main = $('accountMainLink');

    if (main) {
        const link = node('a', '', '♡ Sản phẩm yêu thích');
        link.id = 'socialFavoriteMenu';
        link.href = '/customer?tab=favorites';
        link.hidden = true;

        main.after(link);
    }

    if ($('productGrid')) {
        new MutationObserver(enhance)
            .observe($('productGrid'), {childList: true});
    }

    // Các nút chi tiết cũ chuyển sang trang riêng.
    if (typeof window.openProductDetailModal === 'function') {
        window.openProductDetailModal = id =>
            location.assign('/products/' + Number(id));
    }

    const productPageId = Number(
        document.body.dataset.productId
    );

    if (productPageId) {
        $('socialPageHeart').append(heart(productPageId));
        setupProductPage();
        loadReviews(productPageId);
    }

    refresh()
        .then(() => {
            if (
                portal
                && !portal.classList.contains('hidden')
                && new URLSearchParams(location.search)
                    .get('tab') === 'favorites'
            ) {
                showFavorites();
            }

            returnToProduct();

            const params = new URLSearchParams(location.search);

            if (
                params.get('cart') === '1'
                && typeof window.openCartModal === 'function'
            ) {
                window.openCartModal();
            }

            const id = params.get('product');

            if (
                /^\d+$/.test(id || '')
                && typeof window.openProductDetailModal === 'function'
            ) {
                window.openProductDetailModal(Number(id));
            }
        })
        .catch(error => notice(error.message));

    window.addEventListener('focus', () => {
        refresh().catch(() => {});
    });

    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            refresh().catch(() => {});
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
} else {
    setup();
}
})();
'''


def install():
    root = Path(__file__).resolve().parent

    names = [
        'app.py',
        'templates/index.html',
        'templates/customer_portal.html'
    ]

    changes = {}

    for name in names:
        source = root / name

        if not source.exists():
            raise SystemExit(
                'Đặt product_social.py cùng thư mục app.py.'
            )

        original = source.read_text(encoding='utf-8-sig')
        text = original

        if name == 'app.py':
            if 'register_product_social(app,' not in text:
                marker = "if __name__ == '__main__':"

                if marker not in text:
                    raise SystemExit(
                        'Không tìm thấy điểm khởi động '
                        'trong app.py. Chưa sửa file.'
                    )

                integration = (
                    'from product_social import register_product_social\n'
                    'register_product_social('
                    'app, require_login, require_csrf, current_user'
                    ')\n\n\n'
                )

                text = text.replace(
                    marker,
                    integration + marker,
                    1
                )
        else:
            if '/social-assets/social.css' not in text:
                if '</head>' not in text or '</body>' not in text:
                    raise SystemExit(
                        'HTML thiếu thẻ head/body: ' + name
                    )

                text = text.replace(
                    '</head>',
                    '<link rel="stylesheet" '
                    'href="/social-assets/social.css">\n</head>',
                    1
                )

            if '/social-assets/social.js' not in text:
                text = text.replace(
                    '</body>',
                    '<script src="/social-assets/social.js" '
                    'defer></script>\n</body>',
                    1
                )

        if text != original:
            changes[name] = text

    if not changes:
        print('Review và Yêu thích đã được cài.')
        print('Chạy lại app.py nếu vừa sửa module.')
        return

    backup = root / (
        'backup_social_'
        + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    )
    backup.mkdir()

    for name in changes:
        target = backup / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, target)

    db = root / 'database/store.db'

    if db.exists():
        conn = sqlite3.connect(db)
        saved = sqlite3.connect(backup / 'store.db')

        try:
            conn.backup(saved)
        finally:
            saved.close()
            conn.close()

    try:
        for name, text in changes.items():
            (root / name).write_text(
                text,
                encoding='utf-8'
            )
    except Exception:
        for name in changes:
            shutil.copy2(
                backup / name,
                root / name
            )
        raise

    print('Đã cài trang sản phẩm, Review và Yêu thích.')
    print('Bản sao lưu:', backup.name)
    print('Chạy lại app.py rồi nhấn Ctrl + F5.')
    print('Giữ product_social.py trong project.')


if __name__ == '__main__':
    install()