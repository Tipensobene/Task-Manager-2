"""离线验证检索流程：资料在临时目录，向量和回答由模拟函数提供。"""

import asyncio
import json
import runpy
import sys
from unittest.mock import AsyncMock

import pytest

from examples.rag import answer_demo, embedding_demo, semantic_search_demo as demo


@pytest.mark.parametrize("text, expected", [
    ("", []),
    (" \n\n", []),
    ("a\nb", [("a\nb", 1, 2)]),
    ("a\n\n", [("a", 1, 1)]),
    ("\n a \n\n\nb\nc", [("a", 2, 2), ("b\nc", 5, 6)]),
    ("a\r\nb\r\n\r\nc\r\n", [("a\nb", 1, 2), ("c", 4, 4)]),
])
def test_split_paragraphs(text, expected):
    result = demo.split_paragraphs(text, "notes.txt")
    assert result == [
        {"text": body, "source": "notes.txt", "start_line": start, "end_line": end}
        for body, start, end in expected
    ]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    # 相对路径现在指向临时目录，不会覆盖学习者的笔记或向量缓存。
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "examples" / "rag"
    folder.mkdir(parents=True)
    notes = folder / "notes.txt"
    notes.write_text("first\n\nsecond\nexplanation\n\nthird\n", encoding="utf-8")
    return notes, folder / "notes_vectors.json"


@pytest.fixture
def services(monkeypatch):
    # 人工向量让排名可预测：second > first > third。
    vectors = {"first": [1, 1], "second\nexplanation": [1, 0], "third": [0, 1]}

    async def embed(text):
        pair = vectors.get(text, [1, 0])
        return pair + [0] * 1022

    embedding = AsyncMock(side_effect=embed)
    answer = AsyncMock(return_value="离线回答[资料1]")
    monkeypatch.setattr(demo, "get_embedding", embedding)
    monkeypatch.setattr(demo, "generate_answer", answer)
    return embedding, answer


def test_build_reuse_and_forward_question(workspace, services, capsys):
    notes, cache = workspace
    embedding, answer = services
    asyncio.run(demo.main("question one"))
    assert embedding.await_count == 4  # 三条文档加一个问题。
    data = json.loads(cache.read_text(encoding="utf-8"))
    assert data["source_text"] == notes.read_text(encoding="utf-8")
    assert [(c["start_line"], c["end_line"]) for c in data["candidates"]] == [(1, 1), (3, 4), (6, 6)]
    assert data["chunking"] == "paragraph-v1"
    assert embedding.await_args_list[1].args == ("second\nexplanation",)
    question, context = answer.await_args.args
    assert question == "question one"
    assert context.index("second") < context.index("first")
    assert "third" not in context  # 确认只把前两条交给回答函数。
    assert "[资料1]" in context and "行号：3-4" in context and "second\nexplanation" in context
    assert str(notes.relative_to(notes.parents[2])) in context
    original = cache.read_bytes()
    embedding.reset_mock()
    answer.reset_mock()
    asyncio.run(demo.main("question two"))
    embedding.assert_awaited_once_with("question two")
    assert answer.await_args.args[0] == "question two"
    assert cache.read_bytes() == original
    assert "复用文档向量缓存" in capsys.readouterr().out


@pytest.mark.parametrize("changed", ["source_text", "model", "dimensions", "source", "chunking", "missing_chunking"])
def test_invalid_cache_rebuilds(workspace, services, changed):
    notes, cache = workspace
    embedding, _ = services
    asyncio.run(demo.main("question"))
    if changed == "source_text":
        notes.write_text("first\nsecond\n", encoding="utf-8")
    else:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if changed == "missing_chunking":
            data.pop("chunking")
        else:
            data[changed] = 2 if changed == "dimensions" else "outdated"
        cache.write_text(json.dumps(data), encoding="utf-8")
    embedding.reset_mock()
    asyncio.run(demo.main("question"))
    expected = 2 if changed == "source_text" else 4
    assert embedding.await_count == expected
    rebuilt = json.loads(cache.read_text(encoding="utf-8"))
    assert rebuilt["source_text"] == notes.read_text(encoding="utf-8")
    assert rebuilt["model"] == "text-embedding-v4"
    assert rebuilt["dimensions"] == 1024


@pytest.mark.parametrize("arguments, code", [(["--help"], 0), ([], 2)])
def test_cli_early_exit(monkeypatch, arguments, code):
    embedding = AsyncMock()
    monkeypatch.setattr(embedding_demo, "get_embedding", embedding)
    monkeypatch.setattr(sys, "argv", ["semantic_search_demo", *arguments])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(demo.__file__, run_name="__main__")
    assert caught.value.code == code
    embedding.assert_not_called()


def test_rank_candidates_returns_list_without_printing(capsys):
    candidates = [{"vector": [0, 1]}, {"vector": [1, 0]}, {"vector": [1, 1]}]
    result = demo.rank_candidates([1, 0], candidates)
    assert [item["candidate"] for item in result] == [candidates[1], candidates[2]]
    assert len(demo.rank_candidates([1, 0], candidates, 1)) == 1
    assert demo.rank_candidates([1, 0], []) == []
    assert capsys.readouterr().out == ""


def test_empty_notes_do_not_generate_answer(workspace, services):
    notes, _ = workspace
    _, answer = services
    notes.write_text("", encoding="utf-8")
    asyncio.run(demo.main("question"))
    answer.assert_not_awaited()


@pytest.mark.parametrize("options, count", [([], 2), (["--top-k", "1"], 1), (["--top-k", "2"], 2), (["--top-k", "3"], 3)])
def test_cli_question_reaches_services(workspace, services, monkeypatch, options, count):
    embedding, answer = services
    # runpy执行入口时重新从来源模块导入函数，所以替换来源模块中的名称。
    monkeypatch.setattr(embedding_demo, "get_embedding", embedding)
    monkeypatch.setattr(answer_demo, "generate_answer", answer)
    monkeypatch.setattr(sys, "argv", ["semantic_search_demo", "question with spaces", *options])
    runpy.run_path(demo.__file__, run_name="__main__")
    assert embedding.await_args.args == ("question with spaces",)
    assert answer.await_args.args[0] == "question with spaces"
    assert answer.await_args.args[1].count("[资料") == count


@pytest.mark.parametrize("value", ["0", "4", "abc"])
def test_cli_rejects_invalid_top_k(monkeypatch, value):
    embedding = AsyncMock()
    answer = AsyncMock()
    monkeypatch.setattr(embedding_demo, "get_embedding", embedding)
    monkeypatch.setattr(answer_demo, "generate_answer", answer)
    monkeypatch.setattr(sys, "argv", ["demo", "question", "--top-k", value])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(demo.__file__, run_name="__main__")
    assert caught.value.code == 2
    embedding.assert_not_called()
    answer.assert_not_called()
