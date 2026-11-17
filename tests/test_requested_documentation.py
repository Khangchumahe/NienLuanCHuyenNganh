from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_old_web_guide_is_replaced_and_its_useful_steps_are_in_readme():
    guide = (ROOT / "Huongdansudungweb.txt").read_text(encoding="utf-8-sig").strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert guide == "Đã chuyển vào README.md"
    assert "pip install -r requirements.txt" in readme
    assert "python seed_products.py" in readme
    assert "python seed_accounts.py" in readme
    assert "python create_admin.py" in readme
    assert "python create_staff.py" in readme
    assert "Không chạy script này trên source hiện tại" in readme


def test_srs_keeps_original_requirements_and_documents_implementation_scope():
    srs = (ROOT / "PHAN_TICH_YEU_CAU_HE_THONG.md").read_text(encoding="utf-8")
    assert "* **FR-03: Chi tiết sản phẩm:**" in srs
    assert "* **FR-12: Quản lý dữ liệu RAG AI:**" in srs
    assert "* **NFR-06 (Xác thực & Phân quyền):**" in srs
    assert "## PHẠM VI THỰC HIỆN" in srs
    assert "| FR-03 | Làm một phần |" in srs
    assert "| FR-12 | Làm một phần |" in srs
    assert "| NFR-06 | Làm một phần |" in srs
    assert "product_reviews" in srs and "product_favorites" in srs
    assert "POST /api/auth/register" in srs and "Retry-After" in srs


def test_documents_do_not_publish_a_default_account_password():
    for name in ("README.md", "PHAN_TICH_YEU_CAU_HE_THONG.md", "Huongdansudungweb.txt"):
        content = (ROOT / name).read_text(encoding="utf-8-sig")
        assert not re.search(
            r"(?:mật khẩu|password)[^\n]{0,40}12345678|"
            r"12345678[^\n]{0,40}(?:mật khẩu|password)",
            content,
            flags=re.IGNORECASE,
        )
