from llm_wiki.project_id import slugify_project_name


def test_slugify_project_name_strips_duplicate_suffixes() -> None:
    assert slugify_project_name("v2_order_forecast copy") == "v2-order-forecast"
