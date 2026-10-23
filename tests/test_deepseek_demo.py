"""候选生成的离线测试：替换HTTP请求，不消耗模型费用。"""

import json
from unittest.mock import Mock

import pytest
import requests
from pydantic import ValidationError

import llm_service


@pytest.fixture
def mock_post(monkeypatch):
    # 使用虚构密钥，并替换程序实际调用的post；不读取个人密钥。
    monkeypatch.setenv("DEEPSEEK_API_KEY", "offline-placeholder")
    post = Mock()
    monkeypatch.setattr(llm_service.requests, "post", post)
    return post


def response_with_content(mock_post, content):
    response = Mock()
    response.json.return_value = {
        "choices": [{"message": {"content": content}}],
    }
    mock_post.return_value = response
    return response


def test_generation_forwards_input_and_returns_candidate(mock_post):
    response = response_with_content(mock_post, json.dumps({
        "title": "  Read docs  ", "description": "  Session  ",
    }))
    result = llm_service.generate_candidate("  Read docs  ")
    assert result.model_dump() == {
        "title": "Read docs", "priority": "normal",
        "tags": [], "description": "Session",
    }
    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert payload["messages"][1]["content"] == "Read docs"
    assert payload["response_format"] == {"type": "json_object"}
    response.raise_for_status.assert_called_once_with()


@pytest.mark.parametrize("text, error_type", [
    (None, TypeError), (123, TypeError), ("", ValueError),
    ("   ", ValueError), ("x" * 2001, ValueError),
])
def test_invalid_input_does_not_request(mock_post, monkeypatch, text, error_type):
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    with pytest.raises(error_type):
        llm_service.generate_candidate(text)
    mock_post.assert_not_called()


@pytest.mark.parametrize("api_key", [None, "", " \t\n "])
def test_missing_or_blank_api_key_does_not_request(mock_post, monkeypatch, api_key):
    # None代表环境变量不存在，其余两组代表存在但没有有效内容。
    if api_key is None:
        monkeypatch.delenv("DEEPSEEK_API_KEY")
    else:
        monkeypatch.setenv("DEEPSEEK_API_KEY", api_key)

    # 输入本身合法，才能确定这次失败来自密钥检查。
    with pytest.raises(RuntimeError, match="模型服务未配置API密钥"):
        llm_service.generate_candidate("学习Python")

    mock_post.assert_not_called()


def test_api_key_is_trimmed_before_request(mock_post, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "  offline-placeholder  ")
    response_with_content(mock_post, json.dumps({"title": "学习Python"}))

    candidate = llm_service.generate_candidate("学习Python")

    assert candidate.title == "学习Python"
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer offline-placeholder"


@pytest.mark.parametrize("original", [
    requests.Timeout("timeout"), requests.ConnectionError("connection"),
])
def test_request_failure_preserves_cause(mock_post, original):
    mock_post.side_effect = original
    with pytest.raises(RuntimeError, match="模型服务请求失败") as caught:
        llm_service.generate_candidate("test")
    assert caught.value.__cause__ is original


def test_http_error_does_not_parse_body(mock_post):
    response = Mock()
    original = requests.HTTPError("status")
    response.raise_for_status.side_effect = original
    mock_post.return_value = response
    with pytest.raises(RuntimeError, match="模型服务请求失败") as caught:
        llm_service.generate_candidate("test")
    assert caught.value.__cause__ is original
    response.json.assert_not_called()


def test_invalid_outer_json_preserves_cause(mock_post):
    response = Mock()
    original = requests.exceptions.JSONDecodeError("invalid", "<html>", 0)
    response.json.side_effect = original
    mock_post.return_value = response
    with pytest.raises(RuntimeError, match="模型服务响应不是合法JSON") as caught:
        llm_service.generate_candidate("test")
    assert caught.value.__cause__ is original


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": None}])
def test_missing_response_structure(mock_post, body):
    response = Mock()
    response.json.return_value = body
    mock_post.return_value = response
    with pytest.raises(RuntimeError, match="模型服务响应缺少有效回答结构"):
        llm_service.generate_candidate("test")


@pytest.mark.parametrize("content", [None, 123, "", "   "])
def test_invalid_answer_content(mock_post, content):
    response_with_content(mock_post, content)
    with pytest.raises(RuntimeError):
        llm_service.generate_candidate("test")


def test_invalid_inner_json(mock_post):
    response_with_content(mock_post, "not JSON")
    with pytest.raises(RuntimeError, match="模型回答不是合法JSON") as caught:
        llm_service.generate_candidate("test")
    assert isinstance(caught.value.__cause__, json.JSONDecodeError)


@pytest.mark.parametrize("data", [
    [], None, {}, {"title": " "},
    {"title": "test", "priority": "urgent"},
    {"title": "test", "id": 1},
    {"title": "test", "description": "x" * 501},
])
def test_invalid_candidate_fields(mock_post, data):
    # 外层、回答结构、内层JSON都合法；只让候选模型校验失败。
    response_with_content(mock_post, json.dumps(data))
    with pytest.raises(RuntimeError, match="模型候选任务字段不合法") as caught:
        llm_service.generate_candidate("test")
    assert isinstance(caught.value.__cause__, ValidationError)


@pytest.mark.parametrize("tags, expected", [
    ([" Python ", "SQL", "python"], ["python", "sql"]),
    (["SQL", "Python", "sql"], ["sql", "python"]),
    ([], []),
])
def test_candidate_tags_are_normalized_without_reordering(mock_post, tags, expected):
    # 准备模型回答：让真实解析和候选校验处理这些标签，不发送网络请求。
    response_with_content(mock_post, json.dumps({"title": "test", "tags": tags}))

    result = llm_service.generate_candidate("test")

    # 同时检查去空白、转小写、去重和保留首次出现的顺序；空列表允许。
    assert result.tags == expected


@pytest.mark.parametrize("tags", [[""], ["Python", "   "], ["\t\n"]])
def test_candidate_blank_tags_are_rejected_before_confirmation(mock_post, tags):
    response_with_content(mock_post, json.dumps({"title": "test", "tags": tags}))

    # 标签无效时不能返回候选对象；错误应沿既有异常处理链向外报告。
    with pytest.raises(RuntimeError, match="模型候选任务字段不合法") as caught:
        llm_service.generate_candidate("test")

    assert isinstance(caught.value.__cause__, ValidationError)
    assert "tags must not be empty" in str(caught.value.__cause__)
