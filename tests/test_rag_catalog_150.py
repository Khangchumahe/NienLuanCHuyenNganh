import re

import pytest

from seed_products import seed_catalog
from services.rag_engine import RAGEngine


QUERIES = [
    ("nam cao 1m70 nặng 65kg áo sơ mi", "Áo Nam", None),
    ("nữ cao 1m60 nặng 55kg áo thun", "Áo Nữ", None),
    ("nam cao 1m75 nặng 70kg áo len", "Áo Nam", None),
    ("nữ cao 1m65 nặng 58kg đầm công sở", "Đầm & Váy Nữ", None),
    ("áo sơ mi nam", "Áo Nam", None),
    ("áo sơ mi nữ", "Áo Nữ", None),
    ("so mi nam", "Áo Nam", None),
    ("quần jean nam", "Quần Nam", None),
    ("quần jeans nữ", "Quần Nữ", None),
    ("quần bò nam", "Quần Nam", None),
    ("quần denim nữ", "Quần Nữ", None),
    ("áo thun nam", "Áo Nam", None),
    ("áo phông nữ", "Áo Nữ", None),
    ("t-shirt nam", "Áo Nam", None),
    ("áo khoác gió đi phượt", "Áo Khoác", None),
    ("áo khoác gió đi du lịch", "Áo Khoác", None),
    ("áo len nam giữ ấm", "Áo Nam", None),
    ("đầm công sở nữ", "Đầm & Váy Nữ", None),
    ("đầm văn phòng", "Đầm & Váy Nữ", None),
    ("áo nam dưới 300k", "Áo Nam", 300000),
    ("quần nữ dưới 350k", "Quần Nữ", 350000),
    ("áo khoác màu trắng size M còn hàng", "Áo Khoác", None),
    ("áo thun nữ màu đen size S còn hàng", "Áo Nữ", None),
    ("áo sơ mi nam size M màu trắng còn hàng", "Áo Nam", None),
]


@pytest.fixture(scope="module")
def seeded_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("rag-catalog") / "catalog.db"
    seed_catalog(
        path,
        write_index_html=False,
        image_dir=path.parent / "images",
    )
    return path


@pytest.fixture
def engine(monkeypatch, seeded_db):
    import database.db as db

    monkeypatch.setattr(db, "DB_PATH", str(seeded_db))
    return RAGEngine()


def _base_name(name):
    return re.sub(r"\s+(Đen|Trắng|Be|Xanh Navy|Nâu)$", "", name, flags=re.I)


@pytest.mark.parametrize("query,expected_category,budget", QUERIES)
def test_seeded_150_catalog_retrieval_filters_and_varies_models(
    engine, query, expected_category, budget
):
    results = engine.retrieve(query, top_k=3)

    assert results, query
    assert len({_base_name(item["product_name"]) for item in results}) == len(results)
    assert all(item["category"] == expected_category for item in results)
    if budget is not None:
        assert all(item["price"] <= budget for item in results)
    if "màu trắng" in query:
        assert all({variant["color"] for variant in item["variants"]} == {"Trắng"} for item in results)
    if "màu đen" in query:
        assert all({variant["color"] for variant in item["variants"]} == {"Đen"} for item in results)
    if "size M" in query:
        assert all({variant["size"] for variant in item["variants"]} == {"M"} for item in results)
    if "cao " in query and "kg" in query:
        assert all(item["fit_sizes"] for item in results)


def test_grouped_result_combines_available_colors_and_trace(engine):
    result = engine.generate_response("áo sơ mi nam")
    assert len(result["recommended_products"]) == len(
        { _base_name(item["name"]) for item in result["recommended_products"] }
    )
    first = result["recommended_products"][0]
    assert set(first["available_colors"]) == {"Đen", "Trắng", "Be", "Xanh Navy", "Nâu"}
    assert len({item["product_name"] for item in result["rag_trace"]["retrieved_chunks"]}) == result["rag_trace"]["retrieved_count"]

    from services.agentic_tools import db_search_products

    tool_result = db_search_products(category="áo nam", keyword="sơ mi", limit=3)
    assert tool_result["status"] == "OK"
    assert len({item["name"] for item in tool_result["products"]}) == len(tool_result["products"])
    assert set(tool_result["products"][0]["available_colors"]) == {
        "Đen", "Trắng", "Be", "Xanh Navy", "Nâu"
    }


def test_ambiguous_gender_with_measurements_asks_before_recommending(engine):
    from services.agentic_rag import AgenticRAGEngine

    reply = AgenticRAGEngine().chat_with_agent("cao 1m70 nặng 65kg áo sơ mi")
    assert "Bạn mua cho nam hay nữ ạ?" in reply["answer"]
    assert not reply["recommended_products"]
