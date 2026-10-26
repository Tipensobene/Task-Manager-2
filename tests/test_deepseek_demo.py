"""候选生成的离线测试：替换HTTP请求，不消耗模型费用。"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import httpx
from pydantic import ValidationError

import llm_service


@pytest.fixture
def mock_client(monkeypatch):
    # 用支持异步上下文管理的替身封住整个客户端，不创建真实网络连接。
    client = MagicMock(spec=httpx.AsyncClient)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    client.post = AsyncMock()
    factory = Mock(return_value=client)
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", factory)
    yield factory, client
    # 已进入的客户端，在正常或异常退出时都应执行清理。
    if client.__aenter__.await_count:
        client.__aexit__.assert_awaited_once()


@pytest.fixture
def mock_post(monkeypatch, mock_client):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "offline-placeholder")
    return mock_client[1].post


def run_generation(text):
    # 同步pytest用例的独立入口：实际运行协程，不引入额外测试插件。
    return asyncio.run(llm_service.generate_candidate(text))


def response_with_content(mock_post, content, finish_reason="stop"):
    response = Mock()
    response.json.return_value = {
        "choices": [{"finish_reason": finish_reason, "message": {"content": content}}],
    }
    mock_post.return_value = response
    return response


def test_generation_forwards_input_and_returns_candidate(mock_post, mock_client):
    response = response_with_content(mock_post, json.dumps({
        "title": "  Read docs  ", "description": "  Session  ",
    }))
    result = run_generation("  Read docs  ")
    assert result.model_dump() == {
        "title": "Read docs", "priority": "normal",
        "tags": [], "description": "Session",
    }
    mock_post.assert_awaited_once()
    factory, client = mock_client
    factory.assert_called_once()
    timeout = factory.call_args.kwargs["timeout"]
    assert timeout.connect == 10.0
    assert (timeout.read, timeout.write, timeout.pool) == (20.0, 20.0, 20.0)
    client.__aenter__.assert_awaited_once()
    payload = mock_post.call_args.kwargs["json"]
    assert payload["messages"][1]["content"] == "Read docs"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["max_tokens"] == 2048
    system_message = payload["messages"][0]
    assert system_message["role"] == "system"
    instructions, separator, schema_text = system_message["content"].partition(
        "候选任务应符合以下JSON Schema："
    )
    assert separator
    assert "提取一条候选任务" in instructions
    # 检查实际发送的规则，不依赖缩进、空格或JSON键排列顺序。
    sent_schema = json.loads(schema_text)
    assert sent_schema == llm_service.TaskCandidate.model_json_schema()
    response.raise_for_status.assert_called_once_with()


@pytest.mark.parametrize("text, error_type", [
    (None, TypeError), (123, TypeError), ("", ValueError),
    ("   ", ValueError), ("x" * 2001, ValueError),
])
def test_invalid_input_does_not_request(mock_post, monkeypatch, text, error_type):
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    with pytest.raises(error_type):
        run_generation(text)
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
        run_generation("学习Python")

    mock_post.assert_not_called()


def test_api_key_is_trimmed_before_request(mock_post, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "  offline-placeholder  ")
    response_with_content(mock_post, json.dumps({"title": "学习Python"}))

    candidate = run_generation("学习Python")

    assert candidate.title == "学习Python"
    mock_post.assert_awaited_once()
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer offline-placeholder"


@pytest.mark.parametrize("original", [
    httpx.ReadTimeout("timeout"), httpx.ConnectError("connection"),
])
def test_request_failure_preserves_cause(mock_post, original):
    mock_post.side_effect = original
    with pytest.raises(RuntimeError, match="模型服务请求失败") as caught:
        run_generation("test")
    assert caught.value.__cause__ is original


def test_http_error_does_not_parse_body(mock_post):
    response = Mock()
    request = httpx.Request("POST", "https://offline.invalid/chat/completions")
    original = httpx.HTTPStatusError(
        "status", request=request, response=httpx.Response(503, request=request),
    )
    response.raise_for_status.side_effect = original
    mock_post.return_value = response
    with pytest.raises(RuntimeError, match="模型服务请求失败") as caught:
        run_generation("test")
    assert caught.value.__cause__ is original
    response.json.assert_not_called()


def test_invalid_outer_json_preserves_cause(mock_post):
    response = Mock()
    original = json.JSONDecodeError("invalid", "<html>", 0)
    response.json.side_effect = original
    mock_post.return_value = response
    with pytest.raises(RuntimeError, match="模型服务响应不是合法JSON") as caught:
        run_generation("test")
    assert caught.value.__cause__ is original


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": None}])
def test_missing_response_structure(mock_post, body):
    response = Mock()
    response.json.return_value = body
    mock_post.return_value = response
    with pytest.raises(RuntimeError, match="模型服务响应缺少有效回答结构"):
        run_generation("test")


@pytest.mark.parametrize("finish_reason", [
    "length", "content_filter", "tool_calls", "insufficient_system_resource",
    "aborted", None, "unknown",
])
def test_unfinished_response_is_rejected_even_with_valid_json(mock_post, finish_reason):
    # 即使回答文本与候选字段合法，也必须先满足结束原因的约定。
    response_with_content(
        mock_post, json.dumps({"title": "test"}), finish_reason=finish_reason,
    )

    with pytest.raises(RuntimeError, match="模型回答未正常完成"):
        run_generation("test")


def test_truncated_response_is_rejected_before_json_parsing(mock_post, monkeypatch):
    response_with_content(mock_post, '{"title":', finish_reason="length")
    parse_answer = Mock()
    monkeypatch.setattr(llm_service.json, "loads", parse_answer)

    with pytest.raises(RuntimeError, match="模型回答未正常完成"):
        run_generation("test")

    # 不仅检查报错文本，还证明截断检查发生在内层JSON解析之前。
    parse_answer.assert_not_called()


def test_missing_finish_reason_is_a_structure_error(mock_post):
    response = Mock()
    response.json.return_value = {
        "choices": [{"message": {"content": '{"title": "test"}'}}],
    }
    mock_post.return_value = response

    with pytest.raises(RuntimeError, match="模型服务响应缺少有效回答结构") as caught:
        run_generation("test")

    assert isinstance(caught.value.__cause__, KeyError)


@pytest.mark.parametrize("content", [None, 123, "", "   "])
def test_invalid_answer_content(mock_post, content):
    response_with_content(mock_post, content)
    with pytest.raises(RuntimeError):
        run_generation("test")


def test_invalid_inner_json(mock_post):
    response_with_content(mock_post, "not JSON")
    with pytest.raises(RuntimeError, match="模型回答不是合法JSON") as caught:
        run_generation("test")
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
        run_generation("test")
    assert isinstance(caught.value.__cause__, ValidationError)


@pytest.mark.parametrize("tags, expected", [
    ([" Python ", "SQL", "python"], ["python", "sql"]),
    (["SQL", "Python", "sql"], ["sql", "python"]),
    ([], []),
])
def test_candidate_tags_are_normalized_without_reordering(mock_post, tags, expected):
    # 准备模型回答：让真实解析和候选校验处理这些标签，不发送网络请求。
    response_with_content(mock_post, json.dumps({"title": "test", "tags": tags}))

    result = run_generation("test")

    # 同时检查去空白、转小写、去重和保留首次出现的顺序；空列表允许。
    assert result.tags == expected


@pytest.mark.parametrize("tags", [[""], ["Python", "   "], ["\t\n"]])
def test_candidate_blank_tags_are_rejected_before_confirmation(mock_post, tags):
    response_with_content(mock_post, json.dumps({"title": "test", "tags": tags}))

    # 标签无效时不能返回候选对象；错误应沿既有异常处理链向外报告。
    with pytest.raises(RuntimeError, match="模型候选任务字段不合法") as caught:
        run_generation("test")

    assert isinstance(caught.value.__cause__, ValidationError)
    assert "tags must not be empty" in str(caught.value.__cause__)
