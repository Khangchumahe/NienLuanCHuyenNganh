from getpass import getpass
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
