"""候选输入与路由测试：使用独立应用和模拟生成函数，无外部网络或数据库操作。"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

import ai_routes
from ai_routes import TaskCandidateRequest
from task_candidate import TaskCandidate


@pytest.fixture
def mock_generate(monkeypatch):
    generator = AsyncMock()
    # 替换路由实际调用的生成函数；HTTP测试不会进入真实模型请求。
    monkeypatch.setattr(ai_routes.llm_service, "generate_candidate", generator)
    return generator


@pytest.fixture
def ai_client(mock_generate):
    # 用独立应用装载真实路由，避免导入正式应用中的数据库依赖。
    app = FastAPI()
    app.include_router(ai_routes.ai_router)
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize("text, expected", [
    ("  学习Python  ", "学习Python"),
    ("x" * 2000, "x" * 2000),
    ("  " + "x" * 2000 + "  ", "x" * 2000),
])
def test_candidate_request_accepts_cleaned_text(text, expected):
    # 输入字典交给真实Pydantic模型，检查清理结果及清理后的长度边界。
    request = TaskCandidateRequest.model_validate({"text": text})
    assert request.text == expected


@pytest.mark.parametrize("data", [
    {},
    {"text": None},
    {"text": 123},
    {"text": ""},
    {"text": " \t\n "},
    {"text": "x" * 2001},
    {"text": "学习Python", "id": 1},
])
def test_candidate_request_rejects_invalid_input(data):
    # 每组只改变一种输入条件；此处直接调用模型，预期异常为ValidationError。
    with pytest.raises(ValidationError):
        TaskCandidateRequest.model_validate(data)


def test_candidate_route_returns_candidate(ai_client, mock_generate):
    expected = {
        "title": "阅读Python文档",
        "priority": "normal",
        "tags": ["python"],
        "description": "理解基础语法",
    }
    mock_generate.return_value = TaskCandidate.model_validate(expected)

    # 请求经由真实FastAPI校验、真实路由和响应序列化；只替换生成函数。
    response = ai_client.post("/ai/task-candidate", json={"text": "  学习Python  "})

    assert response.status_code == 200
    assert response.json() == expected
    mock_generate.assert_awaited_once_with("学习Python")


@pytest.mark.parametrize("data", [
    {},
    {"text": None},
    {"text": 123},
    {"text": ""},
    {"text": " \t\n "},
    {"text": "x" * 2001},
    {"text": "学习Python", "id": 1},
])
def test_candidate_route_rejects_input_without_generation(ai_client, mock_generate, data):
    response = ai_client.post("/ai/task-candidate", json=data)

    # 这层检查HTTP状态以及是否阻止调用生成函数，补充上面的模型级测试。
    assert response.status_code == 422
    mock_generate.assert_not_called()


def test_candidate_route_converts_generation_failure(ai_client, mock_generate):
    # 虚构内部错误用于检查响应边界，不使用真实凭据或发送模型请求。
    original = RuntimeError("internal-model-failure-for-test")
    mock_generate.side_effect = original

    # 请求经过真实路由；生成函数抛错后，FastAPI将HTTPException转换为响应。
    response = ai_client.post("/ai/task-candidate", json={"text": "  学习Python  "})

    assert response.status_code == 502
    assert response.json() == {"detail": "候选任务生成失败，请稍后重试"}
    assert str(original) not in response.text
    mock_generate.assert_awaited_once_with("学习Python")


def test_candidate_route_preserves_generation_failure_cause(mock_generate):
    original = RuntimeError("internal-model-failure-for-test")
    mock_generate.side_effect = original
    request = TaskCandidateRequest(text="学习Python")

    # 直接调用路由函数，在FastAPI处理异常之前捕获Python异常对象。
    # HTTP响应JSON不包含__cause__，因此上一项HTTP测试无法检查这条因果关系。
    with pytest.raises(HTTPException) as caught:
        asyncio.run(ai_routes.generate_task_candidate(request))

    assert caught.value.status_code == 502
    assert caught.value.detail == "候选任务生成失败，请稍后重试"
    assert caught.value.__cause__ is original
    mock_generate.assert_awaited_once_with("学习Python")
