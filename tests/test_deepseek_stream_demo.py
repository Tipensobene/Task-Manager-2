"""流式示例的可重复离线验证，不读取真实密钥或连接网络。"""
import asyncio
import json
from unittest.mock import patch

import httpx
import pytest
from pydantic import ValidationError

from examples.llm import deepseek_stream_demo as demo

# 阅读顺序：event → wire → collect 是第一条纯内存路径；文件下半部测试真实 main。
# pytest 收集 test_ 函数；parametrize 为每组数据分别运行一次测试。
# 定义函数/handler 只是准备规则，调用它时才执行函数体。所有请求均离线模拟。

def event(content=None, reason=None, **delta):
    # 本文件的造数据函数，不是 SSE 内置方法。默认正文和结束原因为 None。
    # **delta 收集额外关键字，如 role="assistant"；返回式中的 **delta 再展开字典。
    return {"choices": [{"delta": {"content": content, **delta}, "finish_reason": reason}]}


def wire(*events):
    # *events 接收多个位置参数；字典转 JSON 文本，字符串原样保留以支持坏 JSON 和 [DONE]。
    # data: 标识数据字段；两个换行分别结束数据行、形成结束事件的空行。
    # join 拼成完整 SSE 文本，此处没有发送请求。
    return "".join("data: " + (item if isinstance(item, str) else json.dumps(item)) + "\n\n" for item in events)


def collect(text):
    # 输入完整 SSE 字符串；text= 提供内存正文，200 是状态码。构造 Response 不访问网络。
    response = httpx.Response(200, text=text)
    # collect_candidate(...) 产生协程；run 创建事件循环并执行它，返回候选或传播异常。
    # run 结束后关闭自己创建的事件循环。
    return asyncio.run(demo.collect_candidate(response))


def good_events():
    # 正文片段 → stop 生成结束原因 → [DONE] 协议结束标记。三个信息不是同一回事。
    return [event('{"title":"Learn Python"}'), event(reason="stop"), "[DONE]"]


def test_normal_and_metadata():
    # role/reasoning_content 不进入答案；三段 content 拼成 {"title":"Learn Python"}。
    # stop 后 event() 不应擦除已记录的结束原因。
    # 用量字典已是完整事件，不能用 event() 再包成普通候选正文。
    # [DONE] 也必须是独立标记；event("[DONE]") 会错误地把它放进 delta.content。
    candidate = collect(wire(
        event(role="assistant"), event(reasoning_content="not answer"),
        event('{"title":"Learn'), event(" "), event('Python"}'),
        event(reason="stop"), event(), {"choices": [], "usage": {}}, "[DONE]",
    ))
    # model_dump 把校验后的模型转成字典，检查正文和自动补齐的默认字段。
    assert candidate.model_dump() == dict(title="Learn Python", priority="normal", tags=[], description="")


@pytest.mark.parametrize("raw,message", [
    ("{", "事件不是合法JSON"),
    ("null", "事件必须是对象"),
    ("[]", "事件必须是对象"),
    ({}, "缺少必要结构"),
    ({"error": {}}, "错误事件"),
    ({"choices": None}, "choices必须是列表"),
    ({"choices": {}}, "choices必须是列表"),
    ({"choices": []}, "缺少候选选项"),
    ({"choices": [], "usage": None}, "缺少候选选项"),
    ({"choices": [None]}, "choice必须是对象"),
    ({"choices": [{}, {}]}, "只支持一个"),
    ({"choices": [{}]}, "缺少必要结构"),
    ({"choices": [{"delta": None}]}, "delta必须是对象"),
    ({"choices": [{"delta": []}]}, "delta必须是对象"),
    ({"choices": [{"delta": {}}]}, "缺少必要结构"),
    ({"choices": [{"index": True, "delta": {}, "finish_reason": None}]}, "索引不合法"),
    ({"choices": [{"index": 1, "delta": {}, "finish_reason": None}]}, "索引不合法"),
])
def test_bad_event(raw, message):
    # parametrize 上面的每对 raw/message 独立执行一次：造文本 → 真实解析器 → 抛错。
    # match 对实际异常消息做正则搜索；字符串本身不抛异常。无异常/类型错/消息错均失败。
    with pytest.raises(RuntimeError, match=message):
        collect(wire(raw, "[DONE]"))


@pytest.mark.parametrize("value", [0, 123, False, [], {}])
def test_bad_content(value):
    # 例如 123 → event(123) → delta.content=123 → wire → collect → 类型检查抛 RuntimeError。
    # “正文片段必须”匹配该异常的消息，不是匹配 value，也不是主动抛错。
    with pytest.raises(RuntimeError, match="正文片段必须"):
        collect(wire(event(value), "[DONE]"))


@pytest.mark.parametrize("value", [0, False, [], {}])
def test_bad_reason_type(value):
    # 验证结束原因必须为字符串或 None，不能把数字/容器静默忽略。
    with pytest.raises(RuntimeError, match="结束原因必须"):
        collect(wire(event(reason=value), "[DONE]"))


@pytest.mark.parametrize("reason", ["length", "content_filter", "tool_calls", "aborted", "unknown", ""])
def test_unsuccessful_reason(reason):
    # 即使正文 JSON 合法，也不能接受非 stop 的生成结束原因。
    with pytest.raises(RuntimeError, match="未正常完成"):
        collect(wire(event('{"title":"ok"}', reason), "[DONE]"))


@pytest.mark.parametrize("events,message", [
    ([event('{"title":"ok"}', "stop")], "流未正常结束"),
    ([event('{"title":"ok"}'), "[DONE]"], "未正常完成"),
    ([event(" ", "stop"), "[DONE]"], "回答不能为空"),
    ([event("not JSON", "stop"), "[DONE]"], "回答不是合法JSON"),
    ([event("{}", "stop"), "[DONE]"], "字段不合法"),
    ([event('{"title":"ok","priority":"urgent"}', "stop"), "[DONE]"], "字段不合法"),
    ([event("[]", "stop"), "[DONE]"], "字段不合法"),
    ([event('{"title":"ok"}', "stop"), event("extra"), "[DONE]"], "结束后仍返回正文"),
])
def test_completion_and_candidate_errors(events, message):
    # *events 展开列表为 wire 的多个参数；每组数据验证一个完成条件或候选内容错误。
    # 合法事件 JSON 不等于合法正文 JSON，合法正文 JSON 也不等于字段符合 TaskCandidate。
    with pytest.raises(RuntimeError, match=message):
        collect(wire(*events))


def test_multiline_sse_and_bom_comments():
    # \ufeff 是 Unicode BOM 字符；讲解中的 <BOM> 只是可视化标注，不是原始文本。
    # BOM 可标识编码；UTF-8 无大小端区别。解析器去掉首行 BOM 后得到 : heartbeat。
    # 以冒号开头的 SSE 注释/心跳被 continue 跳过；event/id 非本实验数据字段也跳过。
    # continue 进入下一行，不退出整个循环。\r\n 是换行，两条 data 的值用换行合并。
    # 最后的空行才让解析器派发合并后的事件，然后追加一个完整 [DONE] 事件。
    text = '\ufeff: heartbeat\r\nevent: message\r\nid: 1\r\ndata: {"choices":\r\ndata: [{"delta":{"content":"{\\"title\\":\\"ok\\"}"},"finish_reason":"stop"}]}\r\n\r\n'
    assert collect(text + wire("[DONE]")).title == "ok"


def test_unterminated_event_is_not_dispatched():
    # [:-1] 去掉已有 DONE；手动追加的 data: [DONE] 没有结尾空行。
    # HTTPX 在 EOF 可以交出最后一行，但业务解析器只把它放进 data_lines。
    # 没遇到空行就没有 yield 事件，收集器尚未收到 DONE。EOF 时缓存非空，必须拒绝。
    with pytest.raises(RuntimeError, match="事件未完整结束"):
        collect(wire(*good_events()[:-1]) + "data: [DONE]")


def test_limits(monkeypatch):
    # pytest 按形参名提供 monkeypatch fixture。setattr 临时改属性，默认要求属性存在。
    # 先缩小单事件限制，再恢复它并缩小正文限制，分别触发两种错误；测试后自动恢复。
    monkeypatch.setattr(demo, "MAX_EVENT_CHARS", 5)
    with pytest.raises(RuntimeError, match="事件过大"):
        collect(wire(*good_events()))
    monkeypatch.setattr(demo, "MAX_EVENT_CHARS", 65536)
    monkeypatch.setattr(demo, "MAX_ANSWER_CHARS", 5)
    with pytest.raises(RuntimeError, match="回答过长"):
        collect(wire(*good_events()))


@pytest.mark.parametrize("body,cause", [("not JSON", json.JSONDecodeError), ("{}", ValidationError)])
def test_exception_chain(body, cause):
    # caught 是异常记录，caught.value 是捕获的 RuntimeError。
    # raise ... from error 将原异常存进 __cause__；检查它是 JSON 错误还是字段校验错误。
    with pytest.raises(RuntimeError) as caught:
        collect(wire(event(body, "stop"), "[DONE]"))
    assert isinstance(caught.value.__cause__, cause)


class OfflineStream(httpx.AsyncByteStream):
    # 实现 HTTPX 异步字节流接口；实例本身不建立连接。__aiter__ 供读取，aclose 供清理。
    def __init__(self, mode):
        self.mode = mode
        self.closed = False

    async def __aiter__(self):
        # 含 yield 的 async def 是异步生成器，HTTPX 请求下一块时才推进执行。
        # 入口：业务 aiter_lines → aiter_text → aiter_bytes → aiter_raw →
        # HTTPX 的 BoundAsyncStream 包装器 → 本实例的 __aiter__。
        # 故意拆开字节，验证HTTPX还原行后再交给SSE解析器。
        raw = wire(*good_events()).encode()
        # encode 默认 UTF-8，str 变 bytes；前15字节为 b'data: {"choices'，没有完整行。
        yield raw[:15]
        # 再次取数据时从 yield 后继续；read 模式立即抛异常，经读取链传回 main。
        if self.mode == "read":
            raise httpx.ReadTimeout("offline")
        if self.mode in ("deadline", "cancel"):
            # cancel 模拟外部取消；deadline 等待1秒，让业务的0.01秒总时限触发。
            if self.mode == "cancel":
                raise asyncio.CancelledError()
            await asyncio.sleep(1)
        yield raw[15:]

    async def aclose(self):
        # 调用者：退出 client.stream 上下文 → Response.aclose → 包装流.aclose → 本方法。
        # 这里只设置标志，后面的断言据此证明关闭发生；没有真实套接字需要关闭。
        self.closed = True


@pytest.mark.parametrize("mode", ["normal", "connect", "status", "media", "read", "deadline", "cancel"])
def test_main_transport_and_cleanup(monkeypatch, capsys, mode):
    # mode="read" 的完整路线（不是把所有模式都改成 read）：
    # 1. pytest 注入本轮 mode 和两个 fixture；创建流、登记 handler、创建客户端并替换入口。
    # 2. asyncio.run(main()) → main 构造真实 Request → MockTransport 调 handler。
    # 3. handler 返回 200/SSE Response → main 检查状态和媒体类型 → collect_candidate。
    # 4. HTTPX 读取进入 OfflineStream：先15字节，再抛 ReadTimeout；尚未形成完整事件。
    # 5. 异常退出响应上下文关闭流，再退出客户端上下文；main 转为 RuntimeError from error。
    # 6. pytest.raises 捕获 → 检查原因/输出/关闭 → 测试结束，pytest 恢复替换与环境变量。
    stream = OfflineStream(mode)
    def handler(request):
        # 定义时不执行；真正发请求时 MockTransport 调用。读取外层本轮的 mode 和 stream。
        # request 是业务构造的 httpx.Request；content 是 bytes，loads 解析为 payload 字典。
        payload = json.loads(request.content)
        assert payload["stream"] is True
        assert request.headers["authorization"] == "Bearer offline-placeholder"
        if mode == "connect":
            # 此处直接抛错，还没创建并返回 Response，stream 也还没交给响应管理。
            raise httpx.ConnectError("offline", request=request)
        return httpx.Response(
            # 三个参数分别指定状态、响应头、正文来源；stream 不代表整个 Response 的来源。
            # status 模式用503，其他用200；media 模式故意声明普通JSON，其他声明SSE。
            # main 检查头的标准：取 content-type，split(";", 1)[0]（最多切一次取前段），
            # strip/lower 后应为 text/event-stream。只验证声明，正文另由解析器验证。
            503 if mode == "status" else 200,
            headers={"content-type": "application/json" if mode == "media" else "text/event-stream; charset=utf-8"},
            stream=stream,
            # 左边为参数名，右边为 OfflineStream 实例，HTTPX 从它逐块取正文 bytes。
            # 与请求 payload 中要求服务端流式返回的 "stream": True 不是同一设置。
        )
    # AsyncClient 是类，client 是真实实例；transport 指定执行请求的组件。
    # 通常这个组件负责联网；这里用 MockTransport 保存 handler 回调来代替网络。
    # 实际调用链：AsyncClient._send_single_request → transport.handle_async_request →
    # MockTransport 内部 self.handler(request) → 上面 handler → Response。
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    # 仅设置临时进程环境变量，不修改 .env；测试结束恢复原值或移除临时值。
    monkeypatch.setenv("DEEPSEEK_API_KEY", "offline-placeholder")
    # 必须先创建 client，再替换构造入口。lambda 是接收关键字参数、返回现有 client 的函数。
    # main 调 AsyncClient(timeout=timeout) 时，timeout 被 **kwargs 接收，得到上面的实例。
    # 后续 async with/stream 都是真实执行，只是这个实例已经配置了 MockTransport。
    # demo.httpx 与这里的 httpx 是同一模块，替换属性也会影响这个模块的其他别名。
    # kwargs 在此被忽略，因此这个测试不证明 main 传入的 HTTPX timeout 参数效果。
    monkeypatch.setattr(demo.httpx, "AsyncClient", lambda **kwargs: client)
    if mode == "deadline":
        monkeypatch.setattr(demo, "STREAM_TIMEOUT_SECONDS", 0.01)
    if mode == "normal":
        asyncio.run(demo.main())
        assert "'title': 'Learn Python'" in capsys.readouterr().out
        # capsys 捕获标准输出；readouterr 返回带 out/err 的结果，并清空已捕获的缓冲。
    else:
        # 保留源码的动态选择：cancel 期待 CancelledError，其余才期待 RuntimeError。
        # 不能把 read 场景下的具体取值，冒充所有场景的原始代码。
        error_type = asyncio.CancelledError if mode == "cancel" else RuntimeError
        with pytest.raises(error_type) as caught:
            asyncio.run(demo.main())
        # raises 捕获预期异常后，继续的是外层测试；main 已退出，不从出错语句后继续。
        if mode in ("connect", "status", "read"):
            # ConnectError/HTTPStatusError/ReadTimeout 都继承 HTTPError；检查原始原因保留。
            assert isinstance(caught.value.__cause__, httpx.HTTPError)
        if mode == "deadline":
            # 总时限产生 TimeoutError，不是 HTTPX 的 HTTPError。
            assert isinstance(caught.value.__cause__, TimeoutError)
        assert "'title': 'Learn Python'" not in capsys.readouterr().out
        # 允许诊断/部分正文输出，但不能打印成功的最终候选字典。
    assert client.is_closed
    # 上面检查真实客户端退出状态；下面检查响应是否关闭它持有的正文流。
    if mode != "connect":
        # connect 没返回 Response，未使用的内存流不归响应管理，因此不要求 closed=True。
        # 其他模式已返回响应，即使状态/媒体类型/读取失败，也必须退出上下文关闭它。
        assert stream.closed


def test_missing_key_does_not_create_client(monkeypatch):
    # 空白密钥经 strip 为空；应在创建客户端之前拒绝。
    monkeypatch.setenv("DEEPSEEK_API_KEY", " ")
    with patch.object(demo.httpx, "AsyncClient") as factory:
        # patch.object 临时换成 Mock，as factory 取得这个 Mock；退出 with 自动恢复属性。
        # 与上面返回真实 client 的 lambda 不同，这里仅证明入口从未被调用。
        with pytest.raises(RuntimeError, match="未配置API密钥"):
            asyncio.run(demo.main())
        factory.assert_not_called()
        # 没创建客户端就不可能进入请求流程；monkeypatch 在测试清理时恢复环境变量。
