from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_database_demo_catalog_and_account_creation():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "### Dữ liệu mẫu" in readme
    assert "database/store.db` không được Git theo dõi" in readme
    assert "chỉ có sản phẩm gốc" in readme
    assert "python seed_products.py" in readme
    assert "--db" in readme and "--no-html" in readme and "--refresh" in readme
    assert "python create_admin.py" in readme
    assert "python create_staff.py" in readme
    assert "chức năng trùng nhau" in readme
