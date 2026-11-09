"""Chạy sau khi dừng Flask: python upgrade_staff.py"""

from pathlib import Path
from datetime import datetime
import re
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parent


def update():
    changes = {}

    def read(name):
        return (ROOT / name).read_text(encoding="utf-8-sig")

    app = read("app.py")

    if "def require_management(" in app:
        print("Project đã có bản cập nhật STAFF.")
        return

    if "url_for" not in app.split("from functools")[0]:
        app = app.replace(
            "jsonify, session, g",
            "jsonify, session, g, redirect, url_for"
        )

    # Admin và Staff cùng được sử dụng API quản lý.
    # require_admin vẫn giữ nguyên để bảo vệ dashboard.
    guard = '''def require_management(view):
    @wraps(view)
    @require_login
    def wrapped(*args, **kwargs):
        if g.user['role'] not in ('ADMIN', 'STAFF'):
            return jsonify(
                success=False,
                error='Bạn không có quyền quản lý'
            ), 403
        return view(*args, **kwargs)
    return wrapped


'''

    app = app.replace(
        "def require_csrf(view):",
        guard + "def require_csrf(view):",
        1
    )

    home = '''def account_home(user):
    if user['role'] == 'ADMIN':
        return url_for('admin_dashboard_page')
    if user['role'] == 'STAFF':
        return url_for('staff_orders_page')
    return url_for('customer_page')


'''

    if "def account_home(" in app:
        app, count = re.subn(
            r"def account_home\(user\):.*?(?=@app\.)",
            lambda match: home,
            app,
            count=1,
            flags=re.S
        )
        assert count == 1
    else:
        login_route = '''@app.get('/login')
def login_page():
    user = current_user()
    if user:
        return redirect(account_home(user))
    return render_template('customer_portal.html')


@app.route('/api/auth/register', methods=['POST'])'''

        app = app.replace(
            "@app.route('/api/auth/register', methods=['POST'])",
            home + login_route,
            1
        )

    for module in ("product", "variant", "order"):
        pattern = (
            rf"(register_admin_{module}_routes\(\s*app,\s*)"
            r"require_admin"
        )

        app, count = re.subn(
            pattern,
            r"\1require_management",
            app
        )

        assert count == 1, (
            "Không tìm thấy đăng ký routes: " + module
        )

    app = app.replace(
        "@require_admin\n@require_csrf\ndef api_sync_rag",
        "@require_management\n@require_csrf\ndef api_sync_rag"
    )

    app = re.sub(
        r"(register_admin_dashboard_routes\(\s*app,\s*require_admin)"
        r"\s*(?:,\s*current_user\s*)?\)",
        r"\1, current_user)",
        app
    )

    changes["app.py"] = app

    # Trang Admin và trang làm việc của Staff.
    dash = read("admin_dashboard.py")
    start = dash.index(
        "    @app.get('/api/admin/dashboard/summary')"
    )
    summary = dash[start:]

    changes["admin_dashboard.py"] = '''from flask import (
    render_template, jsonify, redirect, url_for, abort
)
from database.db import get_db_connection


def register_admin_dashboard_routes(app, require_admin, current_user):
    @app.get('/admin/dashboard')
    def admin_dashboard_page():
        user = current_user()
        if not user:
            return redirect(url_for('login_page'))
        if user['role'] != 'ADMIN':
            abort(403)

        return render_template(
            'admin_dashboard.html',
            is_admin=True,
            initial_page='overview'
        )

    @app.get('/staff/orders')
    def staff_orders_page():
        return management_page('orders')

    @app.get('/staff/products')
    def staff_products_page():
        return management_page('products')

    def management_page(page):
        user = current_user()
        if not user:
            return redirect(url_for('login_page'))
        if user['role'] not in ('ADMIN', 'STAFF'):
            abort(403)

        return render_template(
            'admin_dashboard.html',
            is_admin=user['role'] == 'ADMIN',
            initial_page=page
        )

''' + summary

    # Dùng chung giao diện quản lý, bỏ Tổng quan đối với Staff.
    html = read("templates/admin_dashboard.html")

    html = html.replace(
        "ADMIN CONTROL CENTER",
        "{{ 'ADMIN CONTROL CENTER' if is_admin "
        "else 'STAFF CONTROL CENTER' }}"
    )

    html = html.replace(
        "<title>Admin Dashboard · AURA FASHION</title>",
        "<title>{{ 'Quản trị' if is_admin else 'Nhân viên' }}"
        " · AURA FASHION</title>"
    )

    html = html.replace(
        '<button class="active" data-page="overview">▦ Tổng quan</button>',
        '{% if is_admin %}'
        '<button class="active" data-page="overview">▦ Tổng quan</button>'
        '{% endif %}'
    )

    html = html.replace(
        '<h1 id="pageTitle">Tổng quan cửa hàng</h1>',
        '<h1 id="pageTitle">'
        "{{ 'Tổng quan cửa hàng' if is_admin else 'Quản lý đơn hàng' }}"
        "</h1>"
    )

    html = html.replace(
        '<section id="overview">',
        '{% if is_admin %}<section id="overview">',
        1
    )

    html = html.replace(
        '<section id="orders"',
        '{% endif %}\n<section id="orders"',
        1
    )

    html = html.replace(
        "let csrf='', currentOrder=null;",
        "const IS_ADMIN = {{ is_admin|tojson }};\n"
        "const INITIAL_PAGE = {{ initial_page|tojson }};\n"
        "let csrf='', currentOrder=null;"
    )

    html = html.replace(
        "async function loadSummary(){",
        "async function loadSummary(){if(!IS_ADMIN)return;"
    )

    html = html.replace(
        "let recent=$('recentOrders');recent.replaceChildren();",
        "let recent=$('recentOrders');"
        "if(!recent)return;recent.replaceChildren();"
    )

    html = html.replace(
        "async function switchPage(page){",
        "async function switchPage(page){"
        "if(!IS_ADMIN&&page==='overview')page='orders';"
    )

    html = html.replace(
        "$(id).classList.toggle('hidden',id!==page)",
        "$(id)?.classList.toggle('hidden',id!==page)"
    )

    html = html.replace(
        "if(d.user?.role!=='ADMIN')",
        "if(!['ADMIN','STAFF'].includes(d.user?.role))"
    )

    html = html.replace(
        "await switchPage('overview');",
        "await switchPage(INITIAL_PAGE);"
    )

    html = html.replace(
        "Cần đăng nhập Admin trên trình duyệt:",
        "Cần đăng nhập tài khoản quản lý:"
    )

    if 'id="logout"' not in html:
        html = html.replace(
            'id="refresh">↻ Làm mới</button>',
            'id="refresh">↻ Làm mới</button> &nbsp; '
            '<button class="secondary" id="logout">Đăng xuất</button>'
        )

        html = html.replace(
            "(async()=>{try{const d=await api('/api/auth/me');",
            "$('logout').addEventListener('click',async()=>{"
            "try{"
            "await api('/api/auth/logout',csrfOptions('POST',{}));"
            "window.location.replace('/customer');"
            "}catch(e){show(e.message,true);}"
            "});\n"
            "(async()=>{try{const d=await api('/api/auth/me');"
        )

    changes["templates/admin_dashboard.html"] = html

    # Chuyển trang sau khi đăng nhập theo role.
    customer = read("templates/customer_portal.html")

    def role_redirect(match):
        var = match.group(1)
        return (
            f"if (['ADMIN', 'STAFF'].includes({var}.user?.role)) {{ "
            f"window.location.replace("
            f"{var}.user.role === 'STAFF' "
            f"? '/staff/orders' : '/admin/dashboard'); "
            f"return; }}"
        )

    pattern = (
        r"if\s*\(\s*(\w+)\.user(?:\?\.|\.)role\s*"
        r"(?:===\s*['\"]ADMIN['\"]|!==\s*['\"]CUSTOMER['\"])"
        r"\s*\)\s*\{[^{}]*?return\s*;?\s*\}"
    )

    customer, count = re.subn(
        pattern,
        role_redirect,
        customer
    )

    assert count >= 2, (
        "Không nhận diện được hai nhánh đăng nhập "
        "trong customer_portal.html"
    )

    changes["templates/customer_portal.html"] = customer

    # Menu tài khoản trên trang chủ.
    index = read("templates/index.html")

    index = index.replace(
        "user.role !== 'CUSTOMER' && user.role !== 'ADMIN'",
        "!['CUSTOMER', 'ADMIN', 'STAFF'].includes(user.role)"
    )

    index = index.replace(
        "if (user.role === 'ADMIN') {",
        "if (user.role === 'ADMIN' || user.role === 'STAFF') {"
    )

    index = index.replace(
        "label.textContent = 'Quản trị';",
        "label.textContent = user.role === 'STAFF' "
        "? 'Nhân viên' : 'Quản trị';"
    )

    index = index.replace(
        "main.href = '/admin/dashboard';",
        "main.href = user.role === 'STAFF' "
        "? '/staff/orders' : '/admin/dashboard';"
    )

    index = index.replace(
        "orders.href = '/admin/dashboard';",
        "orders.href = user.role === 'STAFF' "
        "? '/staff/orders' : '/admin/dashboard';"
    )

    index = index.replace(
        """main.innerHTML = '<i class="fa-solid fa-gauge"></i> Bảng điều khiển Admin';""",
        "main.textContent = user.role === 'STAFF' "
        "? 'Quản lý cửa hàng' : 'Bảng điều khiển Admin';"
    )

    changes["templates/index.html"] = index

    changes["database/schema.sql"] = read(
        "database/schema.sql"
    ).replace(
        "'ADMIN', 'CUSTOMER'",
        "'ADMIN', 'STAFF', 'CUSTOMER'"
    )

    # Công cụ tạo tài khoản Staff từ Terminal.
    changes["create_staff.py"] = '''from getpass import getpass
from database.db import create_user, get_db_connection


def main():
    email = input('Email Staff: ').strip().lower()
    name = input('Họ tên Staff: ').strip()
    password = getpass('Mật khẩu (ít nhất 8 ký tự): ')

    result = create_user(email, password, name)

    if not result['success']:
        print('Lỗi:', result['error'])
        return

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET role='STAFF' WHERE id=?",
            (result['user_id'],)
        )
        conn.commit()
        print('Đã tạo Staff.')
        print('Đăng nhập tại http://127.0.0.1:5000/customer')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
'''

    # Sao lưu các file trước khi cập nhật.
    backup = ROOT / (
        "backup_staff_"
        + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    backup.mkdir()

    for name in changes:
        source = ROOT / name

        if source.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, saved)

    # SQLite cần cập nhật CHECK constraint của bảng users.
    path = ROOT / "database/store.db"

    if path.exists():
        conn = sqlite3.connect(path)
        saved = sqlite3.connect(backup / "store.db")
        conn.backup(saved)
        saved.close()

        try:
            sql = conn.execute(
                "SELECT sql FROM sqlite_master "
                "WHERE type='table' AND name='users'"
            ).fetchone()[0]

            if "'STAFF'" not in sql:
                sql, count = re.subn(
                    r"('ADMIN'\s*,\s*'CUSTOMER')",
                    "'ADMIN', 'STAFF', 'CUSTOMER'",
                    sql
                )

                assert count == 1, (
                    "Cấu trúc users khác dự kiến. "
                    "Chưa thay đổi dữ liệu."
                )

                sql = re.sub(
                    r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?'
                    r'[\"`\[]?users[\"`\]]?',
                    "CREATE TABLE users_staff_new",
                    sql,
                    count=1,
                    flags=re.I
                )

                conn.execute("PRAGMA foreign_keys=OFF")
                conn.execute("BEGIN IMMEDIATE")

                extras = conn.execute(
                    "SELECT sql FROM sqlite_master "
                    "WHERE tbl_name='users' "
                    "AND type IN ('index','trigger') "
                    "AND sql IS NOT NULL"
                ).fetchall()

                columns = ",".join(
                    '"' + row[1] + '"'
                    for row in conn.execute("PRAGMA table_info(users)")
                )

                sequence = conn.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name='users'"
                ).fetchone()

                conn.execute(sql)

                conn.execute(
                    f"INSERT INTO users_staff_new ({columns}) "
                    f"SELECT {columns} FROM users"
                )

                conn.execute("DROP TABLE users")
                conn.execute(
                    "ALTER TABLE users_staff_new RENAME TO users"
                )

                for (statement,) in extras:
                    conn.execute(statement)

                if sequence:
                    conn.execute(
                        "UPDATE sqlite_sequence "
                        "SET seq=MAX(seq,?) WHERE name='users'",
                        (sequence[0],)
                    )

                assert not conn.execute(
                    "PRAGMA foreign_key_check"
                ).fetchall(), (
                    "Phát hiện lỗi khóa ngoại; hoàn tác migration."
                )

                conn.commit()

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Ghi các file đã cập nhật.
    try:
        for name, content in changes.items():
            (ROOT / name).write_text(content, encoding="utf-8")

    except Exception:
        for name in changes:
            saved = backup / name
            if saved.exists():
                shutil.copy2(saved, ROOT / name)
        raise

    print("Đã cập nhật STAFF.")
    print("Bản sao lưu:", backup.name)
    print("Tiếp theo chạy: python create_staff.py")


if __name__ == "__main__":
    update()