# 流式候选示例：完整执行流程与新增代码逐行讲解

更新日期：2026-10-27。对应 `deepseek_stream_demo.py` 当前版本。业务边界一次补齐，后续不再逐项布置同类补丁。

## 先看一条请求怎样流转

在项目根目录运行 `python -m examples.llm.deepseek_stream_demo`，模块先定义函数，再由底部 `asyncio.run(main())` 执行入口。main准备密钥、提示词与请求体，进入客户端及响应上下文。HTTPX提供文本行；iter_sse_data组装事件；parse_stream_event解析外层JSON并检查结构；collect_candidate收集正文、检查完成状态、解析任务JSON，调用根目录task_candidate.py里的TaskCandidate校验。最终main打印model_dump字典。正式llm_service.py和FastAPI路由未参与这条实验链。

例如两条正文依次为 `{"title":"学习` 和 `Python"}`：每条首先藏在外层事件的delta.content中；事件解析后保存到received_chunks；收到stop和[DONE]后拼成 `{"title":"学习Python"}`，最终候选补齐normal、[]、空备注。reasoning_content及usage不加入正文。任一检查失败会抛出异常，退出已经进入的资源上下文，不打印最终候选。

## 方法输入输出

| 函数 | 输入 | 调用方式 | 输出 |
|---|---|---|---|
| iter_sse_data | HTTPX Response | async for | 逐事件提供str，属于异步生成器 |
| parse_stream_event | 单个事件的数据字符串 | 普通调用 | (content, reason)元组，或纯用量事件的None |
| collect_candidate | HTTPX Response | await | 校验通过的TaskCandidate |
| main | 无参数 | asyncio.run入口 | 打印结果；隐式返回None |

三个辅助函数都没有可选参数和默认参数。大小与总时限由顶部常量配置，不是供应商上限。

## 按源码逐行解释

下表涵盖本轮新增或重新组织的有效语句；原有请求配置和入口不重复罗列，空行只用于排版。点击行号可回到源码。

| 行号 | 代码 | 本行作用 |
|---|---|---|
| [10](deepseek_stream_demo.py#L10) | `# 应用层保护值，不是模型平台的限制。` | 说明下列限制属于我们的示例策略，可以按业务调整，不是DeepSeek官方上限。 |
| [11](deepseek_stream_demo.py#L11) | `MAX_EVENT_CHARS = 65536` | 单个事件累计data文本最多约64K字符，避免无限累计同一事件。 |
| [12](deepseek_stream_demo.py#L12) | `MAX_ANSWER_CHARS = 65536` | 最终回答累计最多64K字符，超过即拒绝，不继续缓存。 |
| [13](deepseek_stream_demo.py#L13) | `STREAM_TIMEOUT_SECONDS = 120` | 整段请求和收集最多120秒，与单次网络等待超时不同。 |
| [16](deepseek_stream_demo.py#L16) | `async def iter_sse_data(response):` | 定义异步生成器：输入HTTPX Response，逐次交出完整事件的数据字符串。调用本身不执行读取，要由async for推进。 |
| [17](deepseek_stream_demo.py#L17) | `"""按空行组装SSE事件；同一事件的多条data行用换行连接。"""` | 函数说明，明确这里只处理SSE的data载荷。 |
| [18](deepseek_stream_demo.py#L18) | `data_lines = []` | 保存当前事件的各条data行，列表属于本次函数调用。 |
| [19](deepseek_stream_demo.py#L19) | `event_size = 0` | 记录当前事件累计字符数。 |
| [20](deepseek_stream_demo.py#L20) | `first_line = True` | 记录是否还在处理响应的第一行。 |
| [21](deepseek_stream_demo.py#L21) | `async for line in response.aiter_lines():` | 异步读取文本行；HTTPX负责从可能被拆开的网络字节还原文本行。 |
| [22](deepseek_stream_demo.py#L22) | `if first_line:` | 仅第一行需要处理可选的文本起始标记。 |
| [23](deepseek_stream_demo.py#L23) | `line = line.removeprefix("\ufeff")` | 移除开头的Unicode BOM；它不是事件正文。 |
| [24](deepseek_stream_demo.py#L24) | `first_line = False` | 后面的行不再进行起始标记处理。 |
| [25](deepseek_stream_demo.py#L25) | `if line == "":` | 空行表示当前SSE事件结束，而不是一律无条件忽略。 |
| [26](deepseek_stream_demo.py#L26) | `if data_lines:` | 只有收集过data字段，才有事件数据可交出。 |
| [27](deepseek_stream_demo.py#L27) | `yield "\n".join(data_lines)` | 同一事件多条data值用换行拼接，yield给collect_candidate；等待消费方索取下一项后才继续执行。 |
| [28](deepseek_stream_demo.py#L28) | `data_lines = []` | 清空当前事件的缓存，准备下一事件。 |
| [29](deepseek_stream_demo.py#L29) | `event_size = 0` | 重新开始计算下一事件的大小。 |
| [30](deepseek_stream_demo.py#L30) | `continue` | 本轮空行已经处理完，直接读取下一行。 |
| [31](deepseek_stream_demo.py#L31) | `if line.startswith(":"):` | 冒号开头是SSE注释，可能被服务端用作心跳。 |
| [32](deepseek_stream_demo.py#L32) | `continue  # SSE注释/心跳没有候选内容。` | 跳过注释，不把它加入任务正文。 |
| [33](deepseek_stream_demo.py#L33) | `field, _, value = line.partition(":")` | partition按第一个冒号返回三元组。例如data: hello得到data、冒号、空格hello；_接收暂不用的分隔符。无冒号时后两项为空。 |
| [34](deepseek_stream_demo.py#L34) | `if field != "data":` | 检查字段名是否恰好为data。 |
| [35](deepseek_stream_demo.py#L35) | `continue  # 本次单次请求不使用event/id/retry等字段。` | 本次单次请求不处理事件名、事件ID或重连间隔；不实现自动重连。 |
| [36](deepseek_stream_demo.py#L36) | `value = value.removeprefix(" ")  # 协议只移除冒号后的一个空格。` | 只删除data值开头的一个空格，遵循SSE字段格式；不用strip误删其他数据。 |
| [37](deepseek_stream_demo.py#L37) | `event_size += len(value) + 1` | 累计值的字符数并计入行分隔开销。 |
| [38](deepseek_stream_demo.py#L38) | `if event_size > MAX_EVENT_CHARS:` | 检查当前事件是否超出应用限制。 |
| [39](deepseek_stream_demo.py#L39) | `raise RuntimeError("模型流式事件过大")` | 超限时立即停止，不把事件交给JSON解析。 |
| [40](deepseek_stream_demo.py#L40) | `data_lines.append(value)` | 把这一条data值保存到当前事件列表。 |
| [41](deepseek_stream_demo.py#L41) | `if data_lines:` | 网络迭代结束后还有数据，表示最后事件没以空行结束。 |
| [42](deepseek_stream_demo.py#L42) | `raise RuntimeError("模型流式事件未完整结束")` | 拒绝不完整事件；即使残留文本看起来是[DONE]也不能冒充完整事件。 |
| [45](deepseek_stream_demo.py#L45) | `def parse_stream_event(event_text):` | 普通同步函数，只解析和检查内存中的一个事件，不等待网络。 |
| [46](deepseek_stream_demo.py#L46) | `"""返回(content, finish_reason)；纯用量事件返回None。"""` | 成功返回二元组；兼容的纯用量事件用None表示无需收集。 |
| [47](deepseek_stream_demo.py#L47) | `try:` | 开始仅针对外层JSON解析的异常处理。 |
| [48](deepseek_stream_demo.py#L48) | `event = json.loads(event_text)` | 事件文本转成Python数据；合法JSON也可能得到列表、数字或None。 |
| [49](deepseek_stream_demo.py#L49) | `except json.JSONDecodeError as error:` | 捕获JSON语法错误。 |
| [50](deepseek_stream_demo.py#L50) | `raise RuntimeError("模型流式事件不是合法JSON") from error` | 转成事件层错误，并保留JSONDecodeError作为原因。 |
| [51](deepseek_stream_demo.py#L51) | `if not isinstance(event, dict):` | 要求事件顶层是字典，而不仅是任意合法JSON。 |
| [52](deepseek_stream_demo.py#L52) | `raise RuntimeError("模型流式事件必须是对象")` | 拒绝顶层null、列表、字符串、数字等。 |
| [53](deepseek_stream_demo.py#L53) | `if "error" in event:` | 检测服务端在流中返回的错误载荷。 |
| [54](deepseek_stream_demo.py#L54) | `raise RuntimeError("模型服务返回流式错误事件")` | 直接失败，不回显可能包含内部信息的完整错误内容。 |
| [55](deepseek_stream_demo.py#L55) | `try:` | 下面需要访问必要键，对缺键统一解释。 |
| [56](deepseek_stream_demo.py#L56) | `choices = event["choices"]` | 读取choices；缺键产生KeyError。 |
| [57](deepseek_stream_demo.py#L57) | `if not isinstance(choices, list):` | 要求choices为列表。 |
| [58](deepseek_stream_demo.py#L58) | `raise RuntimeError("模型流式事件的choices必须是列表")` | 拒绝None、字典等错误类型，避免后续索引误用。 |
| [59](deepseek_stream_demo.py#L59) | `if not choices and isinstance(event.get("usage"), dict):` | 仅在choices为空且usage为字典时，识别为可兼容的纯用量事件。 |
| [60](deepseek_stream_demo.py#L60) | `return None  # 兼容纯用量事件，不将它当作正文或完成标记。` | 返回None让收集器跳过；它不能设置stop或[DONE]。这是兼容分支，不代表当前平台一定发送这种事件。 |
| [61](deepseek_stream_demo.py#L61) | `if not choices:` | 没有可用候选，也不满足用量事件规则。 |
| [62](deepseek_stream_demo.py#L62) | `raise RuntimeError("模型流式事件缺少候选选项")` | 明确报告缺少选项，不再依赖访问空列表产生IndexError。 |
| [63](deepseek_stream_demo.py#L63) | `if len(choices) != 1:` | 当前请求只处理一条任务，不能把多个模型选项混在一起。 |
| [64](deepseek_stream_demo.py#L64) | `raise RuntimeError("当前示例只支持一个候选选项")` | 拒绝多个候选选项。 |
| [65](deepseek_stream_demo.py#L65) | `choice = choices[0]` | 经过非空且单项检查后，安全取第一个元素。 |
| [66](deepseek_stream_demo.py#L66) | `if not isinstance(choice, dict):` | 检查这个元素是否为字典。 |
| [67](deepseek_stream_demo.py#L67) | `raise RuntimeError("模型流式事件的choice必须是对象")` | 拒绝列表中的null、数字等。 |
| [68](deepseek_stream_demo.py#L68) | `index = choice.get("index", 0)` | 读取可选索引；简化样本未提供时按0处理。 |
| [69](deepseek_stream_demo.py#L69) | `if type(index) is not int or index != 0:` | 严格要求整数0；不用isinstance(index,int)，因为Python的bool也是int的子类，而True不应作为候选索引。 |
| [70](deepseek_stream_demo.py#L70) | `raise RuntimeError("模型流式事件的候选索引不合法")` | 拒绝其他索引及类型。 |
| [71](deepseek_stream_demo.py#L71) | `delta = choice["delta"]` | 读取必要的delta字段。 |
| [72](deepseek_stream_demo.py#L72) | `if not isinstance(delta, dict):` | 要求delta是字典。 |
| [73](deepseek_stream_demo.py#L73) | `raise RuntimeError("模型流式事件的delta必须是对象")` | 拒绝不支持.get的类型。 |
| [74](deepseek_stream_demo.py#L74) | `content = delta.get("content")` | 正文可选，缺省得到None；推理文本没有被读取到正文中。 |
| [75](deepseek_stream_demo.py#L75) | `reason = choice["finish_reason"]` | 读取必要结束原因；生成中可以为None，但键应存在。 |
| [76](deepseek_stream_demo.py#L76) | `except KeyError as error:` | 捕获上述必要键访问时产生的KeyError。 |
| [77](deepseek_stream_demo.py#L77) | `raise RuntimeError("模型流式事件缺少必要结构") from error` | 转换缺结构错误，并保留具体缺失键的异常原因。 |
| [78](deepseek_stream_demo.py#L78) | `if content is not None and not isinstance(content, str):` | None允许；其他值必须是字符串，包括空字符串也是合法类型。 |
| [79](deepseek_stream_demo.py#L79) | `raise RuntimeError("模型流式正文片段必须是字符串或null")` | 拒绝0、False、列表等，不强制转成字符串。 |
| [80](deepseek_stream_demo.py#L80) | `if reason is not None and not isinstance(reason, str):` | 结束原因同样只允许字符串或None。 |
| [81](deepseek_stream_demo.py#L81) | `raise RuntimeError("模型流式结束原因必须是字符串或null")` | 拒绝错误类型；具体是不是stop由收集器判断。 |
| [82](deepseek_stream_demo.py#L82) | `return content, reason` | 返回二元组，例如('{"title":"学习', None)。 |
| [85](deepseek_stream_demo.py#L85) | `async def collect_candidate(response):` | 定义普通协程：持续接收事件，完成后返回一个TaskCandidate；没有yield，需await。 |
| [86](deepseek_stream_demo.py#L86) | `"""只在流完整结束、正文及字段均合法时返回候选。"""` | 说明候选返回的前置条件。 |
| [87](deepseek_stream_demo.py#L87) | `received_chunks = []` | 存放已验证类型的正文片段，不存推理、事件包装或[DONE]。 |
| [88](deepseek_stream_demo.py#L88) | `answer_size = 0` | 初始化整份回答的字符计数。 |
| [89](deepseek_stream_demo.py#L89) | `stream_ended = False` | 开始尚未收到流结束标记。 |
| [90](deepseek_stream_demo.py#L90) | `finish_reason = None` | 开始尚未收到生成结束原因。 |
| [91](deepseek_stream_demo.py#L91) | `async for event_text in iter_sse_data(response):` | 消费iter_sse_data交出的完整事件文本；接收等待仍由下层HTTPX执行。 |
| [92](deepseek_stream_demo.py#L92) | `if event_text.strip() == "[DONE]":` | 先识别特殊标记；不能把[DONE]交给JSON解析。这里strip用于标记比较，不修改正文片段。 |
| [93](deepseek_stream_demo.py#L93) | `stream_ended = True` | 记录流确实结束。 |
| [94](deepseek_stream_demo.py#L94) | `break` | 停止继续索取事件；响应资源由main里的async with负责关闭。 |
| [95](deepseek_stream_demo.py#L95) | `parsed = parse_stream_event(event_text)` | 普通事件交给同步解析函数；这里只是普通函数调用，不创建新线程。 |
| [96](deepseek_stream_demo.py#L96) | `if parsed is None:` | 识别纯用量事件的返回约定。 |
| [97](deepseek_stream_demo.py#L97) | `continue` | 不修改正文或结束状态，读取下一事件。 |
| [98](deepseek_stream_demo.py#L98) | `content, current_reason = parsed` | 元组解包，将两个返回值分别保存到变量。 |
| [99](deepseek_stream_demo.py#L99) | `if finish_reason is not None and content:` | 如果之前已经出现生成结束原因，本条事件不得再追加非空正文。 |
| [100](deepseek_stream_demo.py#L100) | `raise RuntimeError("模型结束后仍返回正文")` | 拒绝结束后继续输出正文的异常顺序。 |
| [101](deepseek_stream_demo.py#L101) | `if current_reason is not None:` | 本条有明确结束原因时才更新状态。 |
| [102](deepseek_stream_demo.py#L102) | `if current_reason != "stop":` | 单条候选实验只接受stop；length等其他值均失败。 |
| [103](deepseek_stream_demo.py#L103) | `raise RuntimeError("模型生成未正常完成，不能生成候选")` | 提前拒绝非正常结束，不把格式碰巧合法的JSON当成成功。 |
| [104](deepseek_stream_demo.py#L104) | `finish_reason = current_reason` | 保存stop；后续None不会覆盖它。 |
| [105](deepseek_stream_demo.py#L105) | `if content:` | 跳过None和空字符串，空格字符串仍保留。 |
| [106](deepseek_stream_demo.py#L106) | `answer_size += len(content)` | 累计正文长度。 |
| [107](deepseek_stream_demo.py#L107) | `if answer_size > MAX_ANSWER_CHARS:` | 检查最终回答的缓存上限。 |
| [108](deepseek_stream_demo.py#L108) | `raise RuntimeError("模型回答过长")` | 超限停止，不继续打印或收集本片段。 |
| [109](deepseek_stream_demo.py#L109) | `received_chunks.append(content)` | 按接收顺序保存片段。 |
| [110](deepseek_stream_demo.py#L110) | `print(content)` | 显示接收过程；这些片段不代表已经校验成功。 |
| [111](deepseek_stream_demo.py#L111) | `if not stream_ended:` | 循环结束后检查是否真正收到[DONE]。 |
| [112](deepseek_stream_demo.py#L112) | `raise RuntimeError("流未正常结束，不能生成候选")` | 网络自然结束但缺标记，同样判定失败。 |
| [113](deepseek_stream_demo.py#L113) | `if finish_reason != "stop":` | 再次确认生成结束原因；处理直接[DONE]等缺stop情况。 |
| [114](deepseek_stream_demo.py#L114) | `raise RuntimeError("模型生成未正常完成，不能生成候选")` | 缺少正常完成依据则拒绝。 |
| [115](deepseek_stream_demo.py#L115) | `answer = "".join(received_chunks)` | 无分隔符拼接所有正文，保留正文内部空格。 |
| [116](deepseek_stream_demo.py#L116) | `if not answer.strip():` | 只用strip判断是否全空白，不把原answer替换成去空白版本。 |
| [117](deepseek_stream_demo.py#L117) | `raise RuntimeError("模型回答不能为空")` | 空回答给出独立、明确错误。 |
| [118](deepseek_stream_demo.py#L118) | `try:` | 开始内层任务JSON解析的异常处理。 |
| [119](deepseek_stream_demo.py#L119) | `data = json.loads(answer)` | 完整正文字符串转Python数据。 |
| [120](deepseek_stream_demo.py#L120) | `except json.JSONDecodeError as error:` | 捕获正文JSON格式错误，与事件包装错误区分。 |
| [121](deepseek_stream_demo.py#L121) | `raise RuntimeError("模型回答不是合法JSON") from error` | 转换为模型回答错误，保留原始原因。 |
| [122](deepseek_stream_demo.py#L122) | `try:` | 开始字段校验的局部异常处理。 |
| [123](deepseek_stream_demo.py#L123) | `return TaskCandidate.model_validate(data)` | 构建并返回TaskCandidate，同时执行字段校验、默认值补齐和标签规范化。 |
| [124](deepseek_stream_demo.py#L124) | `except ValidationError as error:` | 捕获Pydantic字段或顶层输入类型校验错误。 |
| [125](deepseek_stream_demo.py#L125) | `raise RuntimeError("模型候选任务字段不合法") from error` | 转换为候选字段错误，失败时不会返回一个默认成功候选。 |
| [190](deepseek_stream_demo.py#L190) | `try:` | 异常处理覆盖建立连接、状态检查、接收及收集过程。 |
| [191](deepseek_stream_demo.py#L191) | `# 总时限避免持续心跳让请求无限延长；取消时仍退出上下文。` | 说明总时限与资源退出关系。 |
| [192](deepseek_stream_demo.py#L192) | `async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):` | asyncio.timeout是标准库异步上下文管理器；120秒后取消当前等待，并在退出时转换成TimeoutError。Python 3.11起提供，当前环境支持。 |
| [193](deepseek_stream_demo.py#L193) | `async with httpx.AsyncClient(timeout=timeout) as client:` | 创建HTTPX客户端并保证退出时清理；原timeout仍限制各阶段网络等待。 |
| [194](deepseek_stream_demo.py#L194) | `async with client.stream(` | 打开流式响应上下文。 |
| [195](deepseek_stream_demo.py#L195) | `"POST", url, headers=headers, json=payload,` | 发送POST，复用已准备的地址、认证头和JSON请求体。 |
| [196](deepseek_stream_demo.py#L196) | `) as response:` | 进入成功后response是本次响应对象。 |
| [197](deepseek_stream_demo.py#L197) | `response.raise_for_status()` | 先检查HTTP状态，非成功状态由HTTPX异常路径处理。 |
| [198](deepseek_stream_demo.py#L198) | `media_type = response.headers.get("content-type", "").split(";", 1)[0]` | 取Content-Type，缺省为空；split(";",1)只拆一次并取前半段，例如text/event-stream; charset=utf-8取出媒体类型。 |
| [199](deepseek_stream_demo.py#L199) | `if media_type.strip().lower() != "text/event-stream":` | 去掉类型声明边缘空格并忽略大小写，再检查是否SSE。 |
| [200](deepseek_stream_demo.py#L200) | `raise RuntimeError("模型响应不是SSE事件流")` | 拒绝200状态下的HTML/普通JSON等错误响应格式。 |
| [201](deepseek_stream_demo.py#L201) | `response.encoding = "utf-8"` | 按SSE格式指定UTF-8解码，随后aiter_lines使用此编码。 |
| [202](deepseek_stream_demo.py#L202) | `print(response.status_code)` | 打印HTTP状态，仍不代表候选已经成功。 |
| [203](deepseek_stream_demo.py#L203) | `candidate = await collect_candidate(response)` | await运行收集协程；只有完整检查通过才得到candidate。 |
| [204](deepseek_stream_demo.py#L204) | `except httpx.HTTPError as error:` | 捕获HTTPX请求、状态和读取异常。 |
| [205](deepseek_stream_demo.py#L205) | `raise RuntimeError("模型流式请求或读取失败") from error` | 转换网络层错误并保留原始原因。 |
| [206](deepseek_stream_demo.py#L206) | `except TimeoutError as error:` | 捕获总时限到期的异常。 |
| [207](deepseek_stream_demo.py#L207) | `raise RuntimeError("模型流式请求超过总时限") from error` | 转换总时限错误；外部主动取消不被此处吞掉。 |
| [209](deepseek_stream_demo.py#L209) | `print(candidate.model_dump())` | 已经离开资源上下文；导出并打印最终候选字典，不写数据库。 |

## 新语法的具体例子

`field, _, value = "data: hello".partition(":")` 得到 `field="data"`、`_ = ":"`、`value=" hello"`。下划线只是普通变量名，表达“不使用这个返回值”。`value.removeprefix(" ")`再得到hello；不会像strip那样删除全部前后空白。

`return content, reason`返回元组，例如("学习", None)；`content, current_reason = parsed`按顺序取出两个成员。纯用量事件返回None，因此先判断None再解包。

`asyncio.timeout(120)`限制整个包裹范围，而HTTPX的read timeout限制一次等待数据的时长：如果对方持续发心跳，每次都没等超过20秒，请求仍可能拖很久，所以另设总时限。超时和取消都是协作式的，不是强制杀进程；没有自动重试模型调用。

## 离线测试怎么验证

`tests/test_deepseek_stream_demo.py`中，wire将预设字典编码成真实SSE文本并补空行；collect用HTTPX Response把它交给生产收集函数。参数化用例覆盖外层结构、类型、状态和正文错误。OfflineStream继承HTTPX AsyncByteStream，故意拆开字节并模拟读取超时、总时限和取消；MockTransport把HTTP请求截留在本进程中，不访问网络。main测试使用假密钥，检查请求stream=True、错误原因、最终输出和资源是否关闭。环境变量替换由pytest恢复，不修改.env。

新增54项通过；连同现有AI相关三个文件共119项通过（1.14s）。这不是数据库全量回归。未对本次新实现重新发送付费模型请求。

## 当前边界与下一步

这是一条不重连、不写库的单候选演示；不实现浏览器EventSource自动重连或多候选选择。事件/回答长度限制是在HTTPX已经提供文本行之后执行，不是底层网络缓冲区的硬内存上限。空choices仅在usage为字典时作为兼容的用量事件接受，不能替代stop和[DONE]。不承诺覆盖世界上所有异常；本次约定的输入、结束、解析和资源路径已经有重复测试。

下一步只做一次真实请求确认协议兼容与提取含义，然后收尾本独立实验；不继续拆分相同边界练习。正式API是否迁移流式，作为后续独立功能决定。

参考：[SSE标准](https://html.spec.whatwg.org/multipage/server-sent-events.html)、[DeepSeek接口](https://api-docs.deepseek.com/api/create-chat-completion/)。
