"""使用调用者传入的数据验证独立检索练习，不请求模型。"""

import pytest

from examples.rag.rebuild_retrieval import retrieve


@pytest.mark.parametrize("section, top_k, expected", [
    (None, 2, ["B", "A"]),
    ("Docker", 2, ["A", "C"]),
    ("Python", 2, []),
    (None, 1, ["B"]),
])
def test_retrieve_sample(section, top_k, expected):
    candidates = [
        {"text": "A", "section": "Docker", "vector": [1, 1]},
        {"text": "B", "section": "事务", "vector": [1, 0]},
        {"text": "C", "section": "Docker", "vector": [0, 1]},
    ]
    result = retrieve([1, 0], candidates, top_k=top_k, section=section)
    assert [item["candidate"]["text"] for item in result] == expected


def test_retrieve_uses_callers_candidates():
    candidates = [{"text": "New", "section": "新主题", "vector": [1, 0]}]
    result = retrieve([1, 0], candidates)
    assert [item["candidate"]["text"] for item in result] == ["New"]


def test_retrieve_uses_callers_query_vector():
    candidates = [
        {"text": "A", "section": "Docker", "vector": [1, 1]},
        {"text": "B", "section": "事务", "vector": [1, 0]},
        {"text": "C", "section": "Docker", "vector": [0, 1]},
    ]
    result = retrieve([0, 1], candidates)
    assert [item["candidate"]["text"] for item in result] == ["C", "A"]
