"""离线运行演示入口，确认它会等待候选，再打印结果。"""

import runpy
from unittest.mock import AsyncMock

import llm_service
from task_candidate import TaskCandidate


def test_demo_entrypoint_awaits_generation(monkeypatch, capsys):
    candidate = TaskCandidate(title="offline-demo")
    generate = AsyncMock(return_value=candidate)
    pending = []

    def tracked_generation(*args, **kwargs):
        coroutine = generate(*args, **kwargs)
        pending.append(coroutine)
        return coroutine

    monkeypatch.setattr(llm_service, "generate_candidate", tracked_generation)
    try:
        runpy.run_module("examples.llm.deepseek_demo", run_name="__main__")
    finally:
        # 入口漏写await时也清理测试创建的协程，避免额外的未等待警告。
        for coroutine in pending:
            coroutine.close()

    generate.assert_awaited_once_with(
        "高优先级学习SQLAlchemy，重点理解Session，标签是Python。"
    )
    output = capsys.readouterr().out
    assert "offline-demo" in output
    assert "'priority': 'normal'" in output
