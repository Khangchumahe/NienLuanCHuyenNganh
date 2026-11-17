
from getpass import getpass
from database.db import create_user, get_db_connection

email = input("Email Admin: ").strip().lower()
name = input("Ho ten Admin: ").strip()
password = getpass("Mat khau Admin: ")

result = create_user(email, password, name)

if result["success"]:
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET role = 'ADMIN' WHERE id = ?",
            (result["user_id"],)
        )
        conn.commit()
        print("Da tao tai khoan Admin thanh cong!")
    finally:
        conn.close()
else:
    print("Loi:", result["error"])
