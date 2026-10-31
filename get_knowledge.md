# 学习问题与知识沉淀

## 阶段六：个人资料检索与回答（2026-10-29起）

### 完整案例回顾与接口职责（2026-10-31归档）

以项目根目录执行`python -m examples.rag.semantic_search_demo "flush 和 commit 有什么区别？" --top-k 1`为例，当前主流程如下。此处汇总跨文件调用链，具体分块、缓存与排序方法见下方对应章节。

| 步骤与调用位置 | 输入、实际处理与输出 |
| --- | --- |
| semantic_search_demo入口：ArgumentParser/add_argument/parse_args | 登记并读取问题与条数，得到args.question字符串和args.top_k整数；asyncio.run(main(...))实际执行协程 |
| main：Path.read_text | 将notes.txt整份正文读入text；相对路径依据当前工作目录 |
| main：Path.exists/json.load | 读取本地缓存，比较原文、来源、模型、1024维及paragraph-v1；有效则直接取得带向量的candidates，失效则走下一步 |
| split_paragraphs(text, source) | 按空行分段，返回text/source/start_line/end_line字典列表；事务段保留1～3行完整解释 |
| embedding_demo.get_embedding(candidate["text"]) | 用整段文字调用百炼Embedding HTTP接口，取出1024维数字列表，保存到候选字典vector字段 |
| main：json.dump | 将候选、完整原文及表示配置保存为notes_vectors.json，进程结束后仍可复用；文件包含原文，不只是数字 |
| get_embedding(question) | 为本次新问题计算向量；文档缓存命中也仍执行此步 |
| rank_candidates/cosine_similarity/get_score | 本地比较问题与各段向量，保存candidate/score，按分数降序切前K条；没有网络调用；空结果由main提示并结束 |
| main：enumerate、字符串构造及join | 将选中的正文和来源范围组织为[资料1]等文字块，拼成context；编号随本次排名变化 |
| answer_demo.generate_answer(question, context) | 将问题及文字参考资料放入messages，调用DeepSeek回答HTTP接口；检查HTTP状态、结构、正常结束和非空文字后返回str |
| main：print | 显示回答，并展示入选原文、路径、范围和分数，供人工核对 |

百炼请求地址为`https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings`，当前源码payload指定text-embedding-v4、input、dimensions=1024、encoding_format=float。HTTPX AsyncClient.post发送请求，raise_for_status检查状态，response.json解析外层JSON，data[0].embedding才是向量。密钥来自DASHSCOPE_API_KEY环境变量。

DeepSeek请求地址为`https://api.deepseek.com/chat/completions`，当前源码指定deepseek-flash、messages、stream=False、max_tokens=2048；密钥来自DEEPSEEK_API_KEY。system提供资料使用与引用约束，user携带问题和context。取回choices[0].message.content作为普通回答文字，不要求json_object，不做TaskCandidate校验。以上描述当前仓库配置，不作为平台最新模型目录或兼容性保证。

两次外部接口职责不同：Embedding把文字转成可比较的数字，回答模型依据检索后的文字组织答案。余弦分数选资料，不直接生成答案；回答模型收到的是正文及来源，不是向量，也不会因这次请求自行读取本地笔记。提示词要求有据引用不等于已自动证明每句话有据。

当前三个段落首次重建时按顺序请求三个文档向量、一个问题向量及一次回答；有效缓存时仅一个问题向量和一次回答。此为当前正常控制流的调用数，不是截图测得的计费记录。文档正文、来源、模型、维度或分块策略变化会重建全部文档向量；改变问题或K不要求重建文档缓存。

document_demo.py是历史读取与关键词练习，不在当前主调用链。当前是CLI RAG，没有通过FastAPI任务路由、不连接PostgreSQL、不创建任务，也未使用向量数据库。离线测试验证可重复流程与参数传递，真实案例检查检索证据覆盖及回答引用；两者不能互相替代。本地提交cd6444b包含源码、样例、测试和文档，不包含生成缓存，尚未推送；本次归档发生在该提交之后。

### 文档向量缓存写入与复用（2026-10-30）

缓存保存可复用的计算结果，不能只看文件存在：旧正文与旧向量一起读会回答过时资料；新正文配旧向量则可能导致检索内容与呈现内容错配。当前小文件保存model、dimensions、source、source_text、candidates，比较原文/来源/模型/维度后决定复用；分块策略变化也应重建。source_text完整原文方案便于理解但有重复存储，尚未引入内容摘要。

当前semantic_search_demo在文档向量生成之后用open(..., "w", encoding="utf-8")和json.dump(..., ensure_ascii=False, indent=2)写入notes_vectors.json。w会创建或覆盖，with负责关闭；JSON可保存浮点数列表，不能保存密钥。临时目录和模拟1024维向量的验收确认写入后可读取、原文/来源/行号/向量正确，没有写项目缓存或请求模型。

读取流程：Path.exists()判断文件是否存在，存在才用Path.open("r", encoding="utf-8")取得文件对象，再由json.load(file)解析为Python字典。原文、来源、模型、维度及分块标识比较通过时直接复用candidates；未命中才计算文档向量并写入。问题向量在分支之外计算，因此换问题不需要重建文档向量，但每次仍需计算问题向量及调用回答模型。当前未处理损坏JSON、缺键或候选内部结构错误，文件存在不代表内容一定可用。

验证证据：此前离线模拟确认两条笔记首次计算3次Embedding、命中时仅1次；原文、来源、模型、维度变化均重建。用户连续运行截图确认第一次重建、第二次复用，两次排名及来源一致；截图本身不是调用计费记录。

### 检索资料组织与文字生成（2026-10-30）

#### 部分可答与元数据范围过滤（2026-10-31）

当前实现更新：过滤功能已通过此前29项离线测试及用户Docker范围真实验证，K=2仅返回5～7行一段。缓存版本已改paragraph-section-v1；取得完整候选后先过滤，再计算问题向量并排名。缓存保留全部主题，无匹配提前结束；首次缓存缺失仍先生成文档向量。下文“下一步计划”属于此前导学过程，实际状态以此更新及源码为准。

P5真实案例同时询问flush与Nginx HTTPS配置：事务段有据可答，证书部分资料不足。用户运行确认回答正确说明flush不提交并引用事务段，同时拒绝给出证书配置步骤。真实存在的资料编号不保证引用有效，应检查该资料能否支持对应结论；引用Docker段说明其只有端口/镜像内容，与引用它证明证书配置不同。

section是段落主题元数据，当前约定取第一行并用str.removesuffix("：")移除末尾中文冒号。该方法返回新字符串；无匹配后缀时原内容不变，不移除中间冒号。没有标题时首行仍成为标签，当前不引入通用标题解析。两处段落保存均增加section，正文仍保留标题，起止行号不变；25项离线流程/分块测试通过，未调用真实模型。

元数据过滤先按用户明确指定的section缩小候选，再计算相似度和取Top-K；范围内只有一段时即使K=2也只返回一段，不从范围外补足。范围过滤不保证资料能回答问题，也不自动从自然语言识别范围。下一步计划在CLI增加--section并把值传入main，在问题向量计算前用普通循环筛选；不限定时沿用全量候选。新字段需使旧缓存失效，完成同步前不运行主流程。

#### 按空行分段与原始行号

分块重叠用于长段落进一步拆分时保留边界上下文。每块最多4行、重叠1行，步长为3：十行形成1～4、4～7、7～10三个块，学习者已正确推导后两块。代价包括重复向量计算/存储、重复上下文及相近块占用Top-K名额，不保证检索改善。此处仅概念学习，当前短段落算法未实现重叠。

2026-10-31接入完成：split_paragraphs先产生带范围的候选字典，遍历候选用整段text计算向量，再通过candidate["vector"]=vector更新列表内的同一个字典。上下文及终端展示同步改用start_line/end_line。缓存增加chunking=paragraph-v1，get缺省None令旧缓存失效；规则变了即使原文相同也需重建，标识必须对应实际算法。用户真实Top-1事务问题取回1～3行完整段落，回答同时解释flush/commit；这是上下文保留的单例证据，不是普遍排名保证。离线段落版24项通过，真实效果与模拟流程验证分别记录。

逐行分块可能拆散标题与解释；按空行合并段落可以一起取回相互补充的内容，但段落过大或混合主题会引入无关材料，不保证检索更准。多行块保存start_line/end_line，空行不进入正文但占原文行号。

split_paragraphs的收集状态：if cleaned_line处理非空正文，if not current_lines仅在新段首行记录起点；空行分支在current_lines非空时用换行join形成字符串、保存终点line_number-1，然后清空状态。连续空行不会创建空块。list.clear()原地清空列表，返回None；此处正文已由join生成独立字符串，因此清空列表不会清掉已保存正文。不要写current_lines = current_lines.clear()。

文件末尾可能没有分隔空行，需在for循环结束后检查剩余current_lines并保存最后一段，再统一return chunks。末尾保存的终点为最后处理的正文行号，不减1；空文本不进入循环，也没有剩余段落。该函数只处理字符串，未接入主流程前不会改变模型检索；后续接入需同步来源字段与缓存分块策略标识。

#### 检索函数职责与命令行Top-K

rank_candidates(query_vector, candidates, top_k=2)仅计算分数、降序排序并返回切片，不负责打印、文件或网络。普通def即可；返回值始终为列表，包括空结果[]，裸return则是None。main负责展示和流程控制，收到空列表后提示并提前return，避免用空资料调用生成模型。重构应保留原有行为：此次曾遗漏main的空结果保护，由离线回归发现并恢复。

argparse的--top-k是可选参数，解析属性为args.top_k；type=int把字符串转换为整数，default=2处理未提供选项，choices=(1,2,3)限定当前实验范围。非法值在解析时退出2，不进入模型流程。传递链为命令行→args.top_k→main的top_k→rank_candidates的top_k→切片条数。choices只约束CLI输入，不会自动约束其他Python代码直接调用函数。改变K不改变文档向量，本身不要求缓存重建；更多资料可能补充证据，也可能引入噪声，不能保证答案更好。

#### 多主题与组合问题的证据覆盖

五条资料实验中，端口问题取回端口映射和镜像概念：后者主题相近，但不能直接证明端口配置。Top-K仅表示现有候选中排名最高的K条，不保证相关、充分或互补；分数也不是正确概率，不凭单次样本设置通用阈值。

组合问题“flush会提交事务吗？另外Docker如何映射8080到80？”此次取回端口映射（资料1，原文第4行）和flush（资料2，原文第1行），回答分别引用两项证据。检查应分两层：先看检索是否覆盖每个子问题，再看回答是否正确使用对应资料。此次通过不代表其他组合问题必定通过。文档不变且配置一致时复用文档向量，但仍计算新问题向量、重新排名并生成回答。

#### 首次真实RAG对照：Top-1与Top-2

问题为“如何把修改正式保存到数据库？”。用户真实运行截图显示flush片段排名1、分数0.7006744461820718，commit片段排名2、分数0.5928322199325635。Top-1只传入flush，模型说明资料未提供具体提交方法；这属于答案片段未进入上下文，不是原文件无答案，也不是降序排序错误。相似度高不等于更能支持具体答案，不能由两个分数直接断言模型排名的具体原因。

本轮实际源码从[:1]改成[:]（全取），当前只有两条资料，因此输出等价于Top-2；需纠正为[:2]才有最多两项的限制。截图显示排名/分数保持一致，回答说明执行commit提交事务并引用[资料2]，解释flush不提交时引用[资料1]。本次必要证据进入上下文后回答改善；这是两条资料、一个问题的小样本对照，不证明Top-K越大越好，也不证明一般检索质量达标。资料编号由本次排序后的上下文位置决定，与文件行号是不同概念。

if not top_candidates只能判断没有候选，无法识别非空但不相关的资料。Top-K在资料非空时仍可能给出无关结果；下一步需用资料无法回答的问题检查模型是否明确说明证据不足。拒答不一定意味着程序失败，应区分“未检索到已有答案”和“资料确实没有答案”。

top_candidates经enumerate从1编号，每项提取candidate里的source/line_number/text，构造[资料N]块；context_parts是字符串列表，"\n\n".join后context是完整参考资料字符串。资料编号按本次检索结果分配，不是原文件行号；三引号字符串会保留缩进和前后换行，当前不影响功能。来源不能写死，离线改为原文第3行已验证编号与原始行号各自正确。

generate_answer(question, context)负责回答而非任务提取。system约束只依据资料、引用已有编号、证据不足时说明并将资料中的指令视为数据；user携带实际问题和context。这些提示不能保证引用真实或回答正确，后续仍需核对证据。复用DeepSeek异步HTTP流程及错误检查，但不使用json_object格式、不对content做第二次json.loads或TaskCandidate校验；HTTP响应外层仍是JSON，里面的content是要返回的普通文字。与Embedding的data[0].embedding返回数字列表相区分。

本轮临时离线验证8类情形：正常文字去首尾空白返回、HTTP错误、非法外层JSON、缺少响应结构、非stop结束、content非字符串、空白回答、缺密钥；同时核对问题资料传递及客户端关闭。未调用真实生成模型；这验证传输和解析，不证明模型会遵守引用或证据不足规则。下一步把生成函数接到semantic_search_demo的context构造之后，再离线验证全链路。

### 可复用向量函数与重构验收（2026-10-30）

#### 列表切片与Top-K结果的类型

切片格式为items[start:stop:step]。步长默认1；正步长时省略start从开头开始，省略stop到末尾；起点包含、终点不包含。例如items=["A","B","C","D"]，items[1:3]为["B","C"]，items[:1]为["A"]，items[2:]为["C","D"]，items[::2]为["A","C"]。step不能为0；本阶段使用正步长，负步长默认边界不同，后续需要时再展开。

items[0]返回元素"A"，items[:1]返回列表["A"]；[:1]是最多取前一项，不是取下标1的元素。切片终点超出长度会取到已有末尾，空列表[:1]返回[]；空列表[0]抛IndexError。切片创建新列表但不深拷贝内部字典，修改内部共享对象可能影响原列表看到的内容。

当前ranked_candidates是评分字典的列表。top_candidates=ranked_candidates[:1]之后仍需for item in top_candidates，item才是字典；item["candidate"]取得候选字典，再用["text"]取得正文。曾将切片结果命名item后直接用字符串键索引，实际报TypeError: list indices must be integers or slices, not str。修正为遍历后，正文、来源、原始行号与分数对应通过离线验收。

2026-10-30补充验收：使用真实notes.txt读取路径，但仅模拟Embedding返回，正常两行资料共3次调用并输出第2行；空白文档得到空结果且不抛索引错误。当前空白文档仍计算一次问题向量、无输出，尚未实现提前返回提示。模拟分数1.0只证明代码流程，不证明真实模型语义效果；完整真实检索仍待运行。

get_embedding(text)把调用者文本填入input，返回完整向量；main只await调用并展示维度/前5项。异步函数的list[float]注解描述await后的预期结果，不自动校验响应；return即使在async with内部也会先退出上下文再完成返回。临时离线HTTPX模拟已验证文本传递、1024项完整返回、HTTP错误传播及客户端关闭，未重复消耗额度。

cosine_similarity通过zip(left, right, strict=True)对应遍历全部维度，累加点积与两边平方和，用math.sqrt求长度后相除。zip默认遇较短输入即停止；strict=True在发现长度不一致时抛ValueError。空向量和零向量长度为0，主动拒绝避免除零。临时验证包含二维与1024维样例；这是教学范围，不代表任意外部数值（如NaN）的全面校验。

重构只替换计算步骤时，必须保留循环内scored_candidates.append。仅赋值score不会把结果自动保存到列表：曾出现函数计算正确但最终Top-2为空的情况。恢复candidate/score记录后，2026-10-30实际验证三条评分保存、降序及Top-2 B/A均通过。后续复用函数前，应把演示执行放进main并用入口保护；导入模块仍执行顶层定义，但不应自动运行演示。

### 百炼接入与首次真实向量请求（2026-10-29）

- 平台提供认证、接口与计费，模型负责具体计算。当前方案用百炼text-embedding-v4计算向量，DeepSeek继续生成回答；不同平台的密钥不能混用。阿里云总控制台概览不等于百炼控制台，百炼API Key也不是阿里云AccessKey。
- 用户当时截图确认text-embedding-v4免费额度剩余1M Token、到期2027-01-28、用完即停开启。这是当时账户证据，不保证以后额度不变；现金余额与免费Token额度不同，余额为0不是防止按量计费的开关。首次调用后额度可能减少，具体余额以控制台为准。规则参考：[免费额度](https://help.aliyun.com/zh/model-studio/new-free-quota)。
- DASHSCOPE_API_KEY用于百炼，DEEPSEEK_API_KEY用于生成。PowerShell Read-Host -AsSecureString隐藏输入，再赋给当前进程环境变量，之后启动的Python可继承；隐藏输入不意味着环境变量加密。bool(os.getenv(..., '').strip())只验证非空，不验证凭据有效；不要打印密钥或认证头。
- 当前北京请求地址为https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings；官方亦提供业务空间专属域名。密钥与地域需对应。复用httpx.AsyncClient，不增加SDK；payload使用model、input、dimensions=1024、encoding_format="float"，而不是聊天接口的messages。await client.post才发请求并消耗额度，json=payload负责JSON编码与对应请求头，raise_for_status检查状态，response.json解析响应。
- response_data["data"][0]["embedding"]依次取得结果列表、第一项、数字向量。这里不是聊天content中的JSON字符串，不需要第二次json.loads。len(vector)检查维度，vector[:5]只查看前5项，不能截取这5项代替完整向量进行后续检索。1024维表示1024个数，不代表1024个Token或字符。接口参考：[官方Embedding说明](https://www.alibabacloud.com/help/en/model-studio/embedding-interfaces-compatible-with-openai)。
- 用户最新截图显示状态200、维度1024和前5个数字，结合当前源码确认单句真实调用成功；尚未完成文档/问题共同向量化、真实语义排序或RAG回答。导师未重复请求模型，具体浮点数不作为固定验收值。

### 本次导入错误：局部变量不需要从其他模块导入

错误的from client_demo import response会先执行client_demo.py顶层请求，访问本地/tasks/stats。连接失败时requests.get抛异常，赋值没有完成；模块捕获并打印错误后，导入方仍找不到response，于是出现ImportError。这个错误发生在百炼请求之前，不应通过启动本地服务来解决。当前response由main内的await client.post返回并赋值，是局部变量，不需要导入。

from fastapi.security import api_key取得的也不是百炼密钥。实际变量命名为ali_api_key，认证头必须引用同一个变量：f"Bearer {ali_api_key}"。变量名看似相同含义不代表对象相同；不要为了消除未定义提示而导入无关同名对象。main入口保护只能阻止被保护的调用，无法阻止其他模块中未放入保护块的顶层请求。骨架中的...是占位表达式，不是本次错误原因，完成实现后可移除。

手工向量实验验收：二维非零向量余弦为点积除以两向量几何长度乘积；query=[1,0]与[1,1]、[2,0]、[0,1]的分数约0.7071、1、0。循环外初始化评分列表，循环内保存candidate/score，循环后sorted(key=get_score, reverse=True)生成降序新列表，[:2]取得最多两项。key传函数对象，由sorted将记录传入函数；排序及切片不深拷贝内部字典。评分保留整个候选，item["candidate"]["text"]/source可取回对应正文和来源。2026-10-29实际运行确认Top-2为模拟B/demo-B、模拟A/demo-A，原记录顺序不变；当前是手工数字，不是模型对文字的真实语义判断。当前输出为完整列表repr，尚未按字段逐条格式化显示，但不影响数据关联。

关键词到向量检索导学：字符串in只判断文字包含，当前区分大小写；用“如何把修改正式保存到数据库？”搜索“commit 提交当前事务。”会漏检。Embedding将文本表示为数字向量；问题与文档需使用兼容的模型和配置。文档内容及表示方式未变时可复用文档向量，新问题计算问题向量；仅存在变量中的向量随进程结束而丢失。余弦相似度比较方向，非零向量同向为1、正交为0，分数不是答案正确概率。Top-K仅取排名靠前的K项，不能保证存在相关证据；检索后必须保留并取回正文与来源。当前只讲解概念，尚未接入真实Embedding或实现向量检索。

真实文档组织与拆分：document用source=str(file_path)、text=text将路径字符串与读取结果组织在一起；字符串转换不读取文件。document["text"].splitlines()返回行字符串列表，默认keepends=False，不保留行结束符、不修改原字符串；支持常见LF/CRLF，中间空行可以产生空字符串。当前notes.txt一行一条知识，按行拆分用于入门，不等同于通用语义分块。两行真实正文已实际运行输出；原手工chunks仍独立，真实行列表尚未转换成带来源的片段。

RAG先检索与问题相关的资料，再把问题和资料交给模型生成回答；检索到内容不等于有回答依据。每个片段保存chunk_id、source、section、text，便于单独取出时仍能追溯来源。source/section属于描述正文的元数据，不是SQLAlchemy的Base.metadata对象；chunk_id当前手动填写，不是自动数据库主键。手工chunks[1]只是按位置取值，尚未实现检索。

pathlib是标准库；Path("examples/rag/notes.txt")创建路径对象，不创建文件。相对路径以进程当前工作目录为起点；当前约定从项目根目录运行。read_text(encoding="utf-8")打开、解码并读完整文件，返回str且自动关闭文件；文件需事先存在并使用对应编码。缺文件会抛FileNotFoundError，若未捕获，后续片段输出不会执行。将正文赋给text不代表已有chunks字典会自动更新，必须显式把该变量用于后续数据组织。2026-10-29实际验收停在缺少notes.txt，下一步创建小文本文件并打印读取结果，尚未实现自动分块或检索。

## 阶段五：DeepSeek调用、候选校验与离线测试（2026-10-22起）

### 从自然语言到候选任务：消息、格式与校验

#### 流式响应入门与本地收集（2026-10-26）

2026-10-29真实验收与连接排查：代理路径TLS握手ConnectTimeout发生在读取SSE正文之前；HTTPX转换后的异常再由main以RuntimeError from error保留原因。未带密钥的探测收到401，证明该次收到HTTP响应，不证明密钥错误，也不证明后续连接必然稳定。用户随后完整调用收到200并输出符合输入的候选字典，完成当前实现的单次真实兼容验收；原超时原因尚未确定。print(content)会给每个片段额外显示换行，但received_chunks保存的仍是原片段，最终空字符串join不会增加这些显示换行。

2026-10-29测试执行链增量已写入[原测试文件旁注](tests/test_deepseek_stream_demo.py)：Response的stream参数仅指定正文的字节来源；AsyncClient的transport指定执行请求并返回响应的组件，MockTransport实际调用保存的handler。monkeypatch替换构造入口后返回预先配置的真实客户端，并非替换整个业务流程。读取异常先触发响应与客户端上下文清理，再由main转换异常，pytest.raises捕获后继续外层测试断言；connect场景没有返回响应，因此不要求未使用的内存流被响应关闭。旁注保留动态error_type分支，另以read场景展示每步实际数据流。此次只补注释，没有重新运行测试或调用模型。

异步关注等待时能否让出执行机会，流式关注数据能否分段到达并处理。当前正式接口仍为异步非流式；模型→后端和后端→浏览器是两段传输，仅把模型stream改True不会自动让浏览器逐字显示。

本地stream_collect_demo已实现遍历预设chunks、依次append到received_chunks、显示片段、循环外join→json.loads→TaskCandidate.model_validate。用户反馈运行符合预期，导师静态核对；这不是实际网络流，也未验证模型正常结束。"".join按顺序连接字符串并返回新字符串，非字符串元素会报TypeError；list.append原地修改列表，返回None。未收完整的JSON不能按最终候选处理，默认字段不能替代后续片段或结束检查。

下一步引入异步生成器：async def中出现yield后，调用得到异步生成器对象，不是可直接await取得最终值的普通协程。await asyncio.sleep模拟片段等待，yield chunk交出一个值并暂停，消费方通过async for索取后续值时再从暂停处继续。普通return结束函数，yield保留执行位置；异步生成器可自然结束或裸return，不使用return携带最终结果。当前练习完整消费，无外部连接；后续网络资源仍需async with管理。参考：[Python异步生成器](https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions)。

2026-10-27增量：本地生成器已经采用None作为末尾标记并通过正常/缺标记临时离线验证。None是自定义约定，不是Python或DeepSeek的内置协议。收到标记后break可退出循环，循环后的检查仍会执行；continue则继续索取下一项。break不保证立即关闭生成器或执行yield之后的普通语句，真实连接需要明确管理生命周期。

真实流式事件的三个信息各有用途：delta.content是新增正文，finish_reason是生成停止原因，data: [DONE]表示事件流结束。length表示生成因长度限制而停止，不是“仍在生成”；即使流结束、正文碰巧是合法JSON，本项目也拒绝作为成功候选。成功路径需流结束、finish_reason为stop、正文JSON解析和TaskCandidate校验全部通过。协议参考：[DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)。

局部解析顺序：原始data行→line.removeprefix("data:").strip()得到event_text字符串→先识别[DONE]→普通事件用json.loads(event_text)得到字典event→event["choices"][0]["delta"]["content"]取正文，event["choices"][0]["finish_reason"]取结束原因。removeprefix和strip返回新字符串，不进行JSON解析、不修改原变量；removeprefix只移除匹配的开头。JSON的null解析为Python的None。固定写finish_reason=None无法读取后续stop值，应按字段取值。

外层事件JSON完整，不代表content里的任务JSON已完整：先解析每个事件并收集content，再join后解析任务JSON。r前缀字符串保留反斜杠，适合本地表示包含JSON转义双引号的样本。if content在当前字符串或None范围内跳过空字符串和None，但保留空格字符串；不要对正文片段strip，否则可能破坏答案内容。读取结束原因要放在if content之外，结束事件可能没有新正文。

当前教学练习只处理预设的单行data事件，假定choices和字段齐全，并非通用SSE解析器。已加入if not line.startswith("data:"): continue，跳过空行及非data行；startswith返回bool，不修改字符串。此处continue继续读取，break会提前终止整个循环。空行样本已实际运行通过；此前正常、缺[DONE]和length三分支临时离线验证全部通过。尚未实现或验证真实网络流，多行事件及真实响应字段差异仍待处理。

取值错误复盘：data:是SSE前缀，移除后json.loads得到的字典顶层为choices，而不是data。event["data"]因此抛KeyError，这表示字典缺键，不是JSON解析失败。应从event["choices"][0]继续取值。

#### SSE与HTTPX流读取生命周期（2026-10-27）

SSE（Server-Sent Events，服务器发送事件）规定通过HTTP响应持续传递文本事件的格式；同一次响应可陆续发送多个事件，无需每条重新请求。媒体类型为text/event-stream，data:表示事件数据，空行分隔事件；一个事件可以有多条data行，数据也不必是JSON。当前模型接口把JSON放进事件数据，[DONE]是该接口的结束约定，不是所有SSE服务必须使用的标记。层次为HTTP承载响应→SSE划分事件→JSON表示事件数据。参考：[SSE标准](https://html.spec.whatwg.org/multipage/server-sent-events.html)。

payload中的stream=True要求模型服务端采用流式返回；client.stream(...)控制本地HTTPX如何读取响应，不会把普通JSON转换成SSE。response.aiter_lines()无必填参数，返回提供str的异步迭代器，用async for读取；行不是网络数据包，也不必是完整事件。

局部请求结构：外层async with httpx.AsyncClient(timeout=timeout) as client管理客户端；内层async with client.stream("POST", url, headers=headers, json=payload) as response管理响应；先response.raise_for_status()检查HTTP状态，再async for line in response.aiter_lines()逐行读取。headers携带认证，json传请求体。读取阶段也可能出现网络异常，因此未来异常处理应覆盖整个读取过程。退出内层上下文关闭响应，退出外层清理客户端资源；break只退出循环，在上下文内的后续语句仍可执行，离开上下文才清理。抛异常时同样执行退出清理，通常继续向外传播。参考：[HTTPX异步流式响应](https://www.python-httpx.org/async/#streaming-responses)。

返回类型应依据实际类、方法定义及装饰器判断，不能凭post名称或是否联网猜测。本机AsyncClient.post源码为async def且无yield，调用产生协程对象，函数体尚未开始执行；await执行并等待协程，最终得到Response。源码的-> Response标注执行完成后的结果类型，不表示直接调用已得到响应，也不自动执行类型转换。协程对象本身也是Python对象。

对比：普通未包装的async def且无yield→协程对象；async def含yield→异步生成器对象；HTTPX stream含yield并被@asynccontextmanager包装→异步上下文管理器。后者应使用async with而非直接await。async with会等待__aenter__进入、将结果赋给as后的变量，并在退出时等待__aexit__；HTTPX stream内部在try中yield response，finally中await response.aclose()。当前无需自己实现这些特殊方法或装饰器。

三种语法职责：await等待一个可等待对象的执行结果；async with组织资源的异步进入和退出；async for逐项获取异步数据。示例async def get_number(): return 10，pending=get_number()得到协程，number=await pending才得到10。正式候选接口仍为非流式，本节为已讲解，非已接入网络。

2026-10-27练习进展：role-only事件不含content，使用delta.get("content")得到None并由if content跳过；choices/delta等必要结构仍用直接索引，不把所有结构错误都当作空内容。正常候选实际运行通过。

网页流读取实验最初只定义main而没有入口，运行模块立即结束且没有输出；补if __name__ == "__main__": asyncio.run(main())后实际返回200和HTML，退出0。def与async def的定义均不自动执行函数体；无yield的普通def调用立即执行，而无yield的async def调用先创建协程。async不自动开线程，普通脚本顶层不能直接await。网页可能只有一条长行，流读取不保证逐字或固定间隔输出，也不会将HTML转换成SSE。

独立deepseek_stream_demo已准备Schema、headers及stream=True的payload，用户反馈配置输出符合预期；准备字典和打印配置尚未调用模型。此前密钥为空是在请求前由本地检查拒绝，不能据此判断密钥无效；临时环境变量及安全输入方法见本章已有配置说明。后续先观察原始SSE数据行，再接入候选收集校验，不能将HTTP200或出现[DONE]单独视为候选验收通过。

2026-10-27后续验收：独立deepseek_stream_demo已将HTTPX逐行响应接到正文收集、结束检查、JSON解析和TaskCandidate校验。用户反馈真实运行符合预期；导师未重复付费调用或取得完整响应证据。当前实验仍按单行data和choices[0]处理，并非通用SSE解析器；正式API仍非流式。仅收集delta.content，reasoning_content不混入候选JSON。

状态覆盖复盘：current_finish_reason读取本条事件的值，finish_reason保存已收到的非空结束原因；仅在current_finish_reason is not None时更新后者。必须移除此前无条件赋值，否则旧语句先将stop覆盖为None，后面的if跳过并不会撤销赋值。Python顺序执行，条件只控制其缩进块，不恢复历史状态。stop后接None是离线状态保持边界样本，不声称供应商必然发送。修正后临时离线normal、missing_done、length、stop_then_null四项通过，正常分支检查最终字典，异常分支不输出最终候选，均验证响应/客户端上下文退出；不是完整pytest套件结果。

输出形式复习：print(candidate)显示Pydantic模型的可读表示；candidate.model_dump()返回Python字典，不修改原模型、不写数据库、不重新执行输入校验。当前默认调用包含已补齐的字段；得到的是dict而不是JSON字符串。流程为json.loads解析字符串→model_validate校验并构建模型→model_dump导出模型数据。只有完成检查及校验之后的最终候选才可供确认，途中打印的正文不是成功结果。

流式异常分层（2026-10-27）：网络错误可能在连接、raise_for_status或aiter_lines等待后续数据时发生，故try必须覆盖两层HTTPX上下文与整个读取循环；HTTPError转换为“模型流式请求或读取失败”。循环内json.loads(event_text)局部捕获JSONDecodeError，提示“模型流式事件不是合法JSON”；循环外json.loads(answer)同类异常提示“模型回答不是合法JSON”。事件包装合法不代表正文是JSON，正文JSON合法也不代表字段符合规则：TaskCandidate.model_validate局部捕获ValidationError，提示“模型候选任务字段不合法”。例如urgent违反优先级枚举，缺title违反必填要求。

各层使用raise RuntimeError(...) from error保留原始原因；重新抛出后不继续打印最终候选，不用默认数据掩盖失败，也不使用宽泛except Exception混同错误。独立脚本仍可显示异常栈，这不同于API路由转换HTTP错误响应。导师分轮临时离线验证连接/状态/读取异常、外层/内层JSON错误、非法优先级与缺title，均检查相关分类和资源退出；未新增仓库测试文件，不宣称完整回归。上下文只有成功进入后才由async with调用退出方法，进入响应失败时仍检查已进入客户端的清理。

事件结构检查增量：合法JSON的{}在event["choices"]处抛KeyError，{"choices": []}在[0]处抛IndexError，均发生在循环内，尚未到最终json.loads(answer)。except (KeyError, IndexError)捕获任意一种，而非两者同时发生；事件字段已集中读取，重复的current_finish_reason取值已移除。键存在不等于类型正确：delta=None时取键成功，但调用.get会抛AttributeError，因此先isinstance(delta, dict)，非字典主动报“模型流式事件的delta必须是对象”，再读取可选content。局部缺键/空列表五项临时离线通过；delta空字典/role字典接受，None/列表/字符串/数字拒绝，六项临时离线通过，失败不进入候选校验且资源退出。本节只证明这些边界，其他层级类型检查尚未完整实现。

2026-10-27用户明确委托一次补齐后，流式实验已整理为iter_sse_data（文本行→完整事件）、parse_stream_event（事件→正文与结束原因）、collect_candidate（收集→候选）及main（网络生命周期）。外层类型、可选正文、单候选索引、服务错误事件、结束后异常正文、空回答及资源时限统一完成。SSE按空行分帧，多条data行用换行合并，支持首行BOM及注释；纯用量事件只作兼容跳过，不能证明成功。事件/正文各64K字符、总时限120秒为本示例策略，不是平台上限或硬内存保证。新增54项可重复离线测试通过，连同现有AI测试共119 passed in 1.14s；未重发真实请求。详细逐行说明和测试流程合并在[STREAM_GUIDE.md](examples/llm/STREAM_GUIDE.md)。此前“尚未完整实现”的段落属于历史推进记录，以本段为当前状态。

#### JSON Schema与实际校验的区别（2026-10-26）

JSON只规定数据格式，JSON Schema描述字段结构和约束。priority="urgent"是合法JSON中的字符串，但不满足enum=["low", "normal", "high"]。properties描述字段，required表示必须提供的字段，additionalProperties=false禁止额外字段。

TaskCandidate.model_json_schema()在类上调用，默认mode="validation"，返回可JSON序列化的规则字典，不校验具体候选、不请求模型。candidate.model_dump()在实例上调用，返回该候选的数据字典；TaskCandidate.model_validate(data)才执行校验及默认值补全。只提供title可以得到priority="normal"、tags=[]、description=""；显式null不等于省略。Schema中的default是描述，Schema本身不会补值。

用户实际打印Schema并正确观察到tags仅有type=array和items.type=string，没有自动描述自定义校验器的strip/lower/去重。输入[" Python ", "python", "SQL"]满足该Schema，实际Pydantic校验会规范为["python", "sql"]；["   "]也满足该Schema的元素类型要求，但会被本地校验器拒绝。生成Schema不等于完整翻译任意Python逻辑，本地校验仍需保留。

json.dumps(schema, ensure_ascii=False, indent=2)将规则字典转为字符串供阅读，ensure_ascii=False保留可读中文，indent=2控制缩进。与json.loads解析字符串的方向相反。若把Schema放进system.content，应先转成字符串再与提示文本拼接；json=payload之后由HTTP客户端编码整个请求，两次序列化针对不同层级。提示词中的Schema只是提供给模型的文本约束，不是供应商严格结构化输出参数，也不保证模型完全遵守。

2026-10-26已实现system提示词追加由TaskCandidate生成的Schema文本，保留业务意图说明、json_object及本地model_validate。请求内容断言从实际system.content提取并解析Schema，与模型生成的规则字典比较，不依赖JSON空格或键顺序；三个离线测试文件65 passed，用户反馈追加Schema后的真实调用符合预期。后续精简了手写类型/枚举等重复规则，字段含义及缺信息处理仍保留；最新四行文案修正已静态核对，没有为纯文字修正重复付费调用。参考：[Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)。

规则维护原则：结构约束主要由TaskCandidate及其生成的Schema描述，自然语言提示说明提取意图及未说明时的处理。Schema的default是注释性质的默认描述，不会自行理解用户是否表达优先级；tags的default_factory也没有自动生成default=[]。提示词中的“未说明时空列表”等策略不能机械删除。面向学习者的编辑说明（如“不再手写三个可选值”）不应复制到发给模型的system提示词中。

下一步理解语义正确性：Schema/Pydantic能验证priority是否属于合法集合，但不能仅凭候选数据判断它是否忠实于用户原文。例如原文指定低优先级，候选却写high，仍可通过当前字段校验。现有model_validate只接收候选字典，未与原文比较；Mock测试证明程序处理预设回答的行为，不证明模型真实提取质量。人工确认及基于固定输入的效果检查承担不同职责，不能用HTTP200或测试全绿替代语义判断。

#### 固定输入的提取效果检查（2026-10-26）

先确定输入和预期，再查看输出：标题可等义改写，明确优先级须保持，未指定标签时不从标题自动补标签，未提供备注时为空字符串。四条基线覆盖完整信息、信息缺省、明确低优先级和多标签；实际候选及判断保存在examples/llm/EVALUATION.md。本轮用户截图四条均200且符合标准，记录为本轮4/4通过，不外推总体准确率或提示词提升幅度。

应保留首次结果，失败分为网络/状态/解析/字段校验失败与语义错配，不靠反复重试隐藏失败。接口候选已经过Pydantic清理，观察到小写标签不证明模型原始输出就是小写。比较提示词版本需要固定案例和判断标准，并确认运行版本；响应截图本身不能证明服务加载的是最新代码。

#### 模型上下文与Token入门（2026-10-24）

上下文是本次请求交给模型的材料。当前llm_service每次只构造system规则及本次user输入，没有自动携带上一轮回答、用户修改或数据库记录。任务保存在PostgreSQL不代表模型能自动读取。用户说“把刚才那条改成高优先级”时，程序必须提供明确的目标及相关信息；如果用户已修改候选，应优先依据当前保存状态，而不是旧模型回答。提供上下文与执行数据库更新是不同职责。

Token是分词器将文本编码后使用的处理单位，不固定等于一个汉字、一个英文单词或一个字符。Python的len(text)与Field(max_length=2000)限制字符长度，不是模型Token数，也不是模型上下文窗口大小。system规则、样例、用户输入及提供的历史信息都可能计入输入用量，不能只数用户一句话。实际Token数以服务返回的usage为准，不使用固定换算保证上限。

外层HTTP响应中的usage与choices同级：prompt_tokens为输入Token数，completion_tokens为生成Token数，total_tokens为两者总数。思考模型的生成用量可能包含推理部分，不能只数最终content的可见文字。本轮只讲字段位置，不改变generate_candidate返回TaskCandidate的契约，不增加真实模型调用或安装分词器。

示意数字而非真实调用结果：usage={"prompt_tokens": 180, "completion_tokens": 60, "total_tokens": 240}。增加system说明即使user文本不变，也可能增加输入用量。上下文窗口是模型能处理的上下文容量限制；max_tokens用于限制生成Token数量，均不同于应用2000字符输入限制。具体模型上限及价格留到实际配置时核对，不在本轮硬编码。

参考：[DeepSeek Token用量](https://api-docs.deepseek.com/zh-cn/quick_start/token_usage/)、[Chat Completions响应字段](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)，2026-10-24核对。

2026-10-24真实观察：用户截图显示输入186、生成141、总量327，其中推理116包含在生成141内，非推理生成部分为25，不能再把116加到327上。缓存命中0、未命中186；本轮只识别数据，不展开缓存定价。用字典get("usage")取值，缺键默认None而非0；在成功校验后临时print不会改变函数返回的候选对象。临时输出用于教学，观察完成后应移除，不输出密钥或完整响应。

#### 输出预算与结束原因（2026-10-24）

max_tokens是请求payload中与model/messages同级的生成上限，不是必须生成的数量，不限制用户输入字符数，也不表示请求超时秒数。当前思考模型的推理部分占用生成预算；一次观察到生成141不代表以后都只需141。512此前只是讲解示例，并未要求写入程序。

每个choices元素中的finish_reason与message同级。stop表示自然结束或命中指定停止序列；length表示达到生成Token或上下文长度限制，回答可能被截断。当前单条候选业务只接受stop，其他值统一抛RuntimeError("模型回答未正常完成")；缺少该字段由已有结构异常处理转换，并保留KeyError原因。stop也不保证JSON或字段正确，因此后续校验仍必须保留。

执行链为外层JSON解析→提取finish_reason及content→检查结束原因→回答类型和非空检查→内层json.loads→TaskCandidate.model_validate。即使length的content碰巧是合法JSON也拒绝，不能只靠JSON解析判断生成是否完成。响应HTTP200只说明请求在HTTP层面成功，不取代结束原因及内容校验。本业务抛出的RuntimeError仍由路由转换为固定502提示，不自动重试。

导师将测试辅助函数response_with_content增加finish_reason="stop"默认参数，让既有正常假响应符合当前协议；显式传非stop模拟中断。新增7个非stop值的拒绝案例、1个截断时json.loads未调用的案例、1个缺字段结构错误案例，两个离线文件实际64 passed。更新模拟数据是因为业务新增了字段要求，不能把旧Mock缺字段造成的失败误判为业务实现错误。

2026-10-24已配置初始教学预算max_tokens=2048，并通过离线测试确认请求传参。这是本项目的起始配置选择，不是模型能力上限或完整回答保证；本轮未发送真实请求验证完成率。需要结合实际用量和length失败情况调整；先具备中断拒绝机制，再设上限。参考：[DeepSeek max_tokens与finish_reason](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)。

#### 同步调用、线程池与函数执行（2026-10-25）

函数用于组织代码，线程负责执行代码。普通函数调用不会因为进入另一文件或函数就自动创建线程。当前FastAPI将普通def候选路由安排到线程池执行；假设线程T1负责该路由，它直接调用llm_service.generate_candidate后，输入检查、requests.post、响应解析和候选校验也在T1执行。Service返回后，路由才将结果赋给candidate并返回；抛出异常时则进入相应异常处理。

执行顺序：请求校验→线程T1执行路由→进入Service→requests.post等待响应→状态及内容校验→Service返回→路由返回。requests.post是同步阻塞调用，等待期间当前线程不能继续执行后续response.json。线程池提供可复用的工作线程，不是每调用一个函数就新建线程，也不是某个用户永久绑定一个线程。

另一个请求B可以由线程T2处理，所以A等待模型时，B查询已有任务可能先完成。这称为并发处理，不意味着无限容量或保证B立即开始；线程池、数据库连接及其他资源均有限。阻塞当前线程不等于整个API停止，FastAPI也不会自动将所有普通工具函数单独放入线程池。

异步等待导学：事件循环负责安排可运行的异步任务；任务A等待支持异步的网络操作时可以暂停，让同一事件循环线程运行其他就绪任务，结果可用后再继续A。A自身仍需取得结果后才能解析，不会提前执行依赖结果的语句。async def声明异步函数，await用于等待可等待对象；不是给任意同步调用加上await就能使其非阻塞。仅将当前路由改为async def、仍直接调用含requests.post的同步Service，会阻塞执行它的事件循环线程。本轮仅理解原理，未改造项目或引入异步HTTP客户端。

参考：[FastAPI异步与线程池](https://fastapi.tiangolo.com/async/)。同步执行链已获学习者理解反馈；异步原理为本轮新导学，理解待确认。

#### 协程对象、await与gather的分工（2026-10-25）

调用async def函数会创建协程对象，单独创建不会运行函数体。例如request_a = simulate_request("A", 3)保存的是协程对象；result_a = await request_a开始执行并等待该协程完成，保存其return值。本实验return name，所以result_a是字符串"A"。两行可合并为result_a = await simulate_request("A", 3)，变量名不改变调度行为。直接await协程不自动新建线程。

await要求当前流程取得结果后再执行下一行。协程内部await asyncio.sleep(delay)时会暂停当前任务，让事件循环运行其他就绪任务；sleep单位为秒、可用小数，默认返回None，不联网。外层main仍需等待simulate_request返回才完成赋值。异步等待不意味着当前任务跳过结果依赖，也不意味着每次await都必然发生任务切换。

连续写await simulate_request("A", 3)和await simulate_request("B", 1)，B的调用在A完成后才执行，等待约4秒。gather同时接收这两个协程时会将它们安排为任务，等待可以重叠，B先结束，等待通常约3秒；await gather取得按传入顺序排列的返回值列表['A', 'B']，不是按完成顺序。gather负责组织并发，await负责等待结果；不能将“连续await新协程顺序执行”推广为“连续await已经调度的Task必然顺序执行”。gather默认传播异常，但不自动取消其他任务。

独立脚本的asyncio.run(main())创建并管理事件循环，完成后清理并关闭循环，返回main的返回值（无显式return则为None）；同一线程已有事件循环运行时不能再次调用它。当前实验无需第三方依赖或模型密钥。参考：[Python协程与任务](https://docs.python.org/3/library/asyncio-task.html)、[运行器](https://docs.python.org/3/library/asyncio-runner.html)。

#### 异步HTTP客户端与响应处理（2026-10-25）

httpx.AsyncClient用于发送异步HTTP请求和管理连接。async with httpx.AsyncClient(timeout=10.0) as client创建并进入客户端使用范围，离开缩进块时执行异步清理，即使块内异常也关闭连接；创建客户端本身不发送请求。当前默认超时5秒，显式10.0配置网络操作超时，不是整个请求严格总时限。

response = await client.get(url)等待网络请求及默认的响应体读取完成，得到httpx.Response对象。response.raise_for_status()、response.status_code和response.text处理已取得的响应，不用await；非2xx状态检查抛httpx.HTTPStatusError，网络错误可抛httpx.RequestError的子类。HTML网页用text，不调用json；普通非流式JSON响应的response.json()同样无需await。

GET实验与模型POST的共同链路为创建客户端→等待请求→状态检查→使用响应→关闭连接。POST用await client.post(url, headers=headers, json=payload)，headers承载请求头，json把Python数据编码为请求JSON；不会自动解析服务返回的JSON。请求完成后仍要逐层解析、检查finish_reason及校验候选。HTTPX与requests的异常类型不同，迁移时不能只替换请求那一行。

2026-10-25导师实际运行examples/async_http_demo.py成功，状态200及HTML正文，退出0；当时打印完整正文，2026-10-26源码核对已改为response.text[:80]。虚拟环境可导入httpx 0.28.1；原requirements仅声明httpx2，二者为不同包，异步迁移时已补httpx==0.28.1直接依赖。参考：[HTTPX异步客户端](https://www.python-httpx.org/async/)、[响应处理](https://www.python-httpx.org/quickstart/)。

#### 异步迁移解决的问题与两条入口的数据流（2026-10-25）

原实现普通def路由由FastAPI安排到工作线程，requests.post等待网络期间占用该线程；不是整个API都停止。异步迁移使等待网络期间当前任务可挂起，让事件循环处理其他就绪任务，不保证模型单次生成更快。调用链里的async def允许使用await，但不会自动等待内部函数；不为每个函数创建新线程。仅改async def而继续直接调用阻塞HTTP请求会阻塞事件循环。

命令行python -m examples.llm.deepseek_demo定位模块，执行导入和函数定义，再进入__name__判断。main()创建协程对象，asyncio.run启动并管理事件循环来执行main；main中的candidate = await generate_candidate(text)等待Service最终返回TaskCandidate。历史错误：演示曾漏这一处await，实际得到协程对象并在访问candidate.title时报AttributeError；2026-10-25已修正且65项离线测试通过。asyncio.run不会自动深入函数查找并运行所有未await的协程。2026-10-26用户反馈真实命令行调用结果符合预期；记录为用户实测反馈，导师未重发模型请求。

Service的具体数据流：自然语言字符串→strip及长度检查→读取并清理密钥→构造headers与payload字典→httpx.Timeout配置→async with AsyncClient→await client.post(url, headers=headers, json=payload)编码并发送请求→得到已读取响应体的Response→raise_for_status→退出上下文关闭连接→response.json()解析外层字典→提取finish_reason和content→检查stop→json.loads(content)得到任务字典→TaskCandidate.model_validate规范化字段→return候选对象。示例Python标签经模型校验变为python；标题、备注去首尾空白，禁止多余字段，优先级限制为low/normal/high。响应和候选保存在当前调用的局部变量中，流程不保存数据库。

独立脚本收到候选后print(candidate.title)、print(candidate.model_dump())，后者是字典而非JSON文本；main完成后run清理事件循环。网页入口则由Uvicorn运行api.py中的app，api.py导入ai_router并include_router登记路由；装饰器与请求/响应模型此时登记规则，不调用模型。收到POST /ai/task-candidate的JSON后，FastAPI用TaskCandidateRequest验证，成功才进入异步路由；路由await同一个Service，得到候选后由response_model=TaskCandidate校验序列化为HTTP JSON。演示脚本不经过api.py/路由；HTTP请求不经过演示main，也不在路由里使用asyncio.run。

异常流：HTTPX网络或状态异常→Service捕获httpx.HTTPError并raise RuntimeError from error→API路由转换固定HTTP502；独立脚本没有这层HTTP转换，异常传播至终端。输入请求校验失败则HTTP422且不调用Service。结构、结束原因、JSON及字段错误仍分别检查，异步改造不取消这些规则。requirements声明直接依赖，不是运行时入口，也不会因import自动安装包。

离线测试对应三段链路：test_deepseek_demo模拟AsyncClient及其异步post，实际执行解析/校验；test_ai_routes用AsyncMock替代Service、执行真实路由；test_llm_demo_entrypoint用异步替身执行脚本入口。AsyncMock可被await并核对是否等待，Response的json/raise_for_status仍用普通Mock；测试通过不证明实网可达或模型真实回答质量。

##### 回顾入口：从具体命令追踪同一份数据（2026-10-26补充）

在项目根目录执行以下已有命令会真实调用模型，不是离线测试：

```powershell
& "D:\Python\Project\.venv\Scripts\python.exe" -m examples.llm.deepseek_demo
```

PowerShell的&执行指定Python；-m按模块定位examples/llm/deepseek_demo.py。导入与函数定义先准备好工具，入口判断成立后才执行asyncio.run(main())。文件分工与运行顺序如下：

| 步骤与文件 | 实际语句或动作 | 当前数据及下一步 |
| --- | --- | --- |
| 1. examples/llm/deepseek_demo.py | asyncio.run(main()) | 创建并运行main协程，管理脚本的事件循环 |
| 2. 同一文件的main | candidate = await generate_candidate(text) | text为“高优先级学习SQLAlchemy，重点理解Session，标签是Python。”，等待Service返回 |
| 3. llm_service.py | 类型检查、strip、长度检查、读取密钥 | 输入合法后才构造请求；密钥进入headers，不进入候选字段 |
| 4. llm_service.py | 构造payload | 原文放入messages中的user.content；system提供字段规则 |
| 5. llm_service.py | Timeout及async with AsyncClient | 配置等待限制并管理连接资源，尚不等于已发送模型请求 |
| 6. llm_service.py | response = await client.post(url, headers=headers, json=payload) | 编码请求JSON并发送；等待网络期间可暂停当前任务；完成后得到Response |
| 7. llm_service.py | raise_for_status，然后退出async with | 检查HTTP状态并关闭客户端；非流式响应内容已读取，仍可解析 |
| 8. llm_service.py | response.json()、提取content、json.loads(answer) | 外层字典→模型回答字符串→候选字段字典，分别检查结构和结束原因 |
| 9. task_candidate.py | TaskCandidate.model_validate(candidate) | 根据类规则实际执行字段校验；例如Python标签规范为python |
| 10. llm_service.py→演示main | return validated_candidate | main的await完成，candidate才成为TaskCandidate对象 |
| 11. 演示main | print(candidate.title)、print(candidate.model_dump()) | 打印标题及Python字典；main结束后run清理事件循环 |

示例数据转换（为解释构造，非要求模型逐字输出）：

```text
自然语言：高优先级学习SQLAlchemy，重点理解Session，标签是Python。
    ↓ payload.messages中的user.content
外层响应字典：{"choices": [{"finish_reason": "stop", "message": {"content": "..."}}]}
    ↓ 提取content，得到字符串
'{"title":"学习SQLAlchemy","priority":"high","tags":["Python"],"description":"重点理解Session"}'
    ↓ json.loads，得到字典
{"title": "学习SQLAlchemy", "priority": "high", "tags": ["Python"], "description": "重点理解Session"}
    ↓ TaskCandidate.model_validate，得到模型对象
TaskCandidate(title="学习SQLAlchemy", priority="high", tags=["python"], description="重点理解Session")
```

浏览器入口的前后两端不同，中间复用同一个Service：

```text
服务器启动：Uvicorn导入api.py → app.include_router(ai_router)登记规则
实际请求：POST /ai/task-candidate，JSON为{"text": "上述原文"}
    → TaskCandidateRequest检查请求体，失败则422
    → ai_routes.generate_task_candidate(request)
    → await llm_service.generate_candidate(request.text)
    → 经过上表步骤3～9
    → 路由return candidate
    → FastAPI按response_model序列化为HTTP JSON，返回200
```

命令行直接调用Service，不经过路由；浏览器请求不经过演示main。api.py还导入任务路由，其依赖会在启动时读取数据库密码配置；这与候选请求实际不调用数据库是两件事。候选成功不代表任务已保存，人工确认后的POST /tasks才走任务Service/Repository的写库流程。

复习异步变化时抓住两个位置：main/路由await Service，Service await网络请求。外层调用等最终候选，内层调用等HTTP响应；每一层都不能跳过结果依赖。Response解析、模型校验、打印无需await。requirements.txt记录直接依赖httpx，测试文件以替身验证各段调用，不属于正常请求的运行路径。

#### 输入与异常按阶段处理

generate_candidate在读取密钥和请求前检查text：非字符串抛TypeError，strip后为空或超过2000字符抛ValueError。2000是应用实验限制，不是模型上限。异常分类区分调用者输入错误与外部服务响应错误；例如用户输入空白是ValueError，模型返回空白属于RuntimeError，不能仅按“都是空字符串”使用同一类别。

post与raise_for_status放在同一个局部try中，捕获requests.RequestException（含超时/连接/HTTP错误）并转换为RuntimeError。response.json独立捕获requests.exceptions.JSONDecodeError；提取choices[0].message.content独立捕获KeyError（键缺失）、IndexError（列表越界）、TypeError（结构类型不符）。多异常可写except (KeyError, IndexError, TypeError)。取值成功不代表内容有效，还需确认answer为字符串、strip后非空，再解析内层JSON；json.loads异常和Pydantic字段异常应各自分阶段处理。

raise RuntimeError("说明") from error在外层提供明确失败类别，同时用异常链保留原始原因，可通过异常对象.__cause__检查。转换异常会结束当前函数，不自动重试或继续解析；窄范围try避免把不相关错误误报为请求失败。导师使用Mock的side_effect模拟抛异常，并检查失败后response.json未调用，不需要付费请求。

2026-10-23路由异常转换补充：`except RuntimeError as error`中的error指向已有异常；`HTTPException(status_code=502, detail="候选任务生成失败，请稍后重试")`创建另一个异常对象，raise将新对象抛出。原异常没有被改成HTTPException，也不会因from而重新执行请求。

| 当前except块中的写法 | 新异常的`__cause__` | 新异常的`__context__` | 表达的关系 |
| --- | --- | --- | --- |
| `raise http_error from error` | 明确指向error | 记录正在处理的原异常 | 原异常是新异常的直接原因 |
| `raise http_error`（新建异常） | 默认为None | 自动记录正在处理的原异常 | 处理原异常期间出现新异常 |

因此不能说“不加from就一定丢失原异常”。当前场景中Python仍通过隐式上下文保留它；from用于明确说明这是有意的异常转换。当完整异常链被展示时，显式原因之间通常显示“The above exception was the direct cause of the following exception”；隐式上下文通常显示“During handling of the above exception, another exception occurred”。这只是异常链的展示方式，from本身不会打印日志，已由FastAPI处理的HTTPException也不保证在终端打印堆栈。

当前项目的具体执行链为：

```text
requests.post请求超时 → Timeout
    ↓ llm_service捕获，再raise RuntimeError(...) from error
RuntimeError("模型服务请求失败")，__cause__指向Timeout
    ↓ ai_routes捕获，再raise HTTPException(...) from error
HTTPException(502, 固定提示)，__cause__指向RuntimeError
    ↓ FastAPI默认异常处理
客户端收到502和{"detail": "候选任务生成失败，请稍后重试"}
```

使用默认HTTP异常处理时，是否写from不改变上述状态码和detail；`__cause__`不会自动进入响应JSON。内部保留原因与对客户端返回固定提示可以同时实现。请求模型非法输入仍返回422；当前约定将生成函数的RuntimeError统一转为502。后续已补密钥配置检查：os.getenv("DEEPSEEK_API_KEY", "")读取后strip，缺失或空白主动抛RuntimeError("模型服务未配置API密钥")，也进入这一固定502响应分支；这是当前阶段的简化错误约定。读取非空不代表密钥实际有效。

测试分别检查两个边界：通过TestClient发送请求，验证502、固定detail及内部错误文本未出现在响应中；直接调用路由函数，用`pytest.raises(HTTPException)`捕获异常对象，再检查`caught.value.__cause__ is original`。直接函数调用不会自动执行FastAPI的请求解析，因此测试先自行构造合法TaskCandidateRequest；它补充异常对象检查，不能替代HTTP测试。两项均用Mock模拟生成失败，不调用真实模型。通用pytest.raises与对象身份检查见本文已有对应章节。

候选模型已实现，备注Field(default="", max_length=500)不可遗漏，否则仅str默认空串仍接受501字符；已离线验证清理后500字符允许、501字符拒绝。TaskCandidate.model_validate(candidate)输入解析后的字典，成功返回校验/清理/补默认值后的模型实例，失败抛ValidationError。字典用candidate["title"]，模型用validated_candidate.title；model_dump()把模型导出为Python字典，不保存数据库或重新校验。完整导入examples.llm.task_candidate配合从项目根目录python -m examples.llm.deepseek_demo运行，模块名称不带.py。

generate_candidate(text: str)->TaskCandidate封装读取密钥、请求、解析及校验，user消息content取自text，return交还候选对象，打印属于调用入口。所有请求代码放在函数内，if __name__ == "__main__"仅保护示例调用：导入模块只定义函数，不读密钥或发送请求；-m运行则进入示例入口。离线测试以Mock替换requests.post，既能检查传入文字，也能模拟响应验证返回对象，不消耗模型费用。用户真实调用成功与助手离线验证分别记录。

#### 候选生成的离线测试：从准备数据到检查结果（2026-10-23）

对应`tests/test_deepseek_demo.py`。目标是验证：给定一种输入和一种模型服务返回情况，自己的`generate_candidate()`会怎样处理。测试用预设响应替代网络，输入检查、请求参数组装、回答结构提取、`json.loads()`和Pydantic校验仍执行项目中的真实代码。它不能证明真实服务可访问，也不能证明模型总能理解用户意图。

2026-10-23模块迁移后，测试实际使用`import llm_service`，调用`llm_service.generate_candidate()`，并替换`llm_service.requests.post`。本节涉及deepseek_demo属性的早期示例保留迁移前语境；当前正式调用关系见下文“正式模块复用与PyCharm导入提示”。

**先区分两个模拟对象和一个真实函数：**

| 名称 | 在本测试中扮演的角色 | 谁会使用它 |
| --- | --- | --- |
| `mock_post` | 模拟发送请求的可调用对象 | `generate_candidate()`执行`requests.post(...)`时 |
| `response` | 模拟请求返回的响应对象 | 随后的`raise_for_status()`与`json()`调用 |
| `generate_candidate` | 被测试的真实业务函数 | 测试函数直接调用 |

模拟关系由两条赋值建立，变量名本身不会决定Mock的类型：

```python
response.json.return_value = {
    "choices": [{"message": {"content": content}}],
}
mock_post.return_value = response
```

第一条登记“以后调用`response.json()`时返回什么”；第二条登记“以后调用`mock_post(...)`时返回哪个对象”。此时尚未调用业务函数。真实的`requests.post(...)`发送POST请求后返回响应对象，不是返回一个“POST请求”；这里用`response`模拟该响应，用`mock_post`模拟发送请求的函数。模拟对象的通用方法与调用记录见下文“Mock为何能够代替Repository”中的补充。

**两个返回值不会因为赋值而合并：**

```python
body = {"choices": []}
response = Mock()
mock_post = Mock()

response.json.return_value = body  # 调用response.json()才得到body。
mock_post.return_value = response  # 调用mock_post(...)先得到response。

received_response = mock_post("https://example.com")
assert received_response is response

received_body = received_response.json()
assert received_body is body
```

对应的业务执行链是`requests.post(...) → response → response.json() → body`。`mock_post.return_value = response`保存的是对整个响应模拟对象的引用，没有读取它的`json.return_value`，也不会自动调用`.json()`。只有写成`mock_post.return_value = response.json.return_value`才相当于直接返回body；若body是普通字典，业务代码随后调用`response.raise_for_status()`就会失败，因为字典没有这个方法。上例是用于理解的独立片段，不代表新增或执行了仓库测试。

**fixture与辅助函数的分工：**

- `@pytest.fixture`把`mock_post(monkeypatch)`登记为测试准备函数。测试声明形参`mock_post`，pytest先准备它依赖的`monkeypatch`，执行fixture，再将`return post`得到的对象交给测试形参。默认每条测试案例独立准备，包括参数化展开的每一例。
- `monkeypatch.setenv("DEEPSEEK_API_KEY", "offline-placeholder")`给当前测试进程设置虚构环境变量，业务函数才能按原有方式读取它；占位字符串不能用于真实认证。
- `monkeypatch.setattr(deepseek_demo.requests, "post", post)`替换业务函数实际查找的模块属性。`deepseek_demo.requests`引用的是共享的`requests`模块，不是独立副本；有效期内，其他代码通过同一模块的`post`属性调用也会受到影响。此前单独保存的原函数引用不会自动改指向Mock。
- 替换从`setattr`执行后生效，持续到默认函数级`monkeypatch`清理时；不是调用一次就失效。正常测试清理会恢复方法和原环境变量状态，测试断言失败也会清理。这个fixture无需自己用`yield`恢复，因为恢复工作由`monkeypatch`负责。
- `response_with_content(mock_post, content)`没有fixture装饰器，是普通辅助函数。测试显式传入两个实参并调用；其中的`mock_post`形参接收测试传进来的对象，不会再次自动触发fixture。它配置模拟响应，再返回`response`，方便测试随后检查响应方法有没有被调用。

这里使用的`setenv(name, value, prepend=None)`与`delenv(name, raising=True)`都返回`None`；后者默认在变量不存在时抛`KeyError`。输入失败测试中，fixture已经设置了变量，所以`delenv("DEEPSEEK_API_KEY")`可以明确移除它。以上都是测试进程中的临时修改。参考：[pytest的monkeypatch方法及恢复机制](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)。

**用成功案例串起具体执行流程：**

```text
测试先用json.dumps把{"title": "  Read docs  ", "description": "  Session  "}
转成JSON字符串，作为模拟回答content
    ↓
辅助函数把这个字符串放进外层choices/message/content字典
    ↓
测试调用真实generate_candidate("  Read docs  ")
    ↓
业务代码strip输入，读取虚构密钥，组装payload
    ↓
requests.post(...)实际调用mock_post，得到预先配置的response
    ↓
response.raise_for_status()调用子Mock，默认不会抛出HTTP错误
    ↓
response.json()直接返回预设外层字典
    ↓
真实业务代码取出content → json.loads得到任务字典
    ↓
TaskCandidate.model_validate清理标题、备注，补priority和tags默认值
    ↓
返回TaskCandidate对象 → 测试用model_dump检查完整字段
```

这里`json.dumps()`是“Python数据→JSON字符串”，`json.loads()`方向相反。外层`response.json()`已经被模拟，因此没有真正解析HTTP正文；内层`json.loads()`确实执行。默认的`response.raise_for_status()`只是子Mock被调用，不读取真实状态码；测试通过给该子Mock设置`side_effect`，专门模拟HTTP失败。

**输入文字不必等于模拟回答中的title：**

成功案例中两边碰巧都写了`"  Read docs  "`，不代表存在绑定关系。`generate_candidate(...)`的实参是用户输入，辅助函数中JSON的title是测试事先安排的模型输出。可以设想输入为`"帮我安排阅读数据库文档，重点理解Session"`，模拟回答为`{"title": "阅读数据库文档", "description": "理解Session"}`：业务函数负责转发输入，并解析这个预设回答；Mock不会理解输入并自动生成标题，也不会检查两段文字语义是否一致。

检查请求内容时，应与清理后的用户输入比较；检查返回候选时，应与预设回答经过校验、清理、补默认值后的结果比较。改变输入不自动改变Mock响应，修改示例时需同步调整对应路径的断言。测试验证的是应用的传参、解析与校验，不是模型的语义理解能力。调用处的`"  Read docs  "`称为实参，函数定义中的`text`称为形参。

**调用记录为什么能反映真实业务函数准备的参数：**

`mock_post.call_args.kwargs["json"]`是读取调用记录的表达式，不是测试函数。fixture函数虽然也叫`mock_post`，但测试函数中的同名形参接收的是fixture返回的Mock对象，不是fixture函数本身。

业务代码实际执行`requests.post(url, headers=headers, json=payload, timeout=(10, 20))`。只有`post`被替换，之前构造payload的真实代码仍然执行；Mock被调用时记录收到的实参，再返回预设response。因此，这里更准确的说法是“读取真实业务函数传给模拟请求方法的json参数”，没有真的通过网络发送它。

| 表达式 | 本例中读到的内容 |
| --- | --- |
| `mock_post.call_args` | 最近一次调用记录 |
| `.args` | 位置实参元组，本例含URL |
| `.kwargs` | 关键字实参字典，含headers、json、timeout |
| `.kwargs["json"]` | `json=payload`传入的payload字典 |

继续取`payload["messages"][1]["content"]`，得到第二条user消息的文本`"Read docs"`。它与构造模拟回答的数据是两条不同的路径：前者检查“发出什么”，后者安排“收到什么”。

**每类失败放在哪一层：**

| 测试安排 | 具体触发点 | 要检查的行为 |
| --- | --- | --- |
| 删除虚构密钥，再传`None`、数字、空白或超长输入 | 类型、空白或长度检查 | 抛约定的输入异常；既不读缺失密钥，也不调用post |
| `mock_post.side_effect = original` | 发送请求时 | 超时/连接错误转换为RuntimeError，保留原始原因 |
| `response.raise_for_status.side_effect = original` | 检查HTTP状态时 | 转换HTTPError，之后不调用`response.json()` |
| `response.json.side_effect = original` | 解析外层正文时 | 转换外层JSON错误 |
| `response.json.return_value = {}`、`{"choices": []}`或`{"choices": None}` | 取回答结构时 | 分别覆盖KeyError、IndexError、TypeError的统一处理 |
| content为`None`、数字、空串或纯空白 | 检查回答类型与内容时 | 拒绝无效回答；当前这些案例只断言RuntimeError类型 |
| content为`"not JSON"` | 真实`json.loads()`执行时 | 报内层JSON错误，原因类型为`json.JSONDecodeError` |
| 把`[]`、`None`、`{}`或错误字段字典先交给`json.dumps()` | 真实候选模型校验时 | 即使JSON语法合法，字段不合法仍转换为RuntimeError |

例如`json.dumps(None)`得到合法JSON文本`"null"`，`json.loads()`会成功得到Python的`None`，之后才由候选模型拒绝。设计此类测试时先让前面步骤成功，只改变本例要检查的失败位置，才能知道错误确实来自目标步骤。

**为什么非法输入测试故意删除密钥：**

fixture先设置虚构密钥，测试再用`monkeypatch.delenv("DEEPSEEK_API_KEY")`将其移除。目的是让“输入不合法”和“密钥缺失”同时存在，检查函数是否先拒绝输入。`os.environ["DEEPSEEK_API_KEY"]`按键读取环境变量；键不存在时，像字典缺键一样抛KeyError。

以`text=None, error_type=TypeError`这一组为例：

```text
正确顺序：检查None不是字符串 → 抛TypeError → pytest.raises(TypeError)接住
         → 执行with外的assert_not_called()，确认没有请求

错误顺序：先读缺失的密钥 → 抛KeyError → 来不及检查None
         → pytest.raises(TypeError)不接受KeyError，用例失败
```

因此，“没有调用post”单独不足以证明逻辑正确：因为读密钥失败也不会调用post。本例同时检查预期输入异常和没有请求，验证应在依赖密钥之前拒绝非法输入。空串/纯空白/超长字符串的预期是ValueError，原理相同。异常类型不匹配时，异常继续传播，后面的普通断言不会执行；不是出现任意异常就通过。

后续密钥读取已改为getenv及显式空值检查；上面的KeyError描述保留初版语境。当前若错误地先检查缺失密钥，会抛RuntimeError，而非预期的输入TypeError/ValueError，所以原测试仍能发现顺序错误。新增配置测试使用合法输入，分别检查密钥缺失、空串、纯空白均在post前拒绝，以及虚构合法密钥清理后正确构造Authorization。

**requests异常类、异常对象与真正抛出异常：**

这里是`requests.Timeout(...)`，不是`response.Timeout(...)`。`requests`是导入的HTTP库，`response`是某次调用得到的响应对象，二者职责不同。`requests.Timeout`、`requests.ConnectionError`和`requests.HTTPError`是该库的异常类；调用异常类创建异常对象，括号中的字符串是错误说明。例如`"timeout"`不是超时秒数，可以换成`"等待模型服务响应超时"`。

```python
original = requests.Timeout("timeout")  # 创建对象，程序还会继续执行。
mock_post.side_effect = original        # 配置规则，此时也没有抛出。
# 随后业务代码调用mock_post(...)，Mock才抛出original。
```

这和`error = ValueError("输入不合法")`再`raise error`的区别一样：创建对象与抛出异常是两个动作。`@pytest.mark.parametrize("original", [requests.Timeout("timeout"), requests.ConnectionError("connection")])`安排两次测试，分别把两个异常对象传给original；模拟超时无需真的联网等待。

`requests.exceptions.JSONDecodeError("invalid", "<html>", 0)`的三个实参分别是错误说明、被解析文档、错误位置；这里同样只是创建供Mock抛出的异常，不是真的运行JSON解析器。`side_effect`的调用效果和断言方法见通用Mock补充；原始请求异常为什么最终匹配RuntimeError，以及`caught.value.__cause__`的检查，见本文“使用pytest.raises验证预期异常”的增量说明。

本文件最初有9个测试函数，参数化后为`1 + 5 + 2 + 1 + 1 + 3 + 4 + 1 + 7 = 25`条案例。2026-10-22导师实际运行得到`25 passed`。2026-10-23先仅归档讲解，随后在标签去重验收轮次新增两项参数化测试共6例，本文件实际结果更新为`31 passed`。不能把它与旧完整回归129例直接相加，声称最新完整套件已经全部通过。

#### 候选标签与保存规则保持一致（2026-10-23离线验收通过）

现有`TaskService.create_task()`会对标签去首尾空白、转小写、拒绝空标签、保留首次出现顺序去重。不能把“字段是字符串列表”等同于“标签符合保存规则”。例如`[" Python ", "SQL", "python"]`应成为`["python", "sql"]`；`["Python", "   "]`应在交给用户确认前被拒绝。

2026-10-23首次归档时，学习者已添加`@field_validator("tags", mode="after")`及normalize_tags，实现strip、lower、空标签拒绝。随后学习者补充`if cleaned_tag not in cleaned_tags:`，仅第一次出现时append，实现保序去重；导师新增6例并运行本文件31 passed，确认两种重复顺序、空列表及三种空标签场景。类定义时装饰器登记规则，调用`model_validate()`才执行；after接收经过字段基础校验的列表，必须返回最终列表供模型保存。省略tags时的默认空列表本身合法，不依赖默认值自动执行验证器。参考：[Pydantic字段验证器](https://docs.pydantic.dev/latest/concepts/validators/)。

**自定义ValueError如何成为ValidationError，再成为RuntimeError：**

当前验证器的相关逻辑是：

```python
for tag in tags:
    cleaned_tag = tag.strip().lower()
    if not cleaned_tag:
        raise ValueError("tags must not be empty")
    if cleaned_tag not in cleaned_tags:
        cleaned_tags.append(cleaned_tag)
return cleaned_tags
```

用`candidate = {"title": "学习 Python", "tags": [""]}`串起流程：

1. 业务函数调用`TaskCandidate.model_validate(candidate)`，Pydantic按模型规则检查数据。
2. tags是列表，内部的空串也是字符串，因此仅`list[str]`类型检查无法拒绝它；基础校验后进入after验证器。
3. normalize_tags收到`[""]`，本轮tag为`""`，strip/lower后仍是`""`，`if not cleaned_tag`成立。
4. 验证器执行`raise ValueError("tags must not be empty")`。本次验证器调用立即中断，不会append该标签，也不会执行末尾return。
5. Pydantic捕获这个校验用的ValueError，把字段位置tags、错误原因、相关输入等整理进ValidationError，并由model_validate向调用者抛出。赋值右侧失败，因此没有正常返回或赋值一个可用的validated_candidate。
6. generate_candidate中的`except ValidationError as error`捕获它，再执行`raise RuntimeError("模型候选任务字段不合法") from error`。
7. 外层测试捕获RuntimeError，其直接原因`caught.value.__cause__`是ValidationError。

```text
normalize_tags              Pydantic校验入口             generate_candidate
raise ValueError       →   报告ValidationError       →   raise RuntimeError
发现某个标签不合法          整理模型字段错误               对外报告候选生成失败
```

可以把验证器理解为“标签检查员”，Pydantic是组织整份数据检查并整理错误报告的人。这不是原ValueError对象就地改变类型，也不是Python自动转换所有ValueError；转换发生在Pydantic调用验证器的校验流程里。直接调用`TaskCandidate.normalize_tags([""])`绕过model_validate时，仍会直接抛出ValueError。

“汇总”不要求至少两个错误：只有一个错误也报告ValidationError。若title为空且tags含空标签，Pydantic可把标题长度错误和标签错误一起放进同一个ValidationError。但单个验证器抛出异常后不会回到循环继续检查后续标签。允许`tags=[]`，因为循环执行零次后返回空列表；拒绝的是`tags=[""]`这类含空内容元素的列表。

边界纠正：`test_invalid_candidate_fields`最后一组是`{"title": "test", "description": "x" * 501}`，由`Field(max_length=500)`内置规则拒绝，不是normalize_tags主动抛ValueError。自定义空标签检查和内置长度限制都会由model_validate对外报告ValidationError，但来源不同。最初归档时测试文件尚未包含空标签案例；随后2026-10-23验收新增`test_candidate_blank_tags_are_rejected_before_confirmation`，以三组标签验证上述异常链，并检查原因为ValidationError及包含自定义空标签消息。

参考：[Pydantic如何收集验证器错误及多个字段错误](https://docs.pydantic.dev/latest/errors/errors/)。

#### 正式模块复用与PyCharm导入提示（2026-10-23）

正式代码由根目录task_candidate.py定义TaskCandidate，由llm_service.py定义generate_candidate。examples/llm/deepseek_demo.py通过`from llm_service import generate_candidate`复用生成函数，仅在`if __name__ == "__main__":`中调用示例和打印。读取密钥和发送请求留在函数内部，导入模块不会调用模型。从项目根目录运行`python -m examples.llm.deepseek_demo`才会执行演示入口并请求真实服务。

旧路径examples/llm/task_candidate.py保留一行`from task_candidate import TaskCandidate`，让旧路径继续提供正式类，称为重新导出（re-export）。它不会复制类，也不创建模型实例。若导入后又写`class TaskCandidate(...)`，后面的定义会覆盖当前模块中的同名绑定，重新变成两份类定义。迁移函数也一样：导入函数后不再保留另一份同名def。

本轮在独立进程移除密钥、Mock阻止HTTP，确认演示函数与正式函数、旧路径模型与根目录模型分别是同一个对象，导入不请求。既有31例改为直接验证llm_service，并实际通过；业务模块迁移后测试替换的位置也需与真实查找位置一致。

编辑器诊断需区分三项设置：

| 设置或文件 | 作用 |
| --- | --- |
| Python解释器 | 指定使用哪个Python和已安装依赖；本项目复用D:/Python/Project/.venv/Scripts/python.exe |
| 源码根目录 | 告诉PyCharm从哪里解析项目模块；本项目根为D:/Python/Project/Task_Managers_2 |
| examples/llm/__init__.py | 将llm明确标记为普通Python包，可为空文件 |

本次观察到：PyCharm在旧模型文件中将绝对导入错误解析为该文件自身，提示“导入解析为其包含文件”；而从项目根目录执行Python时正确取得根目录模型。单独打开项目和设置源码根目录后提示仍存在；学习者添加llm/__init__.py后，截图中红色错误消失、解析目标变为根目录task_candidate。Python也支持没有__init__.py的命名空间包，所以不能笼统说所有没有该文件的目录都不能导入。这个排查结果针对当前项目与编辑器环境，不代表所有导入错误都应通过添加该文件修复。

随后出现的黄色“未使用的import”是另一种提示：当前文件没有直接使用导入名称，但作为兼容模块，它有意将名称提供给其他调用者，因此保留该导入有用途。可选地添加`__all__ = ["TaskCandidate"]`声明导出名称；它影响星号导入的名称选择，也可帮助编辑器识别有意的重新导出，但不创建类、不运行校验，也不是修复此前自导入问题的必要步骤。当前文件仍仅保留一条导入，未要求必须加入__all__。

验证编辑器解析时，可Ctrl点击导入语句中的模块名，检查是否跳到根目录完整模型；运行验证则检查实际模块路径和对象身份。两种检查关注不同层面，不能相互替代。不要因兼容文件显示未使用导入就自动优化删除它。

参考：[PyCharm源码根目录](https://www.jetbrains.com/help/pycharm/content-root.html)、[PyCharm包与目录](https://www.jetbrains.com/help/pycharm/populating-projects.html)。

#### 请求消息与两层JSON解析

system消息放应用的提取规则与输出样例，user消息放本次用户输入；两者均为messages列表中的role/content字典。多行提示词可用Python三引号字符串组织。system规则指导模型，不取代程序校验。当前示例从“高优先级学习SQLAlchemy，重点理解Session，标签是Python”提取title/priority/tags/description，不生成id/done/created_at；用户截图确认模型已按预期输出候选文本，未写数据库。

payload中的response_format={"type":"json_object"}约束模型回答message.content采用JSON对象文本，不是把整个HTTP响应变成JSON；正常外层API响应本来就是JSON。官方要求提示中包含json字样并给输出样例，仍需处理空content、截断或其他异常。JSON模式不保证字段齐全、优先级合法或与用户原意一致。

两层解析的具体值：HTTP外层可包含`"content":"{\"title\":\"学习SQLAlchemy\"}"`，content本身是字符串。response.json()把外层JSON解析为带choices的Python字典，不递归尝试把字符串内容也解析成对象。answer=response_data["choices"][0]["message"]["content"]取出`'{"title":"学习SQLAlchemy"}'`字符串，json.loads(answer)才得到带title的任务字典。print(answer)不显示字符串外层引号，所以看起来像字典；应结合type判断。json.loads来自标准库json，非法JSON抛JSONDecodeError；JSON顶层类型决定返回类型，不保证总是dict。

随后TaskCandidate.model_validate(candidate)负责字段校验，是第三个不同职责：response_format要求回答形式，response.json解析外层，json.loads解析回答，Pydantic检查任务规则。候选模型已实现标题1～100、备注最多500、清理字符串空白、priority限定小写low/normal/high、标签默认独立空列表。ConfigDict(extra="forbid")拒绝未声明字段，避免模型擅自加入id等。Literal固定值的既有讲解见本文对应章节；它不会自动将HIGH转小写。候选模型不导入路由和数据库，离线可验证；标签业务规则仍待补齐。

参考：[DeepSeek JSON输出要求](https://api-docs.deepseek.com/zh-cn/guides/json_mode/)。

#### 调用环境与真实请求

2026-10-23闭环导学补充：用户查看候选后可直接接受或修改title、priority、tags、description。点击“确认保存”应将最终四字段提交POST /tasks，复用既有校验、Service和Repository；不是再次调用模型。只有“重新生成”才再次调用POST /ai/task-candidate，重新生成可能改变用户刚刚修改的内容，也会再次产生模型调用。当前用Swagger手动操作两个接口，还没有实现前端确认按钮或自动保存。

2026-10-29闭环验收与约束补充：用户在Swagger手动复制候选四字段、修改备注后调用POST /tasks，再通过GET /tasks/778确认修改后的备注已保存；修改尚未创建的候选不需要PATCH。TaskCreate负责请求校验，TaskService构造TaskRecord，Repository.add_task执行add/flush，创建路由commit提交后返回。客户端确认提交HTTP请求不等于数据库commit必然成功；若commit后响应丢失，再发相同创建请求仍可能产生新ID。tasks主键保证ID不重复，tags.name唯一保证标签不重名，关联表联合主键保证同一任务/标签关联不重复，都不保证任务内容或创建请求不重复。当前没有创建幂等机制；候选超时重试生成与创建请求超时的处理必须区分。


本机8001候选接口已由用户实际执行并截图返回200，得到学习SQLAlchemy/high/[python]/重点理解Session。该结果证明这一候选调用成功，不证明数据库连通、迁移已更新或任务已保存。保存前需核对运行服务的数据库主机与名称，再以alembic current查询同一配置目标的迁移版本；current查询版本，upgrade才执行迁移，二者职责不同。

环境变量由当前终端及其新启动的子进程使用：换一个终端可能读不到此前设置的临时变量；Ctrl+C正常停止自己启动的Uvicorn不会清空父PowerShell的变量。检查bool(os.getenv(..., '').strip())只显示是否存在非空值，不打印凭据，也不能证明密钥或密码有效。正式app导入任务路由时仍需数据库密码配置，但只调用候选接口不会因此自动查询数据库。用户本轮确认本机目标为localhost/task_manager_learning；不要与测试库或容器库混淆。

当前闭环目标是自然语言→模型解析→程序校验候选任务→用户确认→现有POST /tasks保存。解析成功本身不创建数据库记录。用户已有官方开放平台密钥，在当前PowerShell用Read-Host -AsSecureString输入，再转为当前进程的DEEPSEEK_API_KEY环境变量；输入隐藏不等于环境变量加密，不能打印密钥或headers。子进程Python可继承变量，新终端需重新配置。python -c执行直接提供的代码，-m运行模块，python script.py运行脚本；bool(os.environ.get(...))仅确认非空，不证明密钥有效。

examples/llm/deepseek_demo.py使用现有requests依赖，读取环境变量并构造url、headers、payload。官方地址https://api.deepseek.com/chat/completions；Authorization头格式Bearer加空格及密钥。messages是role/content字典列表，user表示用户消息；model指定API模型标识，stream=False等待非流式结果。2026-10-22官方文档将deepseek-flash对应到DeepSeek-V4.1-Flash-1017，也列出deepseek-v4-pro；API别名不是永久锁定版本。准备字典不发送请求，requests.post才发生真实调用与可能计费。

requests.post(url, headers=headers, json=payload, timeout=(10,120))返回Response；json参数序列化字典并设置JSON内容类型。timeout默认不设，元组分别限制连接和读取等待，不是整次调用总时长。当前学习者实际脚本使用(10,20)，即读取等待20秒，已成功不代表以后都不会超时。raise_for_status无参，4xx/5xx抛HTTPError，正常返回None；response.json解析正文，不证明HTTP成功，非法JSON可抛解析异常。response_data["choices"][0]["message"]["content"]依次取选项列表、首个选项、消息、回答文本。网络故障可能在post就抛异常；首版未封装错误处理，后续已按本章“输入与异常按阶段处理”完成封装，仍不连接任务数据库。

用户截图确认首次真实调用已返回数据库事务解释；这是用户执行证据，助手未使用密钥或调用付费API。参考：[DeepSeek首次调用](https://api-docs.deepseek.com/zh-cn/)、[Requests快速入门](https://requests.readthedocs.io/en/latest/user/quickstart/)。

> 2026-10-09路径调整：文中早期数据库实验文件名保留不变，Psycopg脚本现位于`examples/database/psycopg/`，SQLAlchemy和ORM脚本位于`examples/database/sqlalchemy/`。旧示例中的直接脚本运行命令请改用[数据库实验运行说明](examples/database/README.md)中的模块方式；公共`database.py`、`orm_models.py`和`database_api_demo.py`仍在根目录。

## SQLAlchemy：`Base.metadata`与数据库表结构（2026-10-14）

### 为什么需要元数据

`Base.metadata`是SQLAlchemy保存表结构描述的`MetaData`对象。它记录表、列、数据类型、主键、外键和约束，不保存查询得到的任务记录。“元数据（Metadata）”指描述数据结构的数据：任务标题是业务数据，“title是不允许为空的文本列”是元数据。

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

继承同一个`Base`的ORM模型通常共享该对象。Python执行模型类定义时，SQLAlchemy会创建对应的`Table`结构并登记到`Base.metadata`，同时建立类与表之间的ORM映射。

```text
Base.metadata
├── tasks：任务表结构
├── tags：标签表结构
└── task_tags：关联表结构
```

模型模块必须先被导入并执行，结构才会登记；metadata不会自动扫描项目寻找模型。构造`TaskRecord(title="学习SQL")`是创建业务对象，与登记表结构是不同操作。

### 属性、类型与结构查看

`Base`是ORM基类，`Base.metadata`是`MetaData`实例，`MetaData`是SQLAlchemy提供的类。metadata是属性，访问时不用括号；调用其方法时才使用括号。

```python
from sqlalchemy import MetaData

assert isinstance(Base.metadata, MetaData)
print(Base.metadata.tables.keys())

tasks_table = Base.metadata.tables["tasks"]
assert tasks_table is TaskRecord.__table__
print(tasks_table.columns.keys())
```

`.tables`是表名到`Table`对象的映射；使用schema时，键可能是`public.tasks`。`TaskRecord.__table__`对应单张表的结构对象。以上查看的是Python内存中的结构，不会查询数据库中的任务。

### `create_all()`：根据结构描述创建表

```python
Base.metadata.create_all(
    bind=engine,
    tables=None,
    checkfirst=True,
)
```

| 参数 | 用途与默认值 |
| --- | --- |
| `bind` | 执行操作的`Engine`或`Connection` |
| `tables` | 要创建的`Table`对象序列；默认`None`，处理全部登记表 |
| `checkfirst` | 默认`True`，检查表是否已经存在 |

返回`None`，主要副作用是执行建表SQL；按外键依赖安排创建顺序。它要求目标数据库已经存在，不会创建`task_manager_learning`数据库本身。连接失败、权限不足或DDL失败时会抛出相应数据库异常。

`create_all()`适合初次建表或测试初始化，但不会自动修改已有表。模型新增列后再次调用它，不会给已有表增加该列；此类结构变更由Alembic等迁移工具管理。传入Engine时会为操作获取连接并释放所获取的资源；传入Connection时，连接与事务的生命周期由调用方管理。

### 模型描述与真实数据库的区别

| 位置 | 保存内容 |
| --- | --- |
| PostgreSQL | 实际存在的表、列、约束与业务数据 |
| `Base.metadata` | Python模型声明的表结构描述 |

即使之前已经在pgAdmin手动建表，SQLAlchemy仍需要模型映射来构造SQL。定义模型不会自动修改数据库，两者应保持匹配；列名或结构不匹配可能在执行时导致错误。

### `reflect()`：读取已有数据库结构

```python
Base.metadata.reflect(bind=engine)
```

返回`None`，连接数据库读取已有表、列和约束，将`Table`对象加载到该metadata中；此过程称为反射（Reflection）。常用可选参数包括`schema`（指定schema）和`only`（限定读取的表名）。它不会自动生成`TaskRecord`这样的ORM模型类，也不用于自动同步两端结构。连接与权限问题可能导致异常。

### `drop_all()`：删除登记的表

```python
Base.metadata.drop_all(
    bind=engine,
    tables=None,
    checkfirst=True,
)
```

返回`None`；参数含义与`create_all()`类似，会按依赖关系安排删表顺序。其副作用是删除真实表及其中数据，而不是清空Python中的结构描述。当前仅认识用途，不应对练习数据库随意执行；实际操作需要按项目高影响操作规则确认。

### 在当前项目调用链中的位置

```text
Base.metadata：描述表结构
Engine：管理连接和连接池
Session：组织ORM查询、修改与事务
TaskRecord实例：表示一条任务
```

`select(TaskRecord)`利用模型映射及表结构构造SQL，Session通过数据库连接执行，查询结果再转成ORM对象。metadata提供结构信息，本身不保存这些查询结果。

## Alembic：让数据库结构变化可追踪（2026-10-14）

### 为什么项目需要Alembic

`orm_models.py`描述Python代码期望的目标结构，PostgreSQL保存真实表结构，Git记录源码版本；修改ORM模型不会自动修改已经存在的表。例如给`TaskRecord`增加`description`映射后，数据库中的`tasks`表仍然没有该列。Alembic使用按顺序排列的Python迁移脚本，明确记录数据库应怎样从旧结构变成新结构。

```text
ORM模型：目标结构
      ↓ 比较
迁移脚本：从旧结构到新结构的操作
      ↓ upgrade
PostgreSQL：实际结构
```

Git管理代码和迁移文件，Alembic管理表、列、外键、索引等数据库结构；任务和标签等业务数据仍由应用代码管理。

### Alembic与`create_all()`的区别

`Base.metadata.create_all()`适合在空数据库或测试环境创建尚不存在的表。表已经存在时，它不会因为ORM模型新增字段就自动对旧表执行`ALTER TABLE`。Alembic则会把新增列等变化记录成可以审查和重复执行的迁移操作，例如：

```python
def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("description", sa.Text(), nullable=True),
    )
```

这使开发机、测试环境和部署环境能够按照同一版本链演进，而不需要删除已有表和数据。

### 迁移环境中的文件

执行`alembic init alembic`后通常生成：

```text
alembic.ini
alembic/
├── env.py
├── script.py.mako
├── README
└── versions/
```

| 文件或目录 | 作用 |
| --- | --- |
| `alembic.ini` | 主配置文件，保存迁移目录、日志等配置；真实密码不应写入并提交 |
| `env.py` | `current`、`upgrade`及自动生成等需要迁移环境的命令会执行它，负责数据库连接、加载模型及配置迁移上下文；并非所有Alembic命令都会运行它 |
| `script.py.mako` | 创建新迁移文件时使用的模板 |
| `versions/` | 保存各个版本的迁移脚本 |

为了让自动生成看见当前项目的ORM结构，`env.py`需要导入模型基类并设置：

```python
from orm_models import Base

target_metadata = Base.metadata
```

模型模块必须先被导入执行，表结构才会登记到metadata。`target_metadata`是Alembic拿来与真实数据库结构比较的目标。

### 从`current`理解配置文件与运行流程

```powershell
python -m alembic current
```

`python -m alembic`使用当前Python环境运行Alembic包；`current`是命令参数，要求查看数据库登记的迁移版本。在项目根目录执行时，默认使用`alembic.ini`。执行链为：准备Config对象并读取配置 → 定位迁移目录 → 执行env.py → 配置日志和迁移环境 → 建立连接 → 查询当前迁移版本。

INI是配置格式，不是Python代码：`#`表示注释，`[alembic]`表示配置分组，`名称 = 值`表示配置项。

```ini
[alembic]
script_location = %(here)s/alembic
prepend_sys_path = .
```

`%(here)s`表示INI所在目录；`script_location`帮助Alembic找到迁移环境。`prepend_sys_path`帮助Python找到导入的模块，其中`.`表示运行命令时的当前工作目录，两者的相对路径基准不能混淆。从项目根目录运行时，Python可以找到`database.py`和`orm_models.py`。

```python
from alembic import context

config = context.config
```

`context`是Alembic提供的模块，可访问当前运行环境；`context.config`取得已有的`Config`对象，赋值给变量`config`。此赋值本身不创建配置对象，也不重新读取文件。`alembic.ini`是磁盘文件，`Config`是内存中的配置对象，`config`是引用它的变量名。Config也可以在没有INI文件时由程序创建，不能理解成必须先读文件才能创建对象。

| 当前涉及的Config接口 | 参数、返回值与作用 |
| --- | --- |
| `get_main_option(name, default=None)` | 按名称读取主分组配置；返回字符串或默认值，本身不连接数据库 |
| `set_main_option(name, value)` | 两个参数是配置项名称与字符串值；返回None，修改内存配置，不写回INI |
| `config_file_name` | 属性，保存INI路径或None；访问时不加括号 |

`current`查看迁移版本，不是查看所有表结构，也不会比较模型差异。已有三张业务表但没有登记版本时，可以没有版本号输出；这不意味着没有表。当前生成的env.py根据命令准备环境，查询版本不会执行upgrade；但env.py是可执行Python文件，人为加入的额外代码仍会执行。

### `context`的身份及与`config`的区别

`from alembic import context`导入的是代理模块，访问会转交给当前命令使用的EnvironmentContext对象。运行环境由Alembic建立，因此env.py不需要自己写`context = ...`。EnvironmentContext协调命令配置和执行环境；configure建立更底层的MigrationContext，组织数据库连接、数据库类型和迁移选项。

`config`负责读取或修改配置项，Engine负责获取连接，Connection执行数据库操作，Base.metadata提供模型结构描述；context是把这些信息用于本次迁移命令的统一入口。

```text
config.set_main_option() → 修改内存中的配置项
engine_from_config()    → 读取配置，创建Engine
Engine.connect()        → 获取真实Connection
context.configure()     → 配置本次迁移运行环境
context.run_migrations() → 执行当前命令安排的操作
```

因此set_main_option不是直接创建或配置已有Engine，configure也不是生成迁移脚本文件。前者回答“配置中填写什么值”，后者回答“本次操作使用哪个连接和哪些结构信息”。

context接口速查（详细执行流程见后续各段）：

| 接口 | 参数、返回值与使用条件 |
| --- | --- |
| `context.config` | 属性，取得本次命令使用的Config对象 |
| `is_offline_mode()` | 无参，返回bool，判断运行模式 |
| `configure(...)` | 返回None，配置MigrationContext；connection和target_metadata默认None；compare_type默认True，compare_server_default默认False |
| `begin_transaction()` | 无参，返回事务上下文管理器；具体效果依赖数据库和模式 |
| `run_migrations(**kw)` | 当前无参调用，返回None；执行当前命令安排的流程，可选关键字参数可传给迁移函数 |
| `get_context()` | 无参，返回已配置的MigrationContext；必须先configure |
| `get_bind()` | 无参，在线模式取得当前配置的Connection，不创建独立连接；必须先configure |

get_context和get_bind仅介绍用途，当前无需使用。env.py依赖Alembic准备的运行环境，直接作为普通Python脚本运行不能假定这些接口可用。

### 日志配置逐行说明

```python
from logging.config import fileConfig

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
```

第一行从Python标准库导入日志配置函数。条件检查是否存在配置文件路径；随后按文件中的日志分组设置输出级别、输出目标和格式。`fileConfig()`第一个参数是配置文件路径（也支持文件对象等），返回None；默认`disable_existing_loggers=True`可能禁用已有的非根日志记录器。文件存在不保证日志配置完整，缺少所需日志分组仍可能报错。

例如`INFO [alembic.runtime.migration] ...`是普通运行信息，不等于报错。日志配置影响程序的日志行为，不负责定义表结构或建立业务数据。

### 数据库URL配置与百分号转义

`database_url`是SQLAlchemy的URL对象。`render_as_string(hide_password=True)`返回字符串，默认隐藏密码；连接配置需要真实凭据时使用False，不能将结果打印到日志或写入仓库。调用`config.set_main_option()`只覆盖运行时配置，不把真实密码写回INI。

此前示例还需补足一个细节：ConfigParser把百分号当作插值语法，而URL编码可能包含百分号。写入配置时要转义：

```python
config.set_main_option(
    "sqlalchemy.url",
    database_url.render_as_string(hide_password=False).replace("%", "%%"),
)
```

这一步只适用于经过ConfigParser的配置值，读取配置后百分号恢复；不要把加倍的百分号直接传给数据库驱动。

`str.replace(old, new, count=-1)`返回替换后的新字符串，不修改原字符串；old是被替换文本，new是替代文本，count默认-1表示替换全部匹配。例如`"%40".replace("%", "%%")`得到`"%%40"`。写入配置时转义，读取配置时恢复`%40`，再由URL解析处理；这不是修改真实密码。此前省略replace的示例对不含百分号的URL可能运行正常，但不适合包含URL编码字符的通用情况。

### `target_metadata`逐段理解

```python
from orm_models import Base
target_metadata = Base.metadata
```

导入会执行模型模块，使类映射和`Table(..., Base.metadata, ...)`登记表结构。第二行让变量引用同一个MetaData对象，不会复制结构，也不连接或改变数据库。项目的关联表虽然没有单独的ORM类，也因Table构造时传入Base.metadata而被登记。

后续`context.configure(connection=connection, target_metadata=target_metadata)`把数据库连接和模型结构分别交给迁移环境：连接用于访问实际数据库，metadata用于自动生成时描述目标。完整方法与事务生命周期留待下一小节展开。

模型里新增列而未执行迁移时，两端仍不一致。`target_metadata=None`也不是要求删除所有表，而是未提供目标元数据，自动生成通常会因此报错；空MetaData对象则是另一种情况。

参考：[Config接口](https://alembic.sqlalchemy.org/en/latest/api/config.html)、[Python日志配置](https://docs.python.org/3/library/logging.config.html)。

### 在线与离线分支的执行顺序

```python
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

`context.is_offline_mode()`不需要参数，返回bool；判断本身不连接数据库。在线和离线指是否通过真实数据库连接执行，不是电脑是否联网。`current`需要读取数据库版本，走在线分支；支持`--sql`的迁移命令可以走离线分支生成SQL文本。

`def run_migrations_online() -> None:`执行时定义函数，不立即运行函数体；文件底部调用才执行。`-> None`是返回类型注解，表示不提供有意义的返回结果。当前if/else一次只调用一个分支。

### 从配置字典创建Engine

```python
connectable = engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)
```

按求值顺序解释：

1. `config.config_ini_section`是属性，默认字符串`"alembic"`，对应INI中的`[alembic]`分组。
2. `config.get_section(name, default=None)`读取该分组，返回配置字典；此处显式传入`{}`，分组不存在时返回空字典。缺少URL仍会导致后续创建Engine失败。
3. SQLAlchemy的`engine_from_config(configuration, prefix="sqlalchemy.", **kwargs)`从字典筛选带此前缀的键，并去掉前缀。例如`sqlalchemy.url`变成`url`；`script_location`不作为Engine参数。部分受支持的字符串值会转换成相应类型。
4. `poolclass=pool.NullPool`指定连接管理类；传入类本身，不需要括号。SQLAlchemy内部负责构造实例，显式关键字参数可以覆盖配置字典中的对应选项。
5. 返回Engine对象，变量`connectable`引用它；与`create_engine()`的主要差别是参数来自配置字典。

连接池可以保留连接以供复用；NullPool在每次需要时建立连接，关闭时关闭底层连接，不缓存供后续复用。它不是关闭事务，也不意味着无法连接数据库。

创建Engine通常还没有建立真实连接，成功不证明密码正确或数据库可达。URL格式、驱动加载等问题可能在创建时暴露，认证和网络问题通常在获取连接时暴露。

### Connection生命周期与迁移环境配置

```python
with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
```

`Engine.connect()`当前用法无需参数，返回SQLAlchemy Connection对象，获取真实连接时可能因认证失败、服务不可达等抛出数据库异常。Session提供ORM对象查询与修改跟踪，底层使用Connection；Alembic处理结构操作，直接使用Connection。

外层with在正常结束或异常退出时关闭Connection。当前NullPool策略会同时关闭底层连接；其他连接池策略可能把连接归还池中。连接资源清理不等于提交事务；关闭时尚未结束的事务会被回滚。

`context.configure()`返回None，配置本次迁移上下文。`connection`参数默认None，在线模式传入真实Connection；`target_metadata`默认None，自动生成时传入模型MetaData作为目标。两者分别回答“通过哪个连接访问数据库”和“模型期望什么结构”。`connection=connection`左侧是参数名，右侧是变量引用。

此配置操作不直接执行升级或创建业务表。其后需要运行本次命令对应的操作。当前上下文由Alembic命令建立，通常不把env.py当作普通独立脚本直接运行。

参考：[SQLAlchemy引擎配置](https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.engine_from_config)、[连接池](https://docs.sqlalchemy.org/en/20/core/pooling.html#sqlalchemy.pool.NullPool)、[Alembic运行环境](https://alembic.sqlalchemy.org/en/latest/api/runtime.html)。

### 事务块与`run_migrations()`

```python
with context.begin_transaction():
    context.run_migrations()
```

`context.begin_transaction()`无需参数，返回供with使用的上下文管理器。在当前PostgreSQL在线模板中，没有外部事务接管时，它为通常的事务性DDL建立事务范围，正常退出提交、异常传播时回滚。DDL指CREATE TABLE、ALTER TABLE等定义结构的SQL；特殊自动提交操作、其他数据库和外部事务不应直接套用此结论。离线模式可输出BEGIN/COMMIT文本而不建立真实事务。

`context.run_migrations()`当前无需参数，返回None，运行当前命令预先安排的操作。`current`安排读取并显示版本，不执行升级脚本；`upgrade head`安排根据当前版本和目标版本依次运行待执行的upgrade函数。方法名不能理解成每次都升级到最新版本。

执行顺序为：外层with获取连接 → configure配置上下文 → 内层with管理事务 → run_migrations执行命令操作 → 内层退出提交或回滚 → 外层退出关闭连接。当前尚未实际验收连接或运行迁移，以上为原理讲解。

异常处理遵循从内到外的退出顺序：若run_migrations内部异常向外传播，先退出事务with并回滚该事务内的操作，再退出连接with关闭Connection；当前NullPool会关闭底层连接。清理不等于吞掉异常，异常通常继续传播并使命令失败。回滚只针对尚未提交且受该事务管理的操作，不会撤销此前已提交的修改。

### 首次连接验收：`current`

在设置了`TASK_MANAGER_DB_PASSWORD`环境变量的终端中，从项目根目录运行：

```powershell
& "D:\Python\Project\.venv\Scripts\python.exe" -m alembic current
```

当前项目的database.py在导入时读取该环境变量；如果变量缺失，会先出现KeyError，尚未尝试数据库认证。命令成功、显示PostgreSQL运行日志但没有版本号，可以表示尚未登记迁移版本，并非数据库没有表。验收应同时确认没有异常、进程成功退出；这只验证迁移环境可以查询版本，不代表业务表与ORM完全一致，也不代表已经生成或执行迁移。

### 迁移脚本及版本链

迁移文件的核心结构是：

```python
revision = "当前版本ID"
down_revision = "上一个版本ID"


def upgrade() -> None:
    ...


def downgrade() -> None:
    ...
```

- `revision`唯一标识当前迁移。
- `down_revision`指向上一个迁移；首个迁移为`None`。
- `upgrade()`执行向前的结构变化。
- `downgrade()`描述怎样撤销这一版本的结构变化。

数据库中的`alembic_version`表记录该数据库当前位于哪个版本。Alembic把这个版本与迁移脚本链比较，决定还需执行哪些`upgrade()`或`downgrade()`。

### 当前阶段涉及的常用命令

```powershell
alembic init alembic
```

`init`初始化一次迁移环境；后面的`alembic`是目标目录名。它的副作用是创建配置、模板和版本目录，不会直接修改业务表。

```powershell
alembic revision --autogenerate -m "add task description"
```

- `revision`创建迁移版本。
- `--autogenerate`比较真实数据库与`target_metadata`，生成候选操作。
- `-m`提供迁移说明，用于文件名和脚本头部。

自动生成结果必须人工审查。它能发现许多表、列、可空性、基础外键和约束变化，但不能可靠判断列重命名或表重命名；重命名可能被误判为“删除旧对象并创建新对象”，从而造成数据风险。

```powershell
alembic upgrade head
alembic current
alembic history
alembic downgrade -1
```

| 命令 | 作用 |
| --- | --- |
| `upgrade head` | 从数据库当前版本依次执行到最新版本，并更新`alembic_version` |
| `current` | 查看目标数据库当前登记的迁移版本 |
| `history` | 查看迁移脚本形成的版本链 |
| `downgrade -1` | 执行当前迁移的`downgrade()`回退一步 |

`downgrade`可能删除列或表。数据库结构可以回退并不代表被删除的数据一定能够恢复，因此它不是绝对安全的撤销按钮。

### 创建文件、执行迁移与登记版本

| 操作 | 结果及副作用 |
| --- | --- |
| `revision -m "说明"` | 创建迁移脚本；默认模板和配置下不比较数据库，upgrade/downgrade为空骨架 |
| `revision --autogenerate -m "说明"` | 连接数据库比较模型，生成候选迁移文件，仍需人工审查 |
| `upgrade <版本>` | 执行到目标版本所需的升级操作，并更新数据库版本记录 |
| `stamp <版本>` | 登记数据库版本，不执行升级脚本；必要时建立版本表，不自动验证或修复业务表结构 |

版本脚本存在，不代表数据库已经应用该版本；空白骨架生成也不代表完整基线已建立。对现有数据库stamp之前，必须核对真实结构与该版本一致。全新数据库则需要执行完整基线的建表操作。

本项目首个骨架由`python -m alembic revision -m "create initial task tables"`生成：`042f491f9a4a_create_initial_task_tables.py`。版本标识为042f491f9a4a，down_revision为None；当前函数体仍为pass，尚未执行或登记该版本。

### 阅读首个迁移骨架

文件顶部三引号内容是模块文档字符串，记录说明、版本和生成时间；真正用于组织迁移链的是下面的revision、down_revision等变量。`revision: str`是类型注解，右侧字符串为本版本ID；`down_revision=None`表示没有前驱版本。模板中的`Union[str, Sequence[str], None]`表示允许字符串、字符串序列或None，用于兼容普通迁移及多前驱场景；当前单链保持生成值即可。`branch_labels`为迁移分支命名，`depends_on`声明额外迁移依赖；两者当前均为None，不等于Git分支设置。

`import sqlalchemy as sa`为SQLAlchemy模块起别名；`from alembic import op`导入迁移操作的代理模块，背后是当前环境的Operations对象。context主要用于env.py组织环境，op主要用于迁移脚本描述具体结构操作。

upgrade和downgrade由Alembic在相应命令下调用，返回None；pass只是空语句。创建Python文件不执行函数体，文件也不应通过普通Python脚本运行来代替迁移命令。

### `op.create_table()`：描述并执行建表操作

当前常用形式为`op.create_table(table_name, *columns, schema=None)`，首个参数是表名，后续位置参数是SQLAlchemy Column或约束对象；schema默认None，使用连接的默认schema规则。返回SQLAlchemy Table对象，常规建表迁移可以不接收返回值。在线模式调用时执行建表SQL，离线模式输出SQL；表已存在、权限或约束问题可能导致异常。

最小示例仅用于理解语法，不是项目基础表的最终实现：

```python
op.create_table(
    "example_notes",
    sa.Column("content", sa.Text(), nullable=False),
)
```

sa.Text()构造SQL类型描述对象，sa.Column构造列对象；Column的前两个位置参数分别是列名和类型，nullable=False表示NOT NULL（普通非主键列默认通常可空）。Column对象的构造不直接建表，由外层op.create_table执行建表指令。下一步填写真实基础表前，需核对identity、数据库默认值、约束和外键；不直接把当前ORM声明当作现有数据库结构的完整证据。

进一步区分：“描述列”不等于“在数据库中创建列”。例如`column = sa.Column("content", sa.Text(), nullable=False)`只创建内存中的Column对象；把它传给`op.create_table("example_notes", column)`，才由迁移操作创建包含该列的表。给已有表添加列需要使用另外的操作`op.add_column()`，留到后续字段迁移时学习。

参考：[Alembic命令](https://alembic.sqlalchemy.org/en/latest/api/commands.html)、[迁移操作](https://alembic.sqlalchemy.org/en/latest/ops.html#alembic.operations.Operations.create_table)。

### 基础迁移中的自增主键：`sa.Identity()`

2026-10-14只读核对现有数据库：tasks和tags的id均为INTEGER、主键、GENERATED ALWAYS AS IDENTITY；tags.name为TEXT、NOT NULL、UNIQUE。tasks.done的数据库默认值为false，priority为'normal'；task_tags使用联合主键，两个外键均为ON DELETE CASCADE。本次只查询结构，未执行迁移或版本登记。

`sa.Identity()`是SQLAlchemy的自增身份列描述对象，通常作为Column的位置参数传入。当前使用`sa.Identity(always=True)`：always默认False，在PostgreSQL中对应GENERATED BY DEFAULT；True对应GENERATED ALWAYS，普通INSERT不能随意显式指定该列的值。特殊导入覆盖机制以后按需学习。

```python
sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True)
```

这里Integer描述SQL整数类型；Identity描述由数据库生成编号的规则；primary_key=True声明主键，保证唯一且非空。Identity本身不保证唯一，序列编号也不保证连续。Identity构造返回Identity对象，不立即连接数据库或生成编号；执行建表操作时规则落入数据库，之后插入行时才实际生成编号。本阶段不需调用Identity对象的其他方法。Column的primary_key和unique默认均为False；为标签name设置unique=True表示该列的值不能重复。

初始核对时ORM的id尚未显式声明Identity，done/priority仅有Python侧default。2026-10-15学习者已补充两张主表的Identity(always=True)和done的server_default；priority默认表达式仍有引号问题待修正。基础迁移和模型均需描述真实数据库规则，不能仅凭Python侧default认为两者完全一致。

2026-10-14练习验收：已在首个迁移的upgrade中编写tags建表操作，id使用Integer、Identity(always=True)、primary_key=True；name使用Text、nullable=False、unique=True。临时离线SQL生成检查通过，输出包含GENERATED ALWAYS AS IDENTITY、PRIMARY KEY (id)、name TEXT NOT NULL和UNIQUE (name)。主键即使没有单独写nullable=False，也在数据库中要求非空。该检查没有连接数据库，证明当前操作能生成预期PostgreSQL DDL，不代表完整迁移已执行或通过数据库往返验证；tasks、task_tags和downgrade仍待完成。

参考：[SQLAlchemy Identity列](https://docs.sqlalchemy.org/en/20/core/defaults.html#identity-columns-generated-always-by-default-as-identity)。

### 迁移中的默认值：`default`与`server_default`

2026-10-21接口增量：调用方法时位置参数按形参顺序绑定，description作为第四个显式参数时可写task.description，也可写description=task.description明确指定；self由实例方法调用自动绑定。TaskResponse的from_attributes=True允许读取ORM属性；tags的before校验器先将TagRecord对象转换为name字符串，再按list[str]校验，description本身是字符串则无需额外转换。

PATCH备注必须区分省略、空串、null：TaskUpdate使用str|None且default=None，路由model_dump(exclude_unset=True)排除未提供字段；{}保留原备注，显式空串清空，显式null仍留在字典并由Service拒绝。当前null经Service返回400，数字或超长文本由请求模型返回422。Service仍需独立类型校验，以支持非HTTP调用；测试必须既检查接口行为，也直接调用Service，避免Pydantic掩盖业务层遗漏。

备注隔离测试使用内存SQLite验证接口与Service协作，不替代PostgreSQL迁移验收；Mock替代Repository检查非法输入不调用保存。tests/test_task_description.py通过get_session依赖替换让真实路由使用内存Session，结束后恢复依赖并释放引擎。该套件不覆盖PostgreSQL专有特性或完整历史回归。

#### 备注测试的执行链与连接生命周期（2026-10-22）

description_client是默认function作用域的fixture，每个参数化用例都重新创建Engine、内存库和TestClient。create_all按当前Base.metadata建表，不执行Alembic。内部override_session只是先定义函数；app.dependency_overrides[get_session] = override_session登记替换规则，请求到来后FastAPI才调用它，每次请求在with Session(engine)中创建会话并通过yield提供给真实路由。fixture的yield client则由pytest接收，绑定到测试函数的description_client参数；两处yield的管理者不同。TestClient直接调用应用，无需启动Uvicorn或占用8000端口。finally先恢复此前copy保存的依赖字典，再dispose引擎；即使断言失败也执行清理。

普通SQLite内存数据库通常跟底层连接关联：连接A建表，连接B可能访问另一个没有表的内存库。StaticPool通常只维护一个底层连接，使本用例的建表、POST、GET等操作共享数据；不同请求仍有不同Session。check_same_thread=False只是允许SQLite连接跨线程使用，不会让所有操作自动选择同一连接，也不保证任意并发安全。TestClient可能涉及不同线程，所以两项配置配合使用。本测试按顺序请求；每个用例有独立引擎，因此用例之间不共享数据。连接池释放或连接失效后连接可能重建，StaticPool不表示永久保持同一连接。

engine.dispose(close=True)针对当前Engine的连接池，不处理其他Engine；对常见池会关闭已归还的空闲连接并替换池，不强制关闭仍被借出的连接，使用者仍需关闭它们。StaticPool本例在请求Session结束后释放其连接资源。dispose不使Engine永久失效，后续仍可建新连接，但内存数据库内容不能指望保留。Session.close管理当前会话资源，Connection.close在常见池化场景中归还连接，不能与Engine.dispose混为一谈。

接口测试先POST准备数据，检查创建响应，再GET详情/列表确认数据库读取结果；PATCH测试先创建original，再修改并重新查询，区分省略保留与空白清空。json={"title": "test", **fields}用字典展开组合请求，f"/tasks/{task['id']}"用返回ID构造路径。参数化数量为4+3+5+3+2×3，共21例，不是21个函数。用例验证非法单字段修改不破坏备注，不代表已覆盖多字段更新中途失败的所有回滚场景。

参考：[StaticPool](https://docs.sqlalchemy.org/en/21/core/pooling.html#sqlalchemy.pool.StaticPool)、[跨线程SQLite内存库](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html#using-a-memory-database-in-multiple-threads)、[Engine释放](https://docs.sqlalchemy.org/en/21/core/connections.html#engine-disposal)。

#### Mock为何能够代替Repository（2026-10-22）

Mock()是构造Mock类实例，repository只是变量名，不会推断或转换成TaskRepository。普通Mock访问尚不存在的普通属性时可生成子Mock；repository.get_by_id.return_value = task配置该模拟方法调用时返回task，不查询数据库。TaskService构造参数的类型注解不自动强制运行时类型检查，因此可接收能响应所需调用的模拟对象。assert_not_called()检查对应模拟方法从未被调用。Mock(spec=TaskRepository)可限制按参照对象允许的属性，但仍是模拟对象，不执行真实Repository逻辑。

2026-10-23结合候选生成测试补充：Mock记录自身被调用的次数与参数，也允许配置调用结果。配置语句不等于调用；必须等被测程序真正执行对应方法，才产生相应调用记录或异常。

| 写法 | 含义 |
| --- | --- |
| `mock.return_value = value` | 没有其他覆盖行为时，调用Mock返回value |
| `mock.side_effect = error` | 此处error为异常对象；每次调用Mock时抛出它，不正常返回return_value |
| `mock.call_args` | 最近一次调用的记录；从未调用时是None |
| `mock.call_args.args` | 最近调用的位置实参元组 |
| `mock.call_args.kwargs` | 最近调用的关键字实参字典 |
| `mock.assert_called_once()` | 只要求恰好调用一次，不限制实参 |
| `mock.assert_called_once_with()` | 要求恰好调用一次，而且这次没有传任何实参 |
| `mock.assert_called_once_with(value)` | 要求恰好调用一次，且实参与给定value匹配 |
| `mock.assert_not_called()` | 要求从未调用 |

这些断言方法成功返回None，失败抛AssertionError，因此直接调用，不写`assert mock.assert_called_once()`。普通Mock的方法属性可以是子Mock：`response.json.return_value = body`配置的是`response.json()`的返回值；`response.json = body`则会把该方法属性直接换成body，无法起到相同作用。

**assert_called_once_with的具体执行过程：**

```python
fake_function = Mock()
fake_function("Read docs", priority="high")  # 真正调用，并记录这次实参。
fake_function.assert_called_once_with(
    "Read docs", priority="high",
)  # 对照记录检查“恰好一次，且参数符合预期”；不会再次调用fake_function。
```

调用处的参数是实际输入，断言处的参数是预期输入；把断言中的priority改成`"low"`会失败。对于当前这种普通、未绑定签名的Mock，按记录中的位置实参和关键字实参检查，不把断言参数当作第二次调用的输入。

当前业务代码使用`response.raise_for_status()`，所以测试写`response.raise_for_status.assert_called_once_with()`：要求该子Mock被调用一次，且没有任何实参。空括号不表示忽略参数。

| 各独立场景中的实际调用 | 无参数的assert_called_once_with()结果 |
| --- | --- |
| 从未调用 | 失败：次数为0 |
| 调用一次`raise_for_status()` | 通过：一次且无参数 |
| 调用两次`raise_for_status()` | 失败：次数为2 |
| 调用一次`raise_for_status(123)` | 失败：参数不匹配 |

因此漏掉状态检查时，该断言会因次数为0失败。它检查“程序有没有调用这一步”，不说明Mock真的检查了HTTP状态码；模拟HTTP失败需要另给该子Mock设置side_effect。若只关心次数，使用assert_called_once()。

`side_effect`还支持函数或可迭代对象，本轮只使用“异常对象”形式；不要把它理解为只能执行一次的开关。完整双Mock执行链见阶段五的离线测试章节。参考：[Mock返回值、异常模拟与调用断言](https://docs.python.org/3/library/unittest.mock.html#the-mock-class)。

直接Service测试不请求description_client，因此不创建内存库；TaskRecord仅是未保存的对象。Mock返回该对象，真实Service对非法值抛ValueError，随后检查对象未修改、add_task及标签查询未调用。创建分支中的原对象未被使用，故对象不变断言的主要意义在更新分支；更新本来不调用add_task，不能单凭未调用add_task证明更新安全。参考：[Python Mock文档](https://docs.python.org/3/library/unittest.mock.html#the-mock-class)。

2026-10-21备注实现补充：在SELECT中，`description = '' AS description_is_empty`先比较该行备注是否等于空字符串，再用AS为结果列起别名；不是赋值，也不新增或保存字段。空串得到true，非空文本或纯空格得到false，NULL比较得到NULL；检查NULL应使用IS NULL。

Service按“类型校验→strip→清理后长度校验→构造对象→数据库操作”的顺序处理备注。isinstance(description, str)返回是否为字符串，必须先于strip，避免None引发AttributeError；长度在strip后检查，符合清理后最多500字符的规则。普通TaskRecord(...)仅创建内存对象，不立即INSERT；只要依赖值已就绪，提前构造通常能运行，但放在输入校验之后更清楚，也避免创建随后被弃用的对象。非法输入在标签查询和保存之前失败，可减少不必要的数据库操作。

2026-10-21补充：固定文本默认值可直接传普通字符串，如`server_default=""`、`server_default="normal"`或`server_default="暂无备注"`，SQLAlchemy会处理SQL字符串字面量的引用。使用`text(...)`时，内容是SQL表达式：`text("''")`表示SQL空字符串，`text("")`没有有效表达式，不能表示空字符串。`server_default=text("CURRENT_TIMESTAMP")`表示由数据库计算当前时间；普通字符串`"CURRENT_TIMESTAMP"`表达的是固定文本，不能替代时间计算。

例如备注列同时声明`default=""`和`server_default=""`：前者由SQLAlchemy组织插入时使用，后者描述数据库的DEFAULT规则。迁移为已有表增加`nullable=False`且数据库默认值为空字符串的新列时，旧记录在新增列上的值可得到空字符串，其他字段保留；仅修改模型不会改变数据库。默认值主要处理INSERT省略该列的情况，不是通用的输入清洗规则：主动传空字符串不会自动换成其他默认文本，显式SQL NULL也不会自动触发DEFAULT；ORM对象中的None是否被省略需结合映射和实际INSERT判断。因此接口仍需明确拒绝null、去除首尾空白，并在规范化后检查长度。

备注需求的调用链是：请求JSON→TaskCreate校验→路由传参→TaskService规范化并构造TaskRecord→数据库保存→TaskResponse从对象属性读取→响应JSON。列表查询完整TaskRecord时，新增普通列会随对象加载；仅为了返回备注，无需给Repository.list_tasks增加备注过滤形参。models.py和service.py属于旧CLI/JSON链路，本轮正式API需求不涉及它们。

学习笔记后续按AGENTS.md“文档维护与交接”中的主动归档规范维护：每推进4～5轮检查增量知识并合并，用户明确要求时即时整理。

`default`由SQLAlchemy在组织插入时使用，不会在建表SQL中生成数据库DEFAULT规则。当前普通ORM模型的default通常在执行插入时生效，不代表刚构造Python对象就已赋值。`server_default`是Column的关键字参数，默认None；它描述数据库端默认值，在建表时写入表结构。因此从pgAdmin或其他客户端插入并省略该列，也能使用数据库默认值。

本项目迁移的done列需要`server_default=sa.text("false")`，priority列需要`server_default=sa.text("'normal'")`，分别描述SQL中的`DEFAULT false`和`DEFAULT 'normal'`。`sa.text()`接收SQL文本，返回TextClause描述对象，本身不执行SQL；这里由建表操作将描述写入DDL。外层双引号属于Python字符串语法，内层单引号表示SQL字符串字面量；SQL布尔值false不需单引号。

2026-10-14代码检查发现：学习者首次编写tasks时仍用了`default=False`和`default="'normal'"`，尚不满足数据库默认值要求。后者还有另一层问题：default接收Python字符串时不应额外加入SQL引号，否则字符串内容本身包含单引号。Python侧默认字符串写作`default="normal"`；本次迁移应改用前述server_default，而不是仅修改引号。

默认值不等于校验规则：默认normal不限制其他优先级字符串。原始INSERT显式提供NULL时不会使用默认值，本表会因NOT NULL拒绝该值。仅声明或修改Python中的列描述不会自动修改现有数据库，必须通过相应DDL操作落实。

**2026-10-15补充：为什么ORM模型中可以同时保留两种默认值？**

以done为例，`default=False`由SQLAlchemy在组织插入时补值；`server_default=text("false")`描述数据库应具有的DEFAULT规则。经ORM插入且未提供done时，Python侧default可以先提供False，数据库收到明确的值后就无需再使用数据库默认值；在pgAdmin直接执行省略done的INSERT时，不经过Python模型，只能依靠数据库实际存在的DEFAULT false。两者可以同时声明并应保持一致，但并非必须成对使用：对当前固定默认值，只要数据库规则已正确建立，单独使用server_default也能让省略该列的ORM插入由数据库补值。

`server_default`虽然描述数据库层面的规则，代码本身仍写在Python模型中。SQLAlchemy读取mapped_column定义后，将它记录在Base.metadata的表结构描述中；这不是数据库把规则反向通知ORM，也不会自动读取数据库确认声明是否属实。“让模型知道规则”的准确含义是开发者在模型中主动声明该规则。

| 信息所在位置 | 示例 | 信息来源 |
| --- | --- | --- |
| PostgreSQL实际表结构 | done DEFAULT false | 已实际执行的建表或修改表SQL |
| ORM的Base.metadata | server_default=text("false") | Python模型中的列声明 |

这两份信息不会自动同步。本次模型补充server_default是使其描述与数据库已有规则一致；若数据库原本没有默认值，只补Python声明并不能使真实表产生默认值。Alembic可比较元数据与实际结构以辅助生成迁移，但数据库默认值比较需启用compare_server_default（默认False），不能仅凭模型声明认为数据库已正确配置。

后续验收：学习者已修正上述两个迁移参数；临时离线SQL检查确认生成`done BOOLEAN DEFAULT false NOT NULL`和`priority TEXT DEFAULT 'normal' NOT NULL`。此次只验证SQL生成，没有连接数据库或实际创建表。

2026-10-15模型对齐时再次出现`server_default=text("normal")`：text将内容作为SQL表达式保留，normal没有SQL单引号会被视为标识符，而非字符串值；用于PostgreSQL列默认值时不是所需的常量表达式。应写作`server_default=text("'normal'")`，同时保留`default="normal"`。构造描述对象本身通常不会暴露此问题，实际DDL或默认值比较才可能报错；仅修改模型也不会立即改变已存在的正确数据库默认值。

#### `compare_server_default`：把数据库默认值纳入结构比较

它是Alembic的`context.configure()`关键字参数，默认False。本阶段设置True，表示在自动生成迁移或运行check时，将真实数据库的普通列默认值与target_metadata中的server_default进行比较；不比较Python侧default。设置False是跳过这项比较，不会关闭数据库已有默认值，也不会阻止已写好的迁移操作修改默认值。它不是一个单独返回检查结果的函数；configure返回None，该参数配置后续比较行为。

```python
context.configure(
    connection=connection,
    target_metadata=Base.metadata,
    compare_server_default=True,
)
```

connection提供实际数据库结构的来源，target_metadata提供模型目标结构，compare_server_default控制默认值是否纳入比较。配置本身不修改表。

| 实际数据库 | 模型声明 | 开启比较后的含义 |
| --- | --- | --- |
| priority DEFAULT 'normal' | server_default=text("'normal'") | 默认值一致，无需产生该项变更 |
| priority DEFAULT 'normal' | server_default=text("'high'") | 默认值不同，可能生成改为high的候选操作 |
| done DEFAULT false | 只有default=False，没有server_default | 模型没有数据库默认值，可能生成移除DEFAULT的候选操作 |

第三种情况解释了为什么要先补齐模型描述：模型遗漏不一定被理解成“保留现状”，而可能被当成希望删除数据库规则。Python侧default不会抵消server_default缺失造成的差异。

| 命令 | 发现差异后的行为 |
| --- | --- |
| alembic check | 检查是否存在待生成的迁移操作，存在时失败并报告，不生成迁移文件或执行结构变更 |
| alembic revision --autogenerate | 生成候选迁移文件，必须审查，不立即修改数据库结构 |
| alembic upgrade head | 执行已有迁移文件中的操作；不会因为开启比较就自动推导并应用模型变更 |

典型流程为“修改模型→比较发现差异→生成并审查迁移→执行迁移→数据库规则改变”。将数据库默认值由normal改为high，通常影响以后省略该列的插入，不自动更新已有行。若Python侧仍保留default="normal"，ORM插入可能继续明确提供normal，因此默认值变更还应检查两层配置是否一致。

默认值可能是SQL表达式，比较不是简单字符串匹配，也并非在所有后端都完全可靠；PostgreSQL在部分情况下会查询求值表达式以判断等价性，所以检查可以访问数据库，复杂表达式需审查检测结果。该参数也支持自定义比较函数，本阶段只使用True/False，不展开回调实现。开启它不表示已验证所有数据库结构或业务行为。

参考：[Alembic配置参数](https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure.params.compare_server_default)、[自动生成与check](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)。

### 迁移中创建中间表及编写回退

task_tags必须在被引用的tasks和tags之后创建。task_id、tag_id均为Integer，分别通过`sa.ForeignKey("tasks.id", ondelete="CASCADE")`和对应的tags.id外键引用现有编号，不设置Identity。ForeignKey构造返回外键描述对象，ondelete默认None；执行建表操作时才落实数据库约束。

两列都设置primary_key=True会形成一个联合主键PRIMARY KEY (task_id, tag_id)，要求组合唯一，不要求每列各自唯一；不额外设置unique=True。主键列默认非空，因此本次实现省略nullable=False也符合要求。删除任务或标签会级联删除对应关联记录，不会借此删除另一侧的标签或任务；删除关联记录也不会反向删除父表记录。

2026-10-14静态检查：学习者已正确编写中间表，两列类型、外键目标、CASCADE、联合主键和建表顺序均符合要求。本轮没有新增运行测试或执行迁移。

下一步编写downgrade：它用于把结构退回前一迁移版本，本次对应移除三张基础表。Alembic的`op.drop_table(table_name, schema=None)`按表名删除表，schema默认None，返回None；在线执行会删除整张表及其数据，离线模式只输出SQL。表不存在、权限不足或被其他表外键引用时可能失败。本项目先移除task_tags，再移除tasks、tags；采用与创建相反的顺序容易维护。ON DELETE CASCADE针对行删除，不等于允许任意顺序DROP TABLE。downgrade不是Session.rollback：前者执行另一次结构变更，不能自动恢复已删除的数据。当前仅编写函数，不对学习数据库执行回退。

2026-10-14后续静态核对：downgrade已按task_tags、tasks、tags顺序编写完成，符合外键依赖。此处确认的是代码顺序正确，尚未实际运行完整升级/回退验证，不能据此认定迁移已经在数据库应用。

### 当前项目的初始迁移策略

2026-10-14完整离线预览：用户执行`alembic upgrade head --sql`生成三表及版本登记SQL；执行`alembic downgrade 042f491f9a4a:base --sql`生成按依赖顺序删表及清除版本记录的SQL。回退截图没有DROP TABLE alembic_version，清除记录后保留空版本表不影响base语义。`起点:终点`为离线回退明确指定范围；BEGIN、COMMIT、版本登记也只是文本，不能据此认定数据库已改变或连接密码正确。

当前`tasks`、`tags`和`task_tags`已手动创建并含有练习数据，尚未执行Alembic版本登记。首个迁移既要能够在全新数据库中创建三张基础表，又不能在现有数据库中重复建表。学习顺序是：初始化环境、连接`Base.metadata`、建立基础结构迁移、核对现有表与基线迁移确实一致后登记基础版本，再新增真实字段并生成第二个迁移。版本登记不会自动修复结构差异；登记前还需核对identity、数据库默认值等细节。现有数据库和数据不会为了练习而删除。

以上已有数据、未登记版本的描述针对原库task_manager_learning。2026-10-15测试库task_manager_migration_test已真实升级到042f491f9a4a，两个数据库的迁移状态必须分别记录。

核心关系是：ORM模型描述目标结构，迁移脚本描述从旧结构到新结构的步骤，`alembic_version`记录某个数据库已经执行到哪里。

### 未登记版本的原库：直接比较结构

原库已有手动创建的表但尚未登记版本，直接运行alembic check可能先报数据库未处于最新迁移版本；不能为了让check通过就先stamp。先使用`MigrationContext.configure(connection, opts={...})`建立比较上下文，再调用`compare_metadata(migration_context, Base.metadata)`比较结构。前者从alembic.migration导入，返回MigrationContext对象；后者从alembic.autogenerate导入，返回差异列表，空列表表示在当前检测范围内没有差异，不表示数据库没有表。

两个函数参数不一定是直接互相比较的对象。compare_metadata的第一个参数提供真实连接、数据库方言及比较规则，函数通过连接读取实际结构；第二个参数提供模型结构。真正比较的是“读取到的数据库结构”和“Base.metadata”，不是上下文对象本身与metadata。opts中compare_type=True启用类型比较，compare_server_default=True启用数据库默认值比较。比较不会执行生成的结构变更或登记迁移版本，但需要真实连接及读取权限，也可能因连接、反射或默认表达式比较而报错，仍受自动检测范围限制。

这里建议变量命名为migration_context。env.py的`from alembic import context`是代理模块，转交给EnvironmentContext；临时检查中的migration_context是MigrationContext.configure返回的实例，两者不是同一个对象。尤其注意：env.py的context.configure返回None，而直接调用MigrationContext.configure返回MigrationContext。

只读检查流程：终端指定原库→连接后开启事务→执行SET TRANSACTION READ ONLY→SELECT current_database()并断言目标是task_manager_learning→建立migration_context→compare_metadata→打印差异→退出事务和连接→finally中dispose。READ ONLY限制该事务普通写操作；assert用于防止对错误数据库的比较结果作出结论。此处只读比较不调用upgrade、downgrade或stamp。差异非空时先分析，不能直接登记版本假装结构一致。

2026-10-15原库接管结果：用户报告原库Database目标正确、Differences为[]，随后stamp 042f491f9a4a、current及check均符合预期。stamp创建或更新版本记录，不运行upgrade；原库无需重复建表。结果依据用户报告，助手未重跑。此后新增业务字段应创建后续迁移，不回写已应用的初始迁移。

### 第二个迁移：任务创建时间

需求是在已有tasks表增加created_at，保留任务记录。模型使用`created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))`。datetime从Python标准库datetime导入，表示Python时间值；DateTime从SQLAlchemy导入，构造返回数据库类型描述对象。timezone默认False，PostgreSQL下True对应带时区时间戳，保存时间点并按会话时区显示，不保留原始时区名称。本阶段无需调用这两个类型的其他方法。

CURRENT_TIMESTAMP由PostgreSQL在数据库侧求值，表示当前事务开始时间，同一事务中的多行可以相同。新任务插入省略该列时使用默认值；已有任务在新增列时获得迁移事务的时间补充值，不能声称这是真实历史创建时间。本次不额外声明Python侧default，不设置唯一约束。

流程是修改模型→revision --autogenerate→审查新文件→测试库升级和回退验证→原库升级。模型多出列而数据库未升级期间，不运行依赖新模型的ORM查询/API；create_all不会替已有表补列。`alembic revision --autogenerate -m "add task created_at"`连接目标库、比较真实结构与Base.metadata并生成文件，不执行新增列操作。自动生成内容必须审查，不直接认定正确。

本次生成f959d63045e7_add_task_created_at.py，revision为f959d63045e7，down_revision为042f491f9a4a，连接成迁移链。upgrade仅调用`op.add_column("tasks", sa.Column(...))`，downgrade仅调用`op.drop_column("tasks", "created_at")`。add_column的两个必需参数为表名和Column对象；drop_column为表名和列名；两者schema默认None，返回None。在线分别执行ALTER TABLE ADD COLUMN和DROP COLUMN，离线输出SQL。表或列不存在、重复新增、权限不足或约束冲突可能导致失败；DDL也可能等待数据库锁。删除列会丢失其中的时间值，但本迁移不删除任务记录或整张表。

测试先在测试库旧结构插入任务id=1（有用户截图），再upgrade head，验证旧任务原字段保留且created_at非空，以及INSERT只提供title时新任务自动得到时间。current应显示f959d63045e7 (head)，check应报告无新操作。只回退第二版用`downgrade 042f491f9a4a`，不用base；此时保留基础表和任务，只移除created_at，current不再标head，因为迁移文件的最新版本仍是第二版。此时模型仍有新列，暂不运行ORM查询或check。再次upgrade后列恢复，但时间是本次升级补充值，无法恢复回退前已删除的时间。

2026-10-15验收依据：迁移文件经助手静态审查；用户文字确认测试库旧数据/新数据时间验证、current/check、仅回退第二版后任务保留，以及再次升级/check和非空时间均符合预期。此为手动验证，不是新增自动化测试或完整pytest；原库第二版升级尚未完成。

### 选择测试数据库与首次在线迁移

2026-10-23补充：**HOST找服务器，NAME选数据库**。TASK_MANAGER_DB_HOST传给URL.create的host参数，TASK_MANAGER_DB_NAME传给database参数。可以把服务器比作一栋楼，HOST是楼的地址，NAME是房间名称；同一PostgreSQL服务可管理多个数据库，每个库有独立的tasks表、数据和迁移版本。

| 场景 | HOST | NAME |
| --- | --- | --- |
| Windows学习API | localhost | task_manager_learning |
| Windows数据库回归 | localhost | task_manager_migration_test |
| Compose内API连接数据库服务 | db | task_manager_container |

localhost相对于程序运行环境：Windows中的Python使用它指本机，API容器中使用它指该容器自身；db是Compose网络中可解析的服务名，不是数据库名。port=5432指定服务端口，username/password用于身份认证。学习库和测试库之间切换通常只改变NAME，HOST不变。

设置环境变量不会创建数据库、搬运数据或改变已运行服务的连接；后续新启动的Python继承并读取配置。恢复NAME为task_manager_learning只证明配置恢复，不能据此判断此前完整测试是否执行或通过。

测试目标是在独立空库验证“升级→回退→再次升级”，避免对原库已有表重复建表或删除练习数据。database.py使用`database=os.getenv("TASK_MANAGER_DB_NAME", "task_manager_learning")`选择目标。os.getenv(key, default=None)读取环境变量；存在时返回字符串，不存在时返回default，不创建数据库或连接。设置为空字符串也属于存在，不会使用默认值。密码使用os.environ[...]，缺失时抛KeyError，与数据库名允许默认值的策略不同。

在PowerShell设置`$env:TASK_MANAGER_DB_NAME = "task_manager_migration_test"`后，从该终端启动的新Python进程会继承此值，包括API和Alembic；已有进程不会自动切换。未配置的终端使用原库默认值。环境变量名是配置项，变量值才是目标数据库名。URL.create构造地址不创建目标数据库，数据库不存在时实际连接会失败。

调用链为：终端环境变量→database.py构造database_url→env.py导入并覆盖ini中的连接地址→在线连接目标数据库。因此仅修改alembic.ini不足以改变当前项目的连接目标。当前离线预览也会导入database.py，所以仍要求密码环境变量存在，但不验证密码正确性。

先在pgAdmin的“数据库→创建→数据库…”创建独立空库，不手动创建业务表。随后通过真实连接执行SELECT current_database()确认目标，而非仅打印配置。`connection.execute(text(...))`返回Result；`result.scalar_one()`无参数，要求恰好一行并取其第一列，本例返回数据库名字符串，零行抛NoResultFound、多行抛MultipleResultsFound。with退出归还连接后调用engine.dispose()清理池中空闲连接；它不删除数据库，也不会自动关闭仍被借出的连接。

PowerShell的`@'`与`'@`包围多行文本，管道把文本交给`python -`从标准输入执行，无需新建脚本。此次截图中文提示显示问号，但数据库名正常，查询成功；属于文本编码表现，不是数据库连接失败。

在线执行`alembic upgrade head`没有--sql，会真实运行upgrade并登记版本；head表示迁移链最新版本。随后`alembic current`读取数据库版本，显示042f491f9a4a (head)。版本记录不是完整结构验证，还应检查实际表及约束。pgAdmin在测试库下展开“架构→public→表”，必要时刷新，应看到三张业务表及alembic_version。

2026-10-15证据：用户截图确认真实连接目标为task_manager_migration_test、升级正常结束、current显示042f491f9a4a (head)；用户另行确认pgAdmin四张表、任务列及中间表约束符合预期，助手未收到该结构截图或执行独立结构查询。真实回退与再次升级尚未验证。在线回退可用`alembic downgrade base`，它读取实际当前版本，不必像离线回退那样指定起点；本次会删除测试库三张业务表及其中数据、清除版本记录，不删除数据库本身。回退后current不显示修订号，刷新表列表确认业务表已移除，再重新升级核对恢复。只在确认的专用测试库开展该实验。

参考：[Alembic官方教程](https://alembic.sqlalchemy.org/en/latest/tutorial.html)、[自动生成及限制](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)。

## 旧JSON导入：类型转换与严格校验

JSON导入与Alembic职责不同：前者搬业务数据，后者管理表结构。导入计划先读取并校验整批，再在同一事务创建任务和关联，全部成功才提交；任意一条失败则整批回滚。保留标题、完成状态、优先级和标签，由数据库生成新ID并记录旧新对应；原文件不修改。第一版拟拒绝向已有任务的目标库导入，标签可复用；重复执行和非空目标拒绝的实现、测试尚待完成。

校验不是必然转换。bool("false")为True（非空字符串），bool(0)为False，但严格布尔字段会拒绝字符串"false"和整数0。即使Python中bool是int的子类，严格布尔校验也只接受布尔值。JSON的false/true经json.load解析为Python的False/True，带引号的"false"仍是字符串。缺失done由导入校验模型补False，不要求等到数据库补值；显式null、数字、字符串则拒绝。缺失字段与显式错误值必须区别处理。旧Task.from_dict只是组装dataclass，类型注解本身不完整校验输入，因此不能直接认为读出的任务可信。

Pydantic普通bool字段可能转换输入；本次可声明`done: bool = Field(default=False, strict=True)`：Field返回字段配置对象，default指定缺失时的值，strict=True要求该字段严格类型，省略strict时遵循模型配置（默认通常允许转换）。校验成功后的done仍是普通bool，不是Field对象。通过BaseModel的model_validate(dict)执行校验并返回模型实例；类型错误抛ValidationError。该字段配置只作用于导入模型，不改变现有API的布尔查询参数行为。

title使用严格字符串及min_length=1、max_length=100，并通过模型ConfigDict(str_strip_whitespace=True)先清理首尾空白；空白标题清理后不满足长度要求。id使用`id: int = Field(strict=True, gt=0)`，无默认值表示必填；gt是greater than，限制数值大于边界。min_length检查字符串、列表等的长度，不适用于整数，不能把“正整数”写成min_length=1。严格整数校验拒绝字符串"3"、浮点数3.0和布尔值True，即使Python的bool是int子类。旧id仅供源记录识别和新旧映射，不直接写入数据库identity列。学习者已移除id误用的min_length；截至2026-10-17，模型正常输入、默认值及非法done/id测试通过，其他字段错误边界仍待补齐。

### 导入校验模型的职责与执行顺序

legacy_import.py当前只有LegacyTaskInput校验模型，不代表读取文件、整批导入和数据库事务已实现。database_api_demo.py校验HTTP客户端输入，导入程序处理旧JSON，两者数据入口不同。JSON读取成功只证明语法能解析，不保证字段类型或业务值合法。数据库的非空、唯一、外键约束也不能替代全部输入规则，例如普通TEXT优先级列不会自动限制low/normal/high。之后写入流程可复用Service/Repository，但校验模型本身不连接数据库。

LegacyTaskInput表示经过校验的旧记录，TaskRecord是数据库ORM模型；前者包含源ID，后者使用数据库生成的新ID。原始字典与校验返回对象的区别见下方model_validate章节。

priority使用严格str、default="normal"，after验证器将值转小写并校验low/normal/high；空白或非法文本抛ValueError，非字符串在进入after之前即被类型校验拒绝。`@field_validator("priority", mode="after")`注册规则，after为默认模式，函数接收已通过字段基础校验的值，必须返回最终值；遗漏return会隐式返回None。ValueError由Pydantic汇总为ValidationError。普通默认配置不会自动验证字段默认值，本次默认normal本身已合法。

tags使用`list[StrictStr] = Field(default_factory=list, strict=True)`：外层strict要求列表，内层StrictStr要求每个元素是字符串，外层严格模式不自动递归到元素。StrictStr是严格字符串类型标注，校验成功的元素仍是普通str。default_factory=list在字段缺失时创建独立空列表。模型配置先清理字符串元素首尾空白，after验证器再转小写、拒绝空字符串并保留首次出现的顺序去重。例如[" SQL ", "Python", "sql"]得到["sql", "python"]；不使用无序去重改变输出顺序。

### 模型测试：目前验证到了哪里

tests/test_legacy_import.py直接调用模型校验，不请求HTTP接口，也不需要数据库fixture。正常输入测试覆盖五个字段结果；只提供id/title的默认值测试断言done is False、priority为normal、tags为空列表。曾将done误断言为True导致失败，实际模型返回False符合需求：应修正测试预期，不能为了让测试通过而改变正确默认值。

非法值测试复用已有parametrize和pytest.raises知识：done参数为["false", 0, 1, None]，id参数为[0, -1, "3", 3.0, True, None]。每次只改变目标字段，其他必填值保持合法，避免无关字段错误让测试误通过；raises块只包model_validate调用。两项普通测试加4项done和6项id案例，共12项。异常测试预期不返回正常实例，因此无需接收返回值，也不必再写普通assert。

运行`python -m pytest --noconftest tests/test_legacy_import.py -q`只执行这个文件，--noconftest不加载conftest.py，-q精简输出。当前文件是纯模型测试，跳过conftest可避免数据库配置导入，因此无需密码或数据库连接；这不是完整套件的通用运行替代方案，依赖conftest夹具的测试不能这样运行。2026-10-17助手实际运行结果为12 passed；不等于已经测试JSON读取、数据库导入或完成当前版本全套回归。

### 导入结果的ID对照、集合及标签查询

id_mapping保存实际整数旧ID→数据库新ID，例如{3:101, 8:102}，不是字符串"old_task.id"。循环前创建{}，每创建一条任务记录`id_mapping[old_task.id] = new_task.id`，循环外flush并return；字典赋值只改内存映射，不修改数据库ID，return放循环内会提前结束导入。每条单独commit后，外层rollback不能撤销已提交行，所以导入函数只flush，由调用者统一管理事务。

set是Python内置集合类型，set(iterable)构造不含重复元素的集合，不修改原容器，不保证保留输入顺序，也不能按下标读取，元素须可哈希；set()创建空集合，{}是空字典。直接遍历字典默认得到键，因此set(mapping)相当于set(mapping.keys())，断言它等于{3,8}检查旧ID键没有缺漏或多余。mapping.values()返回字典值视图；set(mapping.values())对新ID去重，再len检查不同新ID数量。例如{3:101,8:101}的键断言通过，但不同值数量只有1，不能代表两条新任务。

成功导入测试的`session.scalars(select(TagRecord).where(TagRecord.name == "pytest-legacy-shared")).all()`先构造整模型查询和SQL筛选条件，由scalars执行并返回ScalarResult，再由all取出TagRecord实例列表，无匹配为[]。不是只取id：SELECT的结果项是整个模型。检查结果长度为1，再比较两条任务关联的标签ID，证明共享同一条标签记录，而不只名称相同。

enumerate(source_ids, start=0)是Python内置函数，返回迭代器，每次产生(位置编号, 元素值)，不修改原列表。测试中对[3,8,3]产生(0,3)、(1,8)、(2,3)，分别用值作旧ID、编号生成不同标题；相邻与非相邻重复ID测试据此只针对ID冲突。

### argparse命令行参数入口

2026-10-30增量：RAG入口使用add_argument("question", help="要查询的问题")登记一个必填位置参数，默认接收一个字符串；question是保存结果的名字，不是命令中需要输入的固定文字。ArgumentParser负责创建对象，description说明整个程序；add_argument登记规则，help说明单个参数，返回Action配置对象；parse_args才读取并检查实际输入。Namespace是属性容器，使用args.question而不是字典下标。Shell中的引号把含空格的问题保留为一个参数，外层引号通常不进入字符串。

具体流转：命令中的问题→sys.argv[1:]→Namespace(question=问题)→args.question→main(question)创建协程→asyncio.run执行协程→get_embedding(question)→generate_answer(question, context)。main内部不能保留固定question赋值，否则会覆盖输入。str类型注解本身不做转换或校验；仅有空格的参数仍能通过当前解析规则。asyncio.run等待协程完成并返回其return结果，当前main未显式return时为None；未处理的异常向外传播，不自动变成成功。

本次临时离线检查以runpy执行真实模块入口，模拟argv、笔记读取和有效缓存，并替换网络函数：--help退出0、缺参退出2且不调用Embedding；两个不同问题均原样传到Embedding和回答函数。未请求网络、未覆盖项目缓存，不等同于新增仓库测试套件或真实模型效果验收。

#### PowerShell启动Python工具：按执行层次读命令（2026-10-21）

终端是输入和显示文字的窗口，PowerShell是解析命令并启动程序的Shell。命令通常由程序与参数组成，参数的含义由接收它的程序决定。例如：

```powershell
& "D:\Python\Project\.venv\Scripts\python.exe" -m alembic revision --autogenerate -m "add task description"
```

PowerShell的`&`是调用运算符，将引号中的路径作为命令执行；引号保证含空格的路径或说明文字作为一个整体，不能把程序路径和所有参数包成一个字符串。完整路径明确选择项目虚拟环境的Python；仅写python时需要Shell查找命令。Python的第一个`-m`表示运行模块alembic，Alembic接收后面的revision、--autogenerate及第二个`-m`；后者是--message的简写，填写迁移说明。参数不能脱离所属程序解释。

完整Python路径不改变当前工作目录。`cd D:\Python\Project\Task_Managers_2`切换目录，使Alembic按默认方式找到项目alembic.ini。执行顺序为PowerShell启动Python→Python运行Alembic→读取项目配置和env.py→连接数据库并比较真实结构与Base.metadata→在versions目录生成候选脚本。revision --autogenerate会读数据库、写脚本，但不执行候选结构变更；upgrade head才执行迁移。

`PATH`帮助Shell查找python.exe、docker.exe等可执行程序；`sys.path`是Python查找模块或包的搜索位置列表。`python -m`方式下通常包含当前目录、标准库目录和当前虚拟环境的Lib/site-packages等。安装在本项目虚拟环境的Alembic通常位于`D:\Python\Project\.venv\Lib\site-packages\alembic`；Python找到包后运行其`__main__.py`，由该入口解析current或revision等参数。找不到时会报告No module named alembic；另一个Python安装过此包不代表当前环境可以使用。

项目自身的alembic目录保存env.py和versions迁移脚本，与site-packages中的工具包职责不同。当前项目目录无__init__.py，按通常的导入规则不会因此阻止后续找到已安装的普通包；在项目中创建同名alembic.py则可能遮蔽真正的工具包。上述是常见文件系统导入流程，Python还支持其他导入机制，当前阶段无需展开。

argparse是Python标准库，用于把启动命令中的参数解析成Python属性。流程为启动命令→ArgumentParser→add_argument登记规则→parse_args读取参数→args.file_path取得路径；本阶段main仅打印路径，不执行导入。ArgumentParser(description=...)创建解析器，description默认None，add_help默认True提供-h/--help。add_argument("file_path", type=Path, help=...)登记必填位置参数，返回参数配置对象，当前不接收；type未指定通常保留字符串。parse_args(args=None)默认读取sys.argv[1:]，返回Namespace；缺参数通常抛SystemExit(2)，--help输出帮助并SystemExit(0)。其余可选接口按需学习。

关键区别："file_path"是参数名称，不是待转换的路径文本。执行python legacy_import.py data/tasks.json时，type=Path将实际输入"data/tasks.json"转为Path对象，结果通过args.file_path取得，相当于args.file_path=Path("data/tasks.json")。改登记名为source后访问args.source，命令本身的位置输入仍可相同。路径构造不创建文件、不检查存在性；相对路径按运行时工作目录解释。if __name__ == "__main__"只在直接运行模块时调用main，测试导入模块不自动执行入口。

2026-10-18入口静态验收及三个测试通过：提供路径时打印正确且不创建文件；缺路径以2退出并报参数名；--help以0退出并显示帮助。monkeypatch临时替换sys.argv（列表首项为程序名，后续为用户输入）；capsys是pytest内置输出捕获fixture，readouterr()无参返回带out/err字符串的结果并清空本次捕获缓冲，分别检查标准输出和错误输出。pytest.raises(SystemExit) as error取得异常信息，error.value.code读取退出状态。当前仅跑无数据库测试文件52 passed，不能称为完整套件或最新全部导入测试结果。

#### 命令行测试中的路径传递与输出断言

测试中的tmp_path是目录fixture，file_path是测试局部Path变量；str(file_path)放到sys.argv第二项模拟用户输入。`monkeypatch.setattr(sys, "argv", [...])`虽未写字面量sys.argv，修改的就是sys模块argv属性。main里的parser.parse_args读取sys.argv[1:]，按type=Path转换后存入args.file_path，再作为实参传给导入函数；替代函数fake_import_file(path)的普通形参path此时才绑定到该值，不是fixture。路径链为file_path→命令行字符串→args.file_path→path→received_paths[0]。测试和main不共享局部变量，相同路径不要求对象身份相同。带空格路径置于argv一个元素中验证参数可包含空格，不覆盖Shell引号解析。

入口最初只打印路径，故捕获输出去换行后与str(file_path)比较；后续已改成调用导入函数并输出数量/映射，旧断言已更新。现在替代导入函数记录收到的Path并返回{3:101,8:102}，断言调用一次、类型为Path，输出splitlines后为["2", "{3: 101, 8: 102}"]；替代函数不读文件或连接数据库。不能把测试的模拟结果当作真实历史文件已导入。

main在parse_args之后捕获OSError、ValueError和SQLAlchemyError，再parser.exit(status=1, message=f"导入失败，{error}\\n")。exit默认status=0、message=None，有消息时写标准错误并抛SystemExit，不正常返回；实际使用换行字符，不是输出字面量反斜线n。原始异常先退出导入函数的事务块完成回滚，再由main转换为友好提示。密码环境变量缺失的KeyError不在当前友好捕获范围内。

`captured = capsys.readouterr()`一次取回out/err并清空本次捕获缓冲，返回对象仍可重复检查。captured.out==""确认失败没有打印成功结果；"导入失败" in captured.err确认失败说明位于标准错误；str(import_error) in captured.err确认提示保留实际异常原因。str(ValueError("原因"))得到"原因"，通常不含异常类名。缺参和--help的SystemExit由parse_args库内部产生，发生时args赋值和后续导入都不执行，测试在main调用外用raises接住，分别断言退出2和0。最终入口错误模拟覆盖文件、数据和SQLAlchemy异常，完整回归108 passed，真实JSON尚未导入。

### 文件导入事务与monkeypatch失败模拟

import_legacy_file先load_legacy_tasks校验完整文件，再在函数内导入SessionFactory，用`with SessionFactory.begin() as session`调用import_legacy_tasks，正常退出提交并关闭会话，异常退出回滚并关闭会话，退出成功后返回ID对照。函数内导入避免仅使用输入模型时就读取数据库密码配置。单纯with SessionFactory()只管理会话关闭，不自动提交；不在begin块内逐条commit或吞掉异常，确保整批事务边界有效。

test_import_file_rolls_back_partial_batch的目标不是再测非法源数据，而是模拟合法数据在写入中途发生运行错误。tmp_path准备两条合法JSON记录，import_file_session准备事务隔离和空任务目标；测试开始先查询专用标签，确认原本不存在，避免将已有标签误判为本轮残留。

`original_create = TaskService.create_task`没有括号，保存原方法引用，不立即执行。随后创建created_ids空列表，内部函数fail_on_second通过闭包读取并append这个外层列表。第一次调用列表为空，使用`original_create(service, title=..., priority=..., tags=...)`执行真实创建，记录返回任务ID并return任务。原方法是从类上取得的函数，所以显式传入service作为self。第二次调用列表非空，先get第一条任务，再raise指定RuntimeError，不执行第二条真实创建。标题写“触发模拟失败”只是便于阅读，失败由替代函数决定，并非标题非法。

pytest内置monkeypatch fixture提供`setattr(target, name, value, raising=True)`，当前用`monkeypatch.setattr(TaskService, "create_task", fail_on_second)`临时替换类属性，返回None；默认属性不存在时抛AttributeError。被替换的是类上的方法，既有和新建实例通过该类属性查找时均受影响，不限于某一实例或一次调用。已预先保存的original_create仍指向原方法；其他事先保存的方法引用也不自动改指向替代函数。

替换从setattr执行后开始生效，默认持续到当前函数级monkeypatch fixture清理时恢复；不是测试一开始就生效，也不随内部辅助函数或with块结束而撤销。测试正常完成或失败后，pytest正常清理都会恢复。替换可调用多次、可覆盖多个属性；无参数undo()返回None，提前撤销该monkeypatch对象记录的全部修改，不只最后一项。本测试同时替换Session工厂和create_task，不在中途随意undo。第一次成功、第二次失败是fail_on_second依据created_ids决定，不是monkeypatch自带计次或“一次性替换”功能。

`with pytest.raises(RuntimeError, match=...)`包住整个import_legacy_file调用，异常先传出函数内部的事务with，触发回滚，再由pytest接收。不能在事务块内部捕获后正常退出，否则可能提交前面已完成的操作。异常之后expire_all再查任务表与专用标签，应均为空；created_ids仍有一个元素，证明第一条执行过，普通Python列表不会随数据库回滚而清空。只靠Session.get断言非None不保证发出查询，因为可能命中身份映射；本例第一条已flush依据真实create_task内部的Repository.flush，再结合外部查询检查回滚结果。

测试工厂绑定已有测试Connection并使用create_savepoint，让入口函数的提交/回滚仅作用于保存点，最外层夹具最终回滚恢复测试前数据。事务内清空任务仅用于测试准备，业务导入函数仍必须拒绝非空目标，不能清库腾位置。2026-10-18导入专项53 passed覆盖成功路径、重复拒绝与中途失败回滚，不等于正式执行真实JSON导入或完成全套回归。

### 读取JSON与临时文件测试

load_legacy_tasks(file_path: Path)返回list[LegacyTaskInput]：UTF-8只读打开文件，json.load解析，检查顶层为list，逐项model_validate并收集返回实例。Path是路径表示，open返回文件对象，两者不同。json.load只负责语法解析，不保证列表结构或字段合法；[]应返回[]。当前文件不存在、JSON语法错误和模型验证错误原样传播，不将读取失败伪装成空数据。函数不写原文件或数据库。完整正常记录和错误文件测试仍待补齐。

tmp_path是pytest内置的函数级fixture，通过测试参数名请求，不需自行定义或导入，pytest为每个测试用例提供独立临时目录的pathlib.Path对象；参数化展开的每个用例也分别获得目录。`file_path = tmp_path / "tasks.json"`拼接出路径，不创建文件；随后用open(file_path, "w", encoding="utf-8")和json.dump准备测试文件，退出with关闭文件后，再调用读取函数。

必须区分fixture作用域、内存对象和磁盘目录：函数级表示每个用例独立准备和管理该fixture，不等于函数结束马上删除目录。局部变量名在函数外不可访问，Path对象无其他引用时可回收，但回收路径对象不删除磁盘目录；构造Path本身也不会创建目录。pytest默认保留最近3次运行的临时目录供排查，随后按保留配置清理。文件对象关闭仅释放打开资源，不删除文件，所以读取函数可以重新打开它。测试无需使用真实data/tasks.json，也无需手动删除临时目录。

本次空文件列表测试流程是：pytest准备临时目录→写入JSON []→关闭写文件→load_legacy_tasks重新打开解析→断言返回[]。2026-10-17实际独立测试文件37 passed，其中新增一项空JSON列表读取；此结果不代表正常多记录读取、错误文件或数据库导入已经验证。

参考：[pytest临时目录说明](https://docs.pytest.org/en/stable/how-to/tmp_path.html)。

## Docker导学：把可运行代码交付为可复现环境

Docker用于准备、隔离、分发和运行应用环境，属于运行交付层。前端负责展示交互，后端负责请求与业务，PostgreSQL负责数据，Docker可以承载这些服务但不替代业务代码。引入它是为了解决换机器后Python/依赖/数据库版本、启动方式和配置不一致的问题；本机程序能运行不等于别人已能按配置复现，也不等于生产部署已完成。

通俗类比：只交付代码像给别人菜谱，还得自行准备厨房设备；镜像像准备好的标准运行模板，Dockerfile是制作模板的步骤，容器是按模板启动的实际运行实例，Compose是安排多个运行单元协作的配置。类比不是打包整个Windows/PyCharm。容器技术上是隔离的进程及其文件、依赖和网络等环境，Linux容器共享所在Linux运行环境的内核，并非每个容器都有独立内核；Windows上通常借助Docker Desktop及WSL等提供Linux环境。

镜像Image是只读模板，容器Container是基于镜像创建的实例；Dockerfile描述构建Python环境、安装依赖、复制应用代码及启动方式。Docker Compose用配置文件组织API、PostgreSQL等多个服务，说明镜像、环境变量、网络、端口和存储关系。venv主要隔离Python包，不负责运行独立PostgreSQL或管理容器网络和卷；Docker与IDE/本地开发可以并存，并非必须把全部组件容器化。

目标链为浏览器HTTP→端口映射→API容器Uvicorn/FastAPI→Service/Repository→容器网络→PostgreSQL容器→持久卷。API与数据库各自管理，代码更新可替换API实例。容器内localhost指自身；同一Compose网络中host=db按服务名查找数据库服务，名字必须真实可解析，不是任意文本。host选择哪个PostgreSQL服务，database选择该服务内部哪个数据库。原先同一PostgreSQL内切换learning/test只改database，访问不同服务则要改host及对应凭据/端口。配置更改需要相应进程重新读取，已有连接不自动切换。

Volume保存容器生命周期之外的数据，替换容器不必丢失数据库文件；它不等于备份，不会自动带上本机数据库或JSON旧数据。Alembic仍负责表结构，Docker创建数据库服务不等于自动应用迁移；导入功能仍需另外明确运行。本节交付Dockerfile、Compose及运行说明，验证构建、迁移、API请求、容器重建和持久化；暂不扩展Kubernetes或云部署。导学完成不代表已安装或掌握。

### WSL软件版本、运行方式与Linux发行版

WSL全称Windows Subsystem for Linux（适用于Linux的Windows子系统），让Windows电脑可以运行Linux环境，无需将原有Windows替换掉；Windows应用与Linux程序可以同时使用。

“WSL 2.7.10”和“默认版本为2”描述不同维度：前者是WSL软件自身的版本号，原检查完整显示2.7.10.0；后者表示新安装的Linux发行版默认采用WSL 2运行方式，而不是旧的WSL 1。不能把2.7.10理解为WSL运行方式有一个叫“2.7”的代际，也不能仅凭默认版本设置认定Docker引擎已经可用。

项目准备运行Linux容器，需要Linux内核支持。使用WSL 2后端时，可理解为Windows提供宿主环境→WSL 2提供Linux运行基础→Docker Desktop利用该环境管理API和PostgreSQL等容器。这是便于理解的依赖关系，不表示每个容器各自运行一套完整操作系统。通俗比喻：Windows是原来的房子，WSL 2提供能运行Linux的一块空间，Docker管理其中的应用运行单元。

Linux发行版是Ubuntu等具体的Linux系统环境。WSL软件已安装，但没有用户自行安装的发行版，并不矛盾；Docker Desktop会管理其所需环境，当前不要求先额外安装Ubuntu。WSL、用户发行版和Docker是否安装/可用，应分别检查。

2026-10-18主对话只读检查记录：docker不在当时PATH，Docker Desktop全用户及常见用户安装路径未找到；WSL可执行文件存在，--version报告2.7.10.0，默认版本2，当时没有用户Linux发行版。该记录不代表之后安装状态，也不证明Docker引擎可用。侧边对话本次仅补充概念，没有重新检查环境、安装软件或启动容器。

### Windows安装、启动入口与排障边界

本机Docker Desktop安装程序位于`D:\Docker`。安装目录、用户配置目录、虚拟磁盘目录是不同概念，安装到D盘不自动代表所有数据都在D盘。当前采用独立目录绕过方案：配置在`D:\DockerData\config`，Docker进程使用的用户目录在`D:\DockerData\Profile`，WSL虚拟磁盘在`D:\DockerData\wsl`。桌面两个快捷方式均调用`D:\Docker\Start-Docker-DDrive.ps1`，按需请求管理员权限；这些环境设置只影响该次Docker及子进程，不修改Windows全局用户目录。直接运行原始exe不等同于经过该启动脚本。

排障应沿完整错误链寻找起点：最初C盘AppData中独立文件重命名也失败，目录带Encrypted属性，但没有查明底层系统原因，D盘方案属于绕过。后续WSL错误链为“挂载Docker数据VHDX被拒绝访问（E_ACCESSDENIED）→Linux中看不到对应磁盘→bootstrap报找不到wwid磁盘”。同屏出现的localhost代理警告不能直接当成根因。启动脚本的旧权限检测存在执行兼容问题，最终改用ASCII脚本、fltmc只读权限检查和快捷方式RunAs标志；失败则请求UAC提升。只通过脚本语法检查不足以证明实际启动具有管理员权限。

Docker Desktop左下角`Engine running`表示引擎在运行，`Containers`为空表示当前没有显示的容器，不是故障。`Images`查看镜像，`Containers`查看容器及状态，`Logs`查看输出，`Volumes`管理持久存储。当前学习使用英文原版界面；官方中文界面需求仍未完成，不为学习依赖第三方汉化替换程序文件。许可协议需要使用者阅读并自行决定是否接受；协议窗口与启动错误是不同事情。

验证应分层：引擎一次启动成功、正常退出后重复启动成功、Windows重启后成功、实际拉取并运行容器成功，分别需要证据。此前两个桌面入口重复启动已验证；用户后来再次进入Engine running界面，不据此自动记录为Windows重启已验收。

### PowerShell如何找到Docker：PATH与完整路径

`PATH`是操作系统查找可执行程序时使用的目录清单。旧的PyCharm终端可能没有加载安装后的路径；Python虚拟环境激活与Docker是否能被找到是两回事。`docker`命令无法识别意味着客户端尚未执行，不是Docker引擎报错。

```powershell
& "D:\Docker\resources\bin\docker.exe" run hello-world
```

`&`是PowerShell调用运算符，用于执行引号内路径指向的程序。完整路径可以找到主程序，但Docker还可能调用`docker-credential-desktop.exe`等辅助程序；辅助程序仍需通过PATH查找。因此“主程序可以执行，但凭据助手不在PATH”不代表密码错误。

```powershell
$env:Path = "D:\Docker\resources\bin;" + $env:Path
docker run hello-world
```

第一行在原目录清单前增加Docker程序目录；分号分隔Windows PATH中的目录。只影响当前终端及后续子进程，关闭后不永久保留，不是修改项目文件或Python依赖。启动脚本中设置Docker后台的运行目录，与另一个PyCharm终端的PATH是两项独立配置。

`docker run hello-world`使用镜像名称，不读取当前目录里的项目代码，因此可以在任意工作目录执行，也不会将镜像下载到当前文件夹。后续`docker build .`中的`.`表示当前构建上下文目录，工作目录会影响行为；构建时再展开。

### hello-world：从命令到容器退出的完整流程

`docker`是客户端；`run`请求根据镜像创建并启动一个新容器；`hello-world`是镜像名称，省略标签时默认为`latest`。标签是可更新的名称引用，`latest`不是保证发布时间最新的特殊比较规则。默认本地缺镜像时尝试拉取，已有时使用本地镜像。

```text
PowerShell命令 → docker.exe客户端 → Docker后台服务（daemon）
    → 检查本地镜像 → 缺少则从Docker Hub下载
    → 根据镜像创建新容器 → 启动容器内程序
    → 后台服务转发程序输出 → 客户端 → 终端
    → 程序执行结束 → 容器停止，命令返回提示符
```

| 输出 | 含义与判断 |
| --- | --- |
| `Unable to find image 'hello-world:latest' locally` | 本地没有镜像，接下来会尝试下载；单独这一行不是最终失败 |
| `latest: Pulling from library/hello-world` | 从Docker Hub的官方仓库拉取latest标签 |
| 短标识加`Download complete`或`Pull complete` | 对应下载对象或镜像层处理进度；多行不表示创建了多个容器 |
| `Digest: sha256:…` | 精确标识镜像内容的摘要；与可重新指向其他内容的标签不同 |
| `Status: Downloaded newer image ...` | 本次镜像拉取成功；不证明本地先前一定有旧版 |
| `Hello from Docker!` | 容器中的程序实际输出欢迎信息，证明本轮下载、创建、执行及输出链成功 |
| `(amd64)` | 使用x86-64架构镜像，不要求CPU必须为AMD品牌 |

下载进度由Docker工具输出，欢迎文字由容器中的程序输出，两者都显示在同一个终端。欢迎信息中四个步骤对应客户端联系后台、后台下载镜像、创建容器执行程序、转发输出；其中推荐的`docker run -it ubuntu bash`只是文字示例，没有自动执行或额外安装Ubuntu。

hello-world打印完成就退出，不像API服务持续等待请求。未使用自动清理选项时，镜像和停止的容器记录仍保留；容器停止不等于镜像被删，也不等于引擎关闭。再次执行`docker run hello-world`会创建另一个新容器，不是自动复用上次实例。当前实验没有端口映射、数据库服务或项目代码容器化，也不能替代项目交付验收。

截至2026-10-19，用户提供完整终端截图，包含拉取完成、摘要、`Hello from Docker!`以及返回PowerShell提示符，证明该次最小容器实验成功。后续学习镜像列表与运行中/全部容器列表，先通过观察验证三者的生命周期区别。

### 查看、创建与重新启动容器

`docker image ls`列出本地镜像；新版输出可能将名称和标签合并为IMAGE列。U（In Use）表示镜像被容器引用，不保证有容器正在运行。`docker container ls`默认只列运行中容器，`docker container ls -a`包含停止的容器，-a为--all。CONTAINER ID是实例标识，IMAGE是来源模板，COMMAND是启动程序，STATUS中的Exited (0)表示正常退出，PORTS显示端口映射，NAMES是实例名称。未指定名称时Docker自动分配，例如cool_mendeleev。

`docker container start -a cool_mendeleev`重新启动原容器，ID不变；这里-a为--attach，把运行输出连接到终端，与ls -a含义不同。不带-a的start启动后返回终端。`docker run --name hello-second hello-world`根据已有镜像创建第二个容器；实例共用镜像层，不重复保存完整相同镜像。--name指定容器名称，不是镜像名称；名称须唯一，停止的容器也占用名称。重复同名run会冲突，需要区分创建新实例与启动已有实例。

### 持续运行的Nginx与端口映射

Nginx是服务端Web服务器软件；本轮使用其默认静态首页，不是Task Manager API。实验命令：

```powershell
docker run -d --name web-demo -p 127.0.0.1:8080:80 nginx:alpine
```

-d是--detach，启动后终端与容器分离，通常输出容器ID；不是把短命程序变成常驻服务。Nginx持续等待请求，因此保持Up；hello-world即使用-d也在程序结束后退出。nginx:alpine是镜像名及基于Alpine Linux的标签。-p为--publish，格式为宿主地址:宿主端口:容器端口，此例提供本机127.0.0.1:8080入口，转发至容器内80；默认使用TCP。不把Nginx自身监听端口改为8080。

```text
Windows浏览器请求http://127.0.0.1:8080/
 → Docker端口转发 → 容器内80端口的Nginx
 → 读取默认HTML → 经连接返回浏览器 → 浏览器解析并绘制页面
```

8080和80不是前后端两个服务的端口，而是同一服务在宿主机和容器网络中的访问位置。这里转发的仍是HTTP请求，不转换成其他业务请求；Python客户端访问同一地址也可以使用入口。

### Nginx、前端页面和业务后端的职责

前端资源是浏览器使用的HTML/CSS/JavaScript等；Nginx提供资源，不等于它是前端框架。镜像自带HTML，Nginx读取并发送，浏览器渲染。服务器能够返回页面，不代表它是一套完整全栈体系。

按浏览器端/服务端划分，Nginx属于服务端；按业务职责划分，它通常提供静态资源、作为流量入口，而标题校验、任务创建和事务等由FastAPI/Service负责，PostgreSQL负责存储。反向代理是接收请求后按规则转交其他服务，再将响应返回客户端。后续可以为浏览器→Nginx，静态文件直接返回，API请求转给FastAPI→PostgreSQL；当前没有配置反向代理或运行Task Manager容器。

HTTPS通过TLS加密传输HTTP，处理HTTPS的能力不决定软件属于前端还是业务后端。当前地址是HTTP，没有配置HTTPS或证书。本节只理解角色，不要求每个项目先引入Nginx。

### 绑定挂载：让Nginx读取Windows上的页面

绑定挂载（Bind Mount）把指定宿主文件或目录映射到容器内路径，不是复制，也不修改镜像。本次源目录为D:\Python\Project\Task_Managers_2\examples\docker\site，目标为/usr/share/nginx/html。Linux容器路径与Windows来源路径可以完全不同；Docker Desktop负责让Linux容器访问所指定的本机文件。

```powershell
docker run -d --name web-files -p 127.0.0.1:8081:80 --mount "type=bind,source=D:\Python\Project\Task_Managers_2\examples\docker\site,target=/usr/share/nginx/html,readonly" nginx:alpine
```

--mount登记挂载关系，双引号将逗号分隔的配置作为一个完整参数传入。type=bind指定绑定挂载，source为本机来源，target为容器内目标，readonly禁止容器通过挂载路径写入本机文件；默认未指定只读则允许写入。readonly不限制用户在Windows上编辑源文件。此处--mount默认要求源路径已存在，否则报错，不会自动准备HTML文件。使用绝对来源路径时命令不依赖当前工作目录。新容器使用8081，与原web-demo的8080分开。

浏览器请求8081→转发至web-files的80→Nginx读取/usr/share/nginx/html/index.html→通过挂载读取Windows中的site/index.html→返回页面。挂载到已有内容的目录会遮住容器原有文件，并非删除镜像中的默认首页。未写挂载时原始镜像仍提供自带页面。

用户创建的HTML包含doctype、lang、UTF-8字符编码、title、body、h1和p；title是标签页标题，body中的h1/p是页面标题及段落。index.html保存后，用户反馈网页显示自定义内容，修改h1为“修改后立即生效”并强制刷新即可看到变化，无需重启Nginx或重建镜像。这里是每次请求读取文件，不等同于所有框架都自动热更新。Bind Mount依赖宿主路径，不能仅交付镜像就假定别的机器已有同一路径；Docker管理的命名卷与其不同，后续结合数据库持久化再展开。

### Dockerfile、FROM/COPY与构建上下文

Dockerfile是制作镜像的文本步骤文件，不是Python模块或容器。保存文件只是写下步骤，不自动执行构建，也不启动服务。当前教学文件为examples/docker/Dockerfile，与site目录同级，无.txt后缀：

```dockerfile
FROM nginx:alpine
COPY site/index.html /usr/share/nginx/html/index.html
```

FROM指定基础镜像，本例保留Nginx程序、默认配置及启动方式。COPY的源site/index.html相对于构建上下文，目标是新镜像内的绝对路径。构建上下文是本次提供给构建器的材料目录；后续指定examples/docker为上下文才能直接找到site/index.html。源不是按终端任意目录解析，也不能仅因Dockerfile放在某处就默认所有构建都以该处为上下文。

构建时COPY读取页面内容并保存到新镜像，源文件不被删除或修改，基础nginx:alpine镜像也不变。运行新镜像时无需依赖原Windows目录；之后修改本机HTML不会自动更新已有镜像或容器，需要重新构建并使用新镜像创建实例。仅start旧容器不采用新构建的文件。相对地，绑定挂载是在运行时读取本机文件，不更新镜像。两种方式分别适合开发中的文件共享和把构建时内容交付为镜像。

### 执行构建：build、镜像标签与点号

```powershell
cd D:\Python\Project\Task_Managers_2\examples\docker
docker build -t task-web:v1 .
docker image ls
```

cd切换工作目录；build根据Dockerfile构建镜像，-t（--tag）给结果指定名称task-web和标签v1，点号指定当前目录为构建上下文。未用-f指定文件时，默认从上下文根目录查找Dockerfile。本例上下文为examples/docker，因此COPY能找到site/index.html。点号不是镜像名称或输出位置；镜像由Docker存储，不会在当前目录生成一个名为task-web的文件。

以第二次构建为具体例子：

```powershell
docker build -t task-web:v2 .
```

| 命令部分 | 输入含义与执行作用 |
| --- | --- |
| docker | 调用命令行客户端，将构建请求交给构建器 |
| build | 制作镜像；与run创建并启动容器不同 |
| -t task-web:v2 | --tag的简写，为构建结果登记名称task-web、标签v2 |
| . | 当前工作目录，指定本次构建上下文，不是结尾标点 |

task-web与v2均由使用者命名，不要求镜像名等于项目目录名。冒号分隔名称与标签，改成task-web:practice同样合法；v2不会让Docker自动寻找v1、检查业务版本或执行升级。同一份构建内容可以有不同标签，标签本身不是内容发生变化的证据。

点号与COPY的关联可代入实际路径理解：

```text
先cd到 D:\Python\Project\Task_Managers_2\examples\docker
    ↓
build最后的 . 指定这个目录为材料目录
    ├─ Dockerfile：默认在材料目录根部查找的制作步骤
    └─ site/index.html：COPY指令声明的材料相对路径
            ↓
实际源文件为
D:\Python\Project\Task_Managers_2\examples\docker\site\index.html
            ↓
复制构建时的文件内容到新镜像的
/usr/share/nginx/html/index.html
            ↓
保存结果，登记名称标签 task-web:v2
```

因此切换到别的工作目录仍执行同样命令，会改变点号代表的位置，可能找不到Dockerfile或COPY来源文件。Dockerfile是步骤，构建上下文是材料范围，task-web:v2是结果名称，三者不是同一个对象。构建v2后，本机HTML仅被读取、基础nginx:alpine与原task-web:v1保留、旧web-built仍使用原镜像内容；不会凭这条build命令创建或启动新容器。上述为命令讲解，不代表本轮已实际执行v2构建。

实际流程为读取Dockerfile→取得基础镜像nginx:alpine→将构建时HTML复制进新镜像→为结果登记task-web:v1名称引用。构建可能复用缓存，也可能请求仓库元数据，并非只要本地有基础镜像就保证完全不联网。构建成功不自动启动容器、不改变原nginx:alpine，也不改变已运行的web-files。重新使用同一标签构建会更新标签指向，不自动更新已有容器。

2026-10-20用户反馈构建完成，导师实际查询本地镜像列表确认task-web:v1存在，短ID为b2de1af8049d。随后用户运行以下命令并反馈网页及对比结果符合预期：

```powershell
docker run -d --name web-built -p 127.0.0.1:8082:80 task-web:v1
```

此命令没有--mount，因此web-built读取镜像里的页面副本。用户将本机h1从“修改后立即生效”改成“本机文件再次修改”，保存并强制刷新后，8081的web-files显示新文字，8082的web-built仍显示构建时旧文字。导师核对源文件确已修改，HTTP现象依据用户反馈，未自行重跑或访问网页。

页面是否更新取决于读取来源，不单取决于是否重启：绑定挂载容器读取本机当前内容，无挂载容器读取镜像提供给实例的内容；重启web-built仍使用原实例，不会重新COPY本机文件。交付新内容应重新构建并用新镜像创建容器。给镜像命名v1/v2只是人为版本标签，不会自动构建、监控文件变化或迁移旧容器；已有容器不会因新版本镜像出现而自动升级。

Nginx教学入口为8080默认首页、8081本机只读挂载、8082自定义v1镜像副本、8083自定义v2镜像副本。用户已反馈v2构建和新容器对比符合预期：8082仍是旧标题，8083显示修改后的标题；依据用户反馈记录实验完成，不将端口或网页文字当成镜像身份标识。构建新版本与运行新实例是两个明确动作，旧实例保留原内容。未执行远程推送或实际生产发布；这个最小静态网页流程通过，不等于正式Task Manager容器化已完成。

### 从Nginx练习迁移到Task Manager：数据库地址可配置

正式请求链准备为浏览器→API容器中的Uvicorn/FastAPI→PostgreSQL容器。Nginx作为基础教学工具，不是本阶段必须再添加的业务层。当前项目入口为api:app；数据库密码与库名已有环境变量配置，但原host硬编码localhost。API进入容器后，localhost指API容器自己，不是Windows，也不是另一数据库容器。

```python
host=os.getenv("TASK_MANAGER_DB_HOST", "localhost"),
```

os.getenv的第一个参数是变量名，第二个是变量不存在时的默认值。未提供时保持本地开发兼容；后续Compose若将数据库服务命名为db，则在API运行环境提供TASK_MANAGER_DB_HOST=db。db不是固定魔法名称，只有实际服务与网络支持解析时才可用。读取变量并创建URL本身不连接数据库；变量由启动进程的运行环境提供，不写入镜像中的密码。这里只将host改为可配置，未同时实现全部数据库参数配置，也未验证容器间连通性。

相关参考：[绑定挂载](https://docs.docker.com/engine/storage/bind-mounts/)、[Dockerfile](https://docs.docker.com/reference/dockerfile/)。

### 正式项目的构建排除规则与Python依赖安装

根目录.dockerignore排除构建上下文中的文件，与.gitignore控制Git跟踪的职责不同；被Git忽略不保证被Docker忽略，也不会因写排除规则而删除本机文件。当前排除.git、Windows虚拟环境、IDE配置、Python/pytest缓存、.env与.env.*、data及日志。.env.*也匹配.env.example，后续如需将示例加入构建材料再明确调整。这里只是按名称排除，不代表所有可能的秘密文件都已自动识别。尚未实际构建验证规则效果。

正式根目录Dockerfile的环境准备部分：

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
```

FROM提供Linux中的Python 3.14精简环境，不使用本机.venv。WORKDIR将后续工作目录设为/app，不存在时创建；这是镜像/容器路径，不切换Windows终端目录，也不自动复制文件。COPY的来源requirements.txt相对于构建上下文，目标点号指当前镜像工作目录，所以结果是/app/requirements.txt。这与build命令末尾点号指定宿主构建上下文的含义应按位置区分。

RUN是Dockerfile指令，要求构建器在构建环境执行后面的命令；python调用镜像中的解释器，-m pip运行该解释器对应的pip模块，install请求安装，-r（--requirement）按文件读取安装要求。清单中的==固定对应包版本，pip还会处理其依赖。安装发生在镜像的Python环境，不改变Windows虚拟环境；缺包、版本冲突或网络故障可能使构建失败。保存Dockerfile本身不会执行RUN。

--no-cache-dir不使用或保存pip下载/构建缓存，但安装好的软件包仍保留；它不关闭Docker层缓存。先COPY清单再安装、后复制业务代码，可让仅改业务代码时有机会复用依赖安装层，是否复用仍取决于输入和缓存状态。整个顺序为准备Python→设置/app→复制清单→在/app按清单安装依赖。2026-10-20已核对上述四条指令正确，尚未实际构建或安装容器内依赖。

### 复制正式源码与登记API启动命令

依赖安装之后追加COPY . .：第一个点号为构建上下文中的内容（受.dockerignore影响），第二个点号为当前镜像工作目录/app。构建后得到/app/api.py等源码；先安装依赖再复制源码，避免只修改源码时不必要地使依赖层缓存失效。

```dockerfile
COPY . .
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

RUN在构建时执行安装等命令；CMD将默认运行命令保存在镜像配置中，启动容器时才执行，可被运行参数覆盖。exec形式使用JSON数组和双引号，每个元素是一项程序或参数，不是Python列表求值；不默认经Shell处理管道或变量展开。此例实际运行python -m uvicorn api:app --host 0.0.0.0 --port 8000。构建不因CMD而导入api或启动服务器；运行时导入api会读取数据库配置，届时仍需提供密码等变量。

api:app遵循模块名:对象名，可近似理解为from api import app。api对应api.py，但模块导入名不带.py；冒号后app为文件中的FastAPI实例，不是文件名的重复。包结构可写backend.api:app，但必须能导入对应包。WORKDIR /app与复制的/app/api.py使当前入口可被找到。

Uvicorn的--host是API接收请求的监听地址，不是database.py中连接PostgreSQL的host。127.0.0.1只监听容器内部回环接口；Docker通常将发布端口流量转发到容器网络接口，因此API监听0.0.0.0以接收容器各IPv4接口上的请求。0.0.0.0不是整个互联网，不会自动发布端口，也不是浏览器应输入的地址；本机入口仍由运行时-p等映射决定。--port 8000指定容器内监听端口，不自动创建Windows端口映射。当前不使用开发用--reload。

截至2026-10-20正式根目录Dockerfile六条指令文本核对通过；尚未实际构建、验证Linux依赖安装或运行正式容器。下一步在项目根目录构建task-manager-api:v1；镜像构建无需提供数据库密码，API运行及数据库连通仍需后续独立验证。

### 正式镜像构建中的网络错误与验证边界

首次构建在FROM阶段获取Docker Hub匿名token时超时，尚未安装Python依赖；单独docker pull python:3.14-slim成功后继续构建。anonymous token是拉取公开镜像时工具自动获取的访问凭证，不是数据库密码，也不直接说明必须登录。读取本地基础镜像不保证构建绝不联网查询元数据。

随后pip访问https://pypi.org/simple/fastapi/时出现TLS UNEXPECTED_EOF_WHILE_READING：加密连接尚未读完便意外结束。索引读取失败后显示versions:none和No matching distribution，不足以证明版本不存在，也不足以证明一定是证书不受信任。先区分下载连接、包是否存在、版本兼容与实际安装，不仅凭最后一行改版本或关闭证书校验。

导师实际复现过失败，同时在普通基础容器及最小构建环境用urllib/pip查询成功并查到0.142.2；再次原样构建成功，生成task-manager-api:v1，ID e1f25dc2ed2c。没有修改源码、Dockerfile、下载源或依赖版本，现象符合间歇性网络中断，具体网络根因未确定。独立容器运行python -m pip check返回No broken requirements found，只验证已安装包的声明依赖一致性，不等于API已能启动、数据库可连接或完整测试已通过。诊断容器已停止，未删除。

### Compose与YAML：用数据描述多个服务

Dockerfile负责单个镜像如何制作，Docker Compose负责按配置组织构建、服务、网络、端口及存储。Compose是工具，compose.yaml是它读取的配置文件。YAML是记录结构化数据的文本格式，不是Python代码，也不是容器；.yaml与.yml都是常见扩展名。保存配置不自动运行服务，需要之后调用Compose命令。

```yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
```

等价的数据层级可用Python字典理解为services包含api，api包含build字符串和ports列表。冒号后空格分隔键和值，空值位置的下一层缩进描述所属内容；统一每层两空格，不使用Tab。短横线表示列表元素，不是命令行选项。端口映射加双引号，作为完整字符串。YAML规定数据如何书写，Compose规定services/build/ports等键的用途。

services登记服务集合，api是使用者选择的服务名，不自动对应api.py；Python入口由Dockerfile的CMD中api:app决定。build: .以Compose文件所在目录为构建上下文，默认读取其中Dockerfile；ports配置宿主与容器端口。不写image时，Compose构建使用默认项目名/服务名生成镜像名称，不能认为一定自动复用手工命名的task-manager-api:v1。共享默认网络后可以按真实服务名查找其他服务，数据库服务将在后续添加为db。

2026-10-20当时只有api配置，导师执行docker compose config --quiet退出0。config读取Compose文件，合并配置、解析YAML结构并替换变量占位符，检查最终数据模型；--quiet只校验而不打印展开后的完整配置，成功时通常无输出并退出0。若必填TASK_MANAGER_CONTAINER_DB_PASSWORD未设置或为空，插值规则会导致校验失败。此命令不会启动容器、创建表或连接数据库，不能证明密码与库内密码一致、数据库就绪、8000端口可用或API业务正常；服务运行后仍需实际HTTP/SQL验证。可以类比为检查方案写法而非执行方案。普通config可能展开密码，涉及凭据时不随意打印完整配置。

### API自制镜像与数据库官方镜像

一个Compose应用可以由多个不同镜像的容器协作，不要求全部软件装进一个镜像。根目录Dockerfile以python:3.14-slim为基础安装Python依赖并复制Task Manager源码，制作的是API镜像，没有安装PostgreSQL服务器。api的build: .使用这份Dockerfile；db的image: postgres:18直接使用官方已制作发布的数据库镜像，当前不需要再写数据库Dockerfile。官方镜像也有其构建过程，只是不由本项目重复实现。API容器通过网络连接数据库容器，而不是把Python安装与数据库安装看成同一个过程。

db的environment将变量传给数据库容器。POSTGRES_USER指定初始化用户名，POSTGRES_DB指定初始化数据库名，POSTGRES_PASSWORD指定初始化密码；这些是官方镜像识别的名称，与API自己读取的TASK_MANAGER_*不同，不自动传给其他服务。首次空数据目录初始化会创建用户/数据库，但不会创建Task Manager业务表，表结构仍由Alembic迁移。已有数据目录初始化完成后，修改这些变量不自动重命名库或修改用户密码。

`${TASK_MANAGER_CONTAINER_DB_PASSWORD:?请先设置容器数据库密码}`是Compose变量插值：从外部获取变量，缺失或为空则报指定错误；不生成密码，也不把变量名当密码。当前使用独立名称区分容器数据库与本机原库。写变量引用不需要把实际密码保存进Compose文件或镜像；API后续还需显式传入对应连接配置。

2026-10-20核对compose.yaml已包含平级db/api，db使用postgres:18和上述三项环境配置，API已有build及ports。服务在YAML中的书写顺序不等于数据库实际就绪顺序。尚未启动、创建数据库、配置数据卷或连接原库。

### 两处environment与启动到查询的执行链

environment语法相同，但按所在服务分别传递：db.environment只进入数据库容器，api.environment只进入API容器，彼此不自动共享。前者告诉官方初始化程序“数据库首次建成什么样”，后者告诉我们的Python代码“去连接哪个已有数据库”。同一个外部TASK_MANAGER_CONTAINER_DB_PASSWORD通过Compose插值，分别变成db内POSTGRES_PASSWORD与api内TASK_MANAGER_DB_PASSWORD，值一致但名称、读取程序和用途不同。

本轮添加api.environment与Python代码的直接关系（2026-10-21补充）：配置不是写给URL.create自动识别的，而是先由Compose传入API进程环境，再由已有Python语句读取。对应如下：

| api.environment中的配置 | database.py中的读取语句 | 本轮改变的实际值 |
| --- | --- | --- |
| TASK_MANAGER_DB_HOST: db | os.getenv("TASK_MANAGER_DB_HOST", "localhost") | 从默认localhost变为db服务地址 |
| TASK_MANAGER_DB_NAME: task_manager_container | os.getenv("TASK_MANAGER_DB_NAME", "task_manager_learning") | 从默认本机练习库名变为容器库名 |
| TASK_MANAGER_DB_PASSWORD: ${TASK_MANAGER_CONTAINER_DB_PASSWORD:?...} | os.environ["TASK_MANAGER_DB_PASSWORD"] | 从外部取得与数据库初始化一致的密码 |

修改前后可以这样比较：仅配置db.environment时，数据库知道如何初始化，但API不会自动继承它的变量；若API环境未另行提供变量，host仍默认localhost（指API容器自身），库名仍默认task_manager_learning，密码缺失则在读取时抛KeyError。加入api.environment后，读取结果改为db、task_manager_container及外部密码，才能与数据库一侧约定的连接条件对应。实际能否连接仍需网络、数据库就绪及认证等后续验证。

URL.create本轮无需改写；改变的是传入它的实际配置值。username="postgres"和port=5432本轮没有修改，分别与数据库用户和容器内端口保持一致，不能将背景参数解释成新增配置。关键链条为“新增Compose配置→容器进程环境变量→Python读取→构造连接目标”，不是直接从一个容器读取另一个容器的environment。

构建与启动要分开理解：compose.yaml的build: .只描述需要构建时的材料位置；构建器读取Dockerfile，执行RUN等构建步骤，把CMD保存进镜像。Compose根据镜像启动容器时，才执行保存的默认CMD；不会每次启动都重跑整个Dockerfile，也不是build配置项直接执行Uvicorn。

“沿导入链加载database.py”在当前源码中有明确对应：api.py的from task_routes import task_router使Python加载task_routes.py，后者的from database import get_session使Python加载database.py。首次导入会执行模块最外层语句，因此先读取密码、创建URL/Engine/Session工厂；执行到def get_session只是定义函数，不调用其函数体。依赖被请求时才进入函数体，真实SQL需要连接时才访问数据库。模块通常在同一进程首次导入后缓存，不是每个HTTP请求重新执行整个database.py。

完整执行顺序按职责理解如下（尚未配置就绪依赖时，并不保证两服务按此顺序完成启动）：

1. Compose解析`${TASK_MANAGER_CONTAINER_DB_PASSWORD:?...}`；缺值报错，存在则填入两服务配置，不创建用户或建立数据库连接。
2. db使用image: postgres:18创建容器，官方启动程序读取POSTGRES_USER、POSTGRES_DB、POSTGRES_PASSWORD，在空数据目录首次初始化用户名postgres、库task_manager_container及密码。volumes挂载将数据保存进命名卷；已有初始化数据时不按环境变量重复建库或改密码。业务表仍待Alembic迁移。
3. api根据build描述取得应用镜像，创建容器时注入api.environment；Dockerfile CMD启动python -m uvicorn api:app，Uvicorn导入api.py。api.py中from task_routes import task_router沿依赖链加载database.py。
4. database_password = os.environ['TASK_MANAGER_DB_PASSWORD']读取API自己的变量；URL.create中host的os.getenv得到db，database的os.getenv得到task_manager_container，username固定postgres、port固定5432，密码取前述变量。API不会主动读取另一个容器的POSTGRES_PASSWORD。
5. URL.create整理连接参数，create_engine创建Engine，sessionmaker(bind=engine)创建Session工厂；这些步骤当前不直接发起数据库连接。db由同一Compose网络的服务名解析提供，不是Python特殊关键字。
6. 需要数据库的HTTP请求到达FastAPI，Depends调用get_session，with SessionFactory() as session创建会话，yield提供给接口/Service/Repository。session.get、execute或flush等实际需要SQL的操作再取得连接；如果已有合适连接则可复用，不表示每次查询都新建物理连接。
7. 数据库接收API提供的用户名/密码与目标库，执行SQL并返回结果。成功还要求数据库已就绪、认证配置一致、业务表迁移完成；API进程能启动不等于数据库请求一定成功。

### 命名卷：容器内路径与实际数据存储

命名卷由Docker管理具体存储位置，区别于用户指定Windows来源目录的绑定挂载。数据库服务中写volumes列表，并在Compose最外层登记卷，两处用途不同：顶层声明应用使用的卷，服务内指定哪个容器在什么路径访问它。

```yaml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql

volumes:
  postgres_data:
```

以上仅示意卷相关配置，省略了真实文件中的镜像等其他项。左侧postgres_data是逻辑卷名，右侧/var/lib/postgresql是数据库容器内Linux目录，不是Windows文件路径。PostgreSQL 18官方镜像默认数据目录为/var/lib/postgresql/18/docker，位于挂载目录下，因此读写数据进入同一卷。旧版教程中的/var/lib/postgresql/data不能不分版本直接套用。Docker Desktop实际存储由其管理，用户不需要手动去容器路径对应的Windows目录编辑数据库文件。

容器是使用存储的运行实例，挂载路径是访问入口，卷是持久存储。替换容器时关键是复用原来的同一实际卷并挂到正确位置，仅写相同容器路径不够；挂新空卷会得到新数据环境。Compose实际卷名默认带项目名前缀，所以换项目名或目录导致使用不同卷时，不能误认原数据被删。不是让两个PostgreSQL服务器同时读写同一数据目录。兼容版本下复用数据与跨大版本升级不同，后者仍需要数据库升级或迁移流程。卷不是备份，删除卷会丢失其中保存的数据，不能未经确认清理。

2026-10-20卷配置文本验收通过：db内正确引用postgres_data:/var/lib/postgresql，顶层声明与services同级。尚未启动Compose、创建实际卷或验证数据库持久化；配置保存与真实资源创建应区分。

### PostgreSQL健康检查：进程启动与可接收连接不同

首次初始化数据库需要时间，容器进程已启动不代表PostgreSQL已接收连接，也不代表业务表存在。Compose中db.healthcheck描述由Docker在数据库容器内定期运行的检查：

```yaml
healthcheck:
  test: ["CMD", "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "task_manager_container"]
  interval: 5s
  timeout: 3s
  retries: 10
  start_period: 10s
```

此处test的CMD是直接执行程序的检查类型，不是Dockerfile默认启动指令。pg_isready是官方PostgreSQL镜像内已有的工具，-h指定主机（省略时常用本地Unix套接字），-U指定用户，-d指定库。检查发生于db容器，因此127.0.0.1指db本身；API从另一容器连接仍使用服务名db。显式TCP地址也有助于避免把初始化阶段仅本地套接字上的临时服务误认为最终TCP服务就绪。

pg_isready通过退出码传递结果：0接收连接，1拒绝连接（例如启动中），2无响应，3参数等问题导致未尝试连接。它不验证API密码认证成功，不检查Task Manager表，不替代Alembic迁移或API实际查询。

interval为常规检查间隔5秒，timeout为单次检查超时3秒，连续失败10次标记unhealthy；start_period提供10秒启动失败宽限，宽限期内失败不计入该连续失败计数，成功可提前进入healthy。宽限期不是无条件等待十秒后才检查。健康状态和容器进程状态不同；标记unhealthy不由本配置自动重启数据库，也不自动创建业务表。

2026-10-21已核对db.healthcheck字段及参数正确，导师在独立子进程提供虚构占位密码运行compose config --quiet，退出0。占位变量未写入文件或持久环境；此检查未创建容器或数据库，真实pg_isready运行结果仍待启动后验收。后续api使用depends_on的service_healthy条件消费该状态，再启动API。

参考：[Compose启动顺序](https://docs.docker.com/compose/how-tos/startup-order/)、[pg_isready](https://www.postgresql.org/docs/18/app-pg-isready.html)。

### depends_on：API等待数据库健康后启动

api下添加depends_on，与build、ports、environment同级；db是依赖服务名称，condition: service_healthy要求Compose启动API前等数据库健康检查通过。

```yaml
depends_on:
  db:
    condition: service_healthy
```

配合db.healthcheck形成启动db→初始化并监听TCP→pg_isready成功→db为healthy→启动API→执行CMD/Uvicorn的流程。YAML服务书写先后顺序不替代该条件，普通进程启动状态也不等于健康。等待不自动执行Alembic、不验证API密码或任务表；数据库以后故障，不会由该配置自动暂停、重启API或持续保证连接可用。

2026-10-21实际核对api.depends_on.db.condition正确，使用独立子进程虚构密码解析完整Compose，退出0。此验证只解析配置，不创建实际资源，也不证明独立数据库已初始化。下一步先用真实运行时变量启动db，再查看健康状态，暂不启动API。

### 首次启动独立数据库：运行时密码与等待健康

在同一PowerShell终端中准备运行时密码：

```powershell
$containerPassword = Read-Host "请输入独立容器数据库密码" -AsSecureString
$env:TASK_MANAGER_CONTAINER_DB_PASSWORD = [System.Net.NetworkCredential]::new("", $containerPassword).Password
```

第一行等待用户输入，-AsSecureString让输入不以明文显示，返回SecureString对象，保存到PowerShell普通变量$containerPassword。第二行从右向左理解：创建临时凭据对象→读取密码字符串→赋给环境变量。

| 语句部分 | 含义、输入与结果 |
| --- | --- |
| `[System.Net.NetworkCredential]` | 引用.NET提供的凭据类；PowerShell可使用.NET类型，不是项目自己定义的类 |
| `::new("", $containerPassword)` | 调用构造函数创建对象，类似Python的类名(...)；第一个参数为用户名，这里用空字符串，第二个参数为之前得到的SecureString密码 |
| `.Password` | 读取凭据对象的属性，不是方法，因此没有调用括号；返回普通.NET String，包含密码明文内容 |
| `$env:TASK_MANAGER_CONTAINER_DB_PASSWORD` | 访问当前PowerShell进程的同名环境变量；$env:是语法前缀，后面是变量名 |
| `=` | 将右侧计算出的字符串赋给左侧环境变量；赋值本身不会将密码打印到终端 |

使用NetworkCredential只是借助临时对象取得普通字符串，不会连接网络、登录数据库、验证密码或修改数据库密码。环境变量需要字符串，不能把SecureString对象本身当作实际密码直接传递。为理解可将原语句展开如下，无需重复执行或打印中间变量：

```powershell
$credential = [System.Net.NetworkCredential]::new("", $containerPassword)
$passwordText = $credential.Password
$env:TASK_MANAGER_CONTAINER_DB_PASSWORD = $passwordText
```

完整数据流：用户输入→SecureString普通变量→临时凭据对象→Password属性返回普通字符串→当前进程环境变量→之后启动的Docker Compose子进程继承→Compose用`${TASK_MANAGER_CONTAINER_DB_PASSWORD:?...}`填入配置→传给db容器成为POSTGRES_PASSWORD（另一路传给api成为TASK_MANAGER_DB_PASSWORD）。数据库首次初始化时才读取POSTGRES_PASSWORD实际设置数据库用户密码，设置PowerShell变量不等于已经设置数据库密码。

普通变量$containerPassword供PowerShell使用，不会像环境变量那样自动交给子进程；$env:设置仅影响当前进程及随后启动的子进程，不自动传播到另一个已打开终端，也不是永久用户级环境变量设置。实际密码不写入命令文本、Compose或.env；但取得.Password后密码已是普通字符串，进程环境和容器配置不是加密秘密存储。输入隐藏不等于全程加密，不能打印中间密码变量或发送给他人。字符串对象或SecureString的生命周期与环境变量有效范围也应分开理解；丢弃一个变量名不保证所有密码副本都立即从内存消失。

在项目根目录执行docker compose up -d --wait --wait-timeout 120 db：up按配置创建/更新并启动指定服务，-d后台运行，--wait等待运行/健康状态，--wait-timeout限制等待秒数，末尾db只选择数据库服务，不启动API。首次可能下载postgres:18、创建项目默认网络与命名卷、初始化独立数据库；不修改没有挂载给它的本机原库。超时不保证容器自动停止或删除，应检查真实状态。docker compose ps查看当前项目服务及健康状态；db未发布宿主端口，PORTS没有宿主映射属于正常设计，后续API通过内部网络连接。

配置正确、使用者反馈已执行、助手实际核验是不同证据。2026-10-21用户反馈完成，但导师检查当前Docker容器列表及compose ls未发现Compose项目或PostgreSQL容器，compose exec返回db未运行；因此不能记为初始化通过，需核对终端启动输出后再推进迁移，不能直接把“已完成”当成数据库真实存在。

### 同一API镜像运行迁移：覆盖默认CMD

`docker compose build api`根据api.build准备服务镜像，不启动API。Compose默认镜像名称不同于手工task-manager-api:v1，但可以复用同一Dockerfile的构建缓存。

2026-10-22镜像选择补充：run/up中的api是Compose服务名，不是对镜像名称进行模糊搜索。当前未设置image，Compose按项目名和服务名确定task_managers_2-api:latest；构建日志naming to该名称确认本次标签。重新build成功后，同一标签指向新构建结果，旧镜像或旧容器可能仍保留。latest只是标签，不会扫描并挑选所有API镜像中时间最新的一个。若显式配置image: task-manager-api:v2，则按该镜像引用选择；build时也可使用该名称标记结果。构建更新标签不改变已运行容器，仍需up使API使用新镜像。

迁移命令为：

```powershell
docker compose run --no-deps --name task-manager-migrate-v1 api python -m alembic upgrade head
```

语法边界为compose run [选项] 服务名 [本次命令及参数]。--no-deps不额外启动依赖，要求db已运行；--name指定一次性任务容器名，退出后仍占用该名称。api选择服务配置，之后的python -m alembic upgrade head是本次启动命令，不是传给已运行HTTP接口的请求。run创建新任务容器，使用服务镜像、网络与environment，默认不发布该服务ports；它不是在已有API容器里执行命令。

当前镜像用CMD登记Uvicorn默认启动命令；compose.yaml没有额外command或entrypoint。本次run在服务名后明确提供命令，替代该新容器的默认CMD，不修改Dockerfile、镜像或其他容器。若未提供新命令，当前配置会用原CMD。镜像同时包含Uvicorn、Alembic及源码/迁移文件，因此可选择启动HTTP服务或执行迁移后结束。后续有ENTRYPOINT时，组合规则需另行解释，不能把此例无条件推广。

执行链为Compose插值并注入API数据库变量→任务容器运行Alembic→读取alembic.ini与env.py→database.py生成指向db/task_manager_container的URL→连接独立数据库→执行已有两版upgrade→提交迁移并退出。此处实际修改目标库结构，不启动Uvicorn。迁移容器退出0本身应结合数据库事实确认，不仅凭保存配置或镜像存在判定通过。

2026-10-21导师实际核验task-manager-migrate-v1状态exited、退出码0、Config.Cmd为Alembic命令，日志执行042f491f9a4a和f959d63045e7；只读查询确认当前库task_manager_container、版本f959d63045e7，public有alembic_version/tags/task_tags/tasks，tasks有created_at字段。未访问或修改本机原库；API HTTP服务和业务请求仍待验证。

### Compose启动API与查看项目容器

`docker compose up -d api`按服务配置创建或启动API，未提供覆盖命令时使用镜像CMD运行Uvicorn，数据库健康条件通过后启动。不等同于compose run临时迁移任务。首次创建/配置变化与单纯启动的行为由Compose根据现有资源判断，不能认为每次up必然新建所有容器。

`docker compose ps`列当前Compose项目的运行服务容器，不启动或停止服务；ps -a包含停止的项目容器。docker container ls则列当前Docker环境的运行容器，可能同时出现其他项目及Nginx教学容器。SERVICE对应YAML逻辑服务名，NAME是实际容器名，STATUS的Up表示运行，healthy表示健康检查通过，PORTS显示发布关系。db显示5432/tcp不代表该端口已发布至Windows；api的127.0.0.1:8000->8000/tcp明确表示本机映射。

验收应分层：API容器Up→HTTP文档可访问→真实数据库查询成功。/docs展示文档不能独自证明数据库连接成功；GET /tasks实际执行查询，空库应返回[]。compose logs --tail 30 api读取API末尾30行标准输出/错误，不重新启动服务。

2026-10-21用户反馈命令及页面符合预期，导师只读核实api运行、db healthy，GET /openapi.json返回200且标题Task Manager 4.0，GET /tasks返回200和空列表。容器网络、认证及迁移后列表查询链已通过；尚未验收容器化创建写入、容器重建后的卷数据保留或Windows重启恢复，未导入历史JSON。

### Compose build与up：首次部署、恢复和更新分别处理

`docker compose build api`读取api.build及Dockerfile，准备基础环境、安装依赖、复制源码并保存默认启动命令，生成镜像但不启动API、不执行Uvicorn，也不等待数据库健康。已运行的API容器不会因构建完成就自动更新。

`docker compose up -d --wait --wait-timeout 120 api`组织运行环境，按depends_on启动或等待数据库，通过后创建/启动API，注入运行环境并执行默认CMD。已有配置或镜像变化时可能重建容器，不是无条件复用；镜像不存在时可能触发构建，但不能因源码改了就假定普通up一定重建镜像。--wait对当前API只等待运行状态，仍需查询接口验证。

| 场景 | 操作选择与判断 |
| --- | --- |
| 首次空环境 | 准备密码、启动db、build api、run执行Alembic、up api、ps及HTTP验收 |
| 普通恢复 | 镜像/配置/源码未变且卷保留时，准备同一密码后up整套服务，不机械重建或迁移 |
| 更新Python业务代码 | build api，再up api使服务使用新镜像；出现容器替换时遵循操作授权 |
| 新增表结构迁移 | 需让迁移任务使用包含新脚本的镜像，并在确认目标后执行迁移，不仅更新HTTP容器 |

显式合并构建与启动可写`docker compose up -d --build --wait --wait-timeout 120 api`，--build要求启动前构建，仍可复用构建缓存。这是更新流程，不是当前普通恢复练习必须执行的命令；不自动运行Alembic。首次安装README里的完整命令组不能当成每次恢复都要重做的清单。

### 新终端恢复：配置、镜像、迁移与服务范围分别判断

新终端不继承另一个已打开终端中临时设置的环境变量，因此需重新提供原有TASK_MANAGER_CONTAINER_DB_PASSWORD，必要时准备Docker命令PATH，并进入项目根目录。Read-Host输入的是已有容器数据库密码，不是借重新启动设置新密码。变量赋值应以$containerPassword开始，不在前面添加image等无关文字。config --quiet只校验配置，不启动服务。

用户实际新终端练习中遇到两处已解释的问题：docker无法识别时尚未执行到Compose，应先将D:\Docker\resources\bin加入当前终端PATH，无需重复输入已在该终端设置的密码；bad flag syntax: ---quiet是三个短横线，应为两个短横线的--quiet。前者是命令查找问题，后者是参数解析问题，均不能直接归因为数据库密码或连接故障。此轮PATH步骤使用了导师提示，不记为无提示独立完成。

`docker compose up -d --wait --wait-timeout 120 db`只选择数据库服务，不会因为API依赖db就反向启动API；省略末尾服务名则恢复当前配置中的整套默认服务。应区分“依赖先满足”与“启动依赖后自动启动所有使用者”。

恢复时分别判断：源码/依赖/Dockerfile未变化且本地镜像仍在，无需重建镜像；原数据卷仍在、迁移已应用且没有新增迁移，无需为普通停启再次迁移。两项依据不同，不以一句“之前成功过”替代状态检查。配置、密码、镜像或数据卷丢失时需按实际问题处理，不能只重复启动命令。

验收分两层：compose ps确认API Up与db healthy；GET /tasks/1确认原任务可实际读回。路由是复数/tasks，不是/task，查询ID应来自已创建记录，不能假设每个新环境都有ID=1。当前练习用已确认存在的任务1。用户首次口述理解了密码准备和已有镜像复用，但遗漏API启动，路由写成单数且密码赋值多写image；导师已指出并解释。此为有提示口述练习，尚未证明新终端独立恢复通过，也不是Windows重启验收。

恢复练习最终输出显示用户重复执行首次启动清单：build api中依赖层CACHED、COPY . .重新执行，生成新API镜像，随后up采用新镜像替换API容器。文档等非业务文件也在当前COPY范围内，因此业务代码未变不保证镜像内容未变。再次upgrade head仅有环境日志、没有Running upgrade，与数据库已在head一致；并非重新创建已有表。实际任务1与同一数据库卷保留，恢复结果通过，但流程选择存在冗余，记录为有提示练习，不要求立即重新停启。Found orphan containers涉及保留的一次性迁移容器，不等于业务服务失败；不要只为去掉警告就执行remove-orphans，删除仍须确认。

### 停启与替换容器的持久化验收

docker compose stop正常停止项目服务而不删除容器、网络或卷；随后up -d --wait --wait-timeout 120恢复当前默认服务。未指定服务名时处理整套默认服务；up可创建或按变化重建，不总等同start。--wait隐含后台运行，-d可显式表达同一意图。db有健康检查须到healthy，api当前没有健康检查只等运行状态；120限制等待阶段，不限制服务运行时长，不保证涵盖所有下载/构建耗时。超时不会保证回滚或停止已经运行的容器。用户已反馈停启后/tasks/1保留，不能仅凭此证明容器被替换后仍持久保存。

2026-10-21用户明确授权删除旧数据库容器并保留原卷进行重建。导师先停止API，使用pg_dump -Fc备份独立容器库到D:\DockerData\backups（备份命令成功且文件具有PGDMP头，未做恢复演练）；再执行compose up -d --no-deps --force-recreate --wait --wait-timeout 120 db，强制替换指定服务容器但不删除命名卷。此命令包含旧容器删除，不作为未经确认可执行的普通只读命令。

实际旧db容器ID d57023a294ca，新ID 66e013a3e621，挂载实际卷均为task_managers_2_postgres_data，db healthy。随后compose start api恢复已有API容器，GET /tasks/1返回200及原任务、high、false和docker/persistence标签；SQL确认库名task_manager_container、迁移版本f959d63045e7、任务数1。没有重新初始化业务数据或再次迁移，证明本轮同一PostgreSQL主版本下换容器并复用原卷保留了数据。未删除卷、未执行down -v、未触及本机原库；跨版本升级、机器重装和备份恢复能力仍不能由本实验推出。

### 日志与停止、恢复服务

`docker container logs --tail 10 web-demo`读取标准输出/标准错误日志末尾10行，不重新执行程序；未指定--tail时默认读取全部已有日志，默认不持续跟踪。当前官方Nginx镜像将访问日志输出到这里，可观察GET / HTTP/1.1及状态码；200为成功，304表示缓存验证后可继续使用缓存，不是故障。日志还可能包含初始化信息、图标请求，不保证每次刷新只有一行。

`docker container stop web-demo`请求主程序正常结束，超过等待期限才强制终止，不删除镜像或容器。浏览器已显示的页面不会随之消失，要重新请求（例如Ctrl+F5）观察服务不可用。`docker container start web-demo`重新运行原容器，原端口映射保留，无需重复指定-p，新请求恢复。用户已反馈日志、停止后不可连接、启动后网页恢复均符合预期；本轮助手没有重跑实验。

参考：[Docker概览](https://docs.docker.com/get-started/docker-overview/)、[容器](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)、[Compose](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-docker-compose/)、[数据卷](https://docs.docker.com/engine/storage/volumes/)、[Windows安装](https://docs.docker.com/desktop/setup/install/windows-install/)、[运行容器](https://docs.docker.com/reference/cli/docker/container/run/)、[官方中文界面需求](https://github.com/docker/roadmap/issues/543)。

## pytest共享fixture：`conftest.py`

2026-10-23补充`--noconftest`：加此选项表示不加载conftest.py；不加则按目录规则加载相关文件并注册fixture。测试文件自身定义的fixture和pytest内置的monkeypatch仍可使用，因此自带mock_post、mock_generate、ai_client的两个AI测试文件可以独立运行。

当前tests/conftest.py提供database_session、task_client、database_client。完整回归的测试请求task_client时，pytest先准备database_session，建立连接与外层事务，再让API使用测试会话，最后回滚并关闭连接。如果用--noconftest跳过这些定义，需要它们的测试通常会报fixture 'task_client' not found，这是测试准备失败，不等于业务断言失败。

| 运行方式 | 是否加载conftest.py | 本项目用途 |
| --- | --- | --- |
| `python -m pytest -q` | 是 | 在专用数据库运行完整回归 |
| `python -m pytest --noconftest tests/test_deepseek_demo.py tests/test_ai_routes.py -q` | 否 | 两个自带fixture的AI离线测试文件 |

加载conftest.py会执行顶层导入，但不会立即执行所有fixture。当前导入database会读取密码配置；被请求的数据库fixture才真正建立连接。--noconftest不是禁用网络或数据库的安全开关，测试文件自行请求时它不会阻止；离线保障来自Mock和测试设计。`-p no:cacheprovider`单独控制禁用pytest缓存插件，不负责fixture加载。

`conftest.py`是pytest自动加载的本地测试配置文件，可以集中定义多个测试模块需要的fixture。测试通过函数参数请求fixture，不需要`from conftest import ...`。pytest从测试所在模块和目录逐步向上寻找可用fixture；上级目录的fixture可供下级测试使用，兄弟目录专属fixture不会自动互相可见。

### `@pytest.fixture`是什么

`pytest.fixture()`是pytest提供的装饰器函数。它把一个普通Python函数注册成由pytest管理的**测试夹具（test fixture）**，用于集中准备测试需要的数据或资源，并在需要时负责清理。

```python
@pytest.fixture
def sample_task():
    return Task(
        id=1,
        title="学习pytest",
    )
```

装饰器形式可以近似理解为：

```python
def sample_task():
    return Task(...)

sample_task = pytest.fixture(sample_task)
```

测试函数通过同名参数向pytest申请fixture：

```python
def test_task_title(sample_task):
    assert sample_task.title == "学习pytest"
```

pytest执行时会完成：

```text
发现测试参数sample_task
    ↓
寻找同名fixture
    ↓
执行fixture并取得产出的值
    ↓
把该值注入测试函数参数
    ↓
执行测试
```

测试函数中的`sample_task`是fixture产出的`Task`对象，不是fixture函数本身。fixture应由pytest按参数名解析，不应手动调用`sample_task()`。

### `return`与`yield`两种fixture

只需要准备普通数据、不需要测试后清理时，可以使用`return`：

```python
@pytest.fixture
def sample_task():
    return Task(id=1, title="测试任务")
```

数据库Session、文件或客户端等需要释放的资源应使用`yield`：

```python
@pytest.fixture
def database_session():
    session = create_session()

    try:
        yield session
    finally:
        session.close()
```

`yield`把fixture分为准备与清理两个阶段：

```text
yield之前：准备资源
yield的值：注入测试或其他fixture
测试执行期间：fixture暂停
yield之后：测试结束后恢复并清理
```

资源型fixture使用`try/finally`，可以在断言失败或测试抛出异常时仍然进入`finally`，尽力完成回滚、关闭连接或清除依赖覆盖。如果fixture在到达`yield`前就失败，测试函数不会执行，因此创建多项资源时也要考虑已经成功创建部分的清理顺序。

### fixture的执行条件和作用域

定义fixture不等于立即执行。pytest通常只在以下情况运行它：

1. 测试函数声明同名参数；
2. 另一个fixture声明对它的依赖；
3. fixture设置了`autouse=True`；
4. pytest配置显式要求使用它。

`scope`控制fixture实例可以复用多久：

| `scope` | 生命周期 |
| --- | --- |
| `"function"` | 每个测试案例创建一次，默认值 |
| `"class"` | 每个测试类创建一次 |
| `"module"` | 每个测试模块创建一次 |
| `"package"` | 每个测试包创建一次 |
| `"session"` | 整次pytest运行创建一次 |

当前数据库fixture应保持默认的`scope="function"`，使每个测试拥有独立事务，测试A写入的数据不会影响测试B。`autouse=True`会让fixture在测试未声明参数时也自动执行，容易隐藏依赖，当前数据库资源应继续通过参数显式申请。

fixture还支持`name=`修改注册名称、用`params=`提供多组资源配置等参数；当前阶段优先掌握默认名称、`function`作用域、依赖注入和清理生命周期，普通输入组合继续使用`@pytest.mark.parametrize`通常更直观。

此前`tests/conftest.py`只定义`database_client`，`tests/test_database_api.py`仅保留测试函数及参数化所需的`import pytest`。同目录的过滤和统计测试文件都可以声明`database_client`参数。

```text
tests/conftest.py：定义database_client
tests/test_database_api.py：请求database_client
tests/test_database_filters.py：也可以请求database_client
```

共享定义的位置不会改变fixture生命周期。默认`scope="function"`意味着每条测试案例仍独立准备Connection、外层事务、Session和TestClient，并在结束时清理；不意味着多个测试共用同一个Session。

### fixture依赖与职责拆分

fixture不仅可以注入测试函数，也可以注入另一个fixture。下面的`database_client`声明了`database_session`参数，pytest会先寻找并执行同名fixture，再把它`yield`出来的Session对象传入客户端fixture：

```python
@pytest.fixture
def database_session():
    ...
    yield session
    ...


@pytest.fixture
def database_client(database_session):
    ...
```

这种关系称为**fixture依赖（fixture dependency）**或**fixture组合（fixture composition）**。它不是手动执行：

```python
database_session()
```

而是pytest根据函数参数名自动解析依赖、取得fixture产出的值。

当前拆分目标是让两个fixture各自只管理一种职责：

| fixture | 负责创建和清理的资源 | 可以供谁使用 |
| --- | --- | --- |
| `database_session` | Connection、外层事务、Session、最终回滚和关闭 | Repository测试、`database_client` |
| `database_client` | FastAPI依赖覆盖、TestClient、清除依赖覆盖 | API测试 |

执行顺序为先准备依赖，再准备使用者；清理顺序与创建顺序相反：

```text
创建database_session
    ↓
把Session注入database_client
    ↓
执行测试
    ↓
清理database_client中的依赖覆盖
    ↓
清理database_session，回滚事务并关闭资源
```

这个逆序清理保证TestClient不再使用Session以后，才真正关闭Session和Connection。

资源型fixture应把`yield`放在`try/finally`中：

```python
@pytest.fixture
def database_session():
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(...)

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()
```

`yield`之前负责准备资源，`yield`的值会被注入测试或其他fixture，`finally`负责清理。即使测试断言失败或抛出异常，pytest恢复fixture后仍会进入`finally`，尽力完成回滚和关闭。

拆分时不能让`database_client`重新创建另一份Session。API依赖覆盖必须`yield database_session`，这样HTTP接口和直接Repository操作才使用同一条Connection和同一个外层事务，测试结束时才能由一处统一回滚。

### 当前代码中的三个`yield`

当前测试结构中出现三个`yield`，它们由两个不同的依赖系统管理：

| 位置 | 管理者 | 产出的对象 | 接收者 |
| --- | --- | --- | --- |
| `database_session`中的`yield session` | pytest | SQLAlchemy `Session` | Repository测试或`database_client` |
| `override_get_session`中的`yield database_session` | FastAPI | 同一个测试Session | 路由中的`Depends(get_session)` |
| `database_client`中的`yield TestClient(app)` | pytest | `TestClient` | API测试函数 |

完整关系为：

```text
database_session fixture
    yield Session
        ↓ pytest注入
database_client(database_session)
    ├── override_get_session
    │       yield同一个Session
    │           ↓ FastAPI注入
    │       API路由函数
    │
    └── yield TestClient
            ↓ pytest注入
        API测试函数
```

测试结束后，pytest先恢复`database_client`并清除FastAPI依赖覆盖，再恢复`database_session`，关闭Session、回滚外层事务并关闭Connection。这正是“先创建依赖、后创建使用者；先清理使用者、后清理依赖”。

### 常见错误

- 手动调用fixture函数，而不是在测试参数中申请它；
- 定义了fixture，但测试没有声明参数，误以为它会自动执行；
- 资源型fixture在`yield`后没有关闭或回滚；
- 没有用`try/finally`明确保护清理过程；
- `database_client`和`database_session`分别创建Session，导致API写入不受同一个外层事务控制；
- 把测试参数误认为fixture函数。测试中的`database_client`实际是`TestClient`，`database_session`实际是`Session`。

pytest加载`conftest.py`时执行其顶层导入。当前顶层导入`database`，该模块读取`TASK_MANAGER_DB_PASSWORD`，所以即使只选择模型测试，也需要设置该环境变量。加载fixture定义不会自动执行fixture函数或连接数据库；只有测试请求fixture时才创建资源。以后若需要模型测试脱离数据库配置运行，可以调整导入位置或将数据库fixture放进专门子目录。

2026-10-09迁移验收：完整测试套件实际得到`15 passed`、无warning，证明fixture自动发现正常且原测试行为保持有效。

## 文档作用

本文档用于记录项目驱动学习过程中遇到的具体问题、关键结论、底层原理和易错点。它不是项目进度表，也不替代 README；重点保存那些“代码会写，但概念容易混淆”或“以后可能再次遇到”的知识。

记录新问题时，优先使用下面的结构：

1. **问题场景**：当时在写什么代码，为什么产生疑问。
2. **核心结论**：用一两句话直接回答问题。
3. **原理说明**：解释不同层次、对象职责和执行过程。
4. **项目示例**：使用 Task Manager 当前代码展示正确写法。
5. **专业术语**：记录更准确的技术表达。
6. **易错点**：列出容易混淆或写错的形式。

---

## SQLAlchemy ORM：关系路径 JOIN 与原生 SQL JOIN

### 问题场景

原生 SQL 的 `JOIN` 后通常跟表名：

```sql
SELECT tasks.*
FROM tasks
JOIN task_tags
    ON tasks.id = task_tags.task_id
JOIN tags
    ON task_tags.tag_id = tags.id;
```

SQLAlchemy ORM 查询却可以写成：

```python
.join(TaskRecord.tags)
```

这里为什么使用 `TaskRecord.tags`，而不是直接使用映射类 `TagRecord`？

### 核心结论

原生 SQL 的 `JOIN` 直接操作数据库表；SQLAlchemy ORM 的 `.join(TaskRecord.tags)` 沿着已经声明好的 ORM 关系路径进行连接。

`TaskRecord.tags` 已经包含以下信息：

- 起点是 `TaskRecord`，对应 `tasks` 表；
- 终点是 `TagRecord`，对应 `tags` 表；
- 中间经过 `task_tags_table`；
- 外键提供两段连接条件。

因此 SQLAlchemy 能根据这一个关系属性生成经过关联表的两段 SQL JOIN。

### 原理说明

模型中的关系定义如下：

```python
tags: Mapped[list["TagRecord"]] = relationship(
    secondary=task_tags_table,
    back_populates="tasks",
)
```

其中：

- `relationship()` 描述 Python 对象之间怎样互相访问；
- `secondary=task_tags_table` 指明多对多关系使用的中间关联表；
- `ForeignKey("tasks.id")` 和 `ForeignKey("tags.id")` 描述数据库字段之间的连接。

所以：

```python
.join(TaskRecord.tags)
```

可以理解为：

> 沿着 `TaskRecord.tags` 多对多 ORM 关系，从任务连接到标签。

SQLAlchemy 最终生成的 SQL 仍然需要连接真实表，逻辑上类似：

```sql
FROM tasks
JOIN task_tags
    ON tasks.id = task_tags.task_id
JOIN tags
    ON tags.id = task_tags.tag_id
```

### 为什么不只写 TagRecord

下面的代码只提供了目标模型：

```python
.join(TagRecord)
```

但 `tasks` 与 `tags` 之间没有直接外键，它们通过 `task_tags` 间接连接。只给出 `TagRecord` 时，ORM 未必能确定应当沿哪条路径连接。

使用：

```python
.join(TaskRecord.tags)
```

则明确指定了完整关系路径：

```text
TaskRecord
→ task_tags_table
→ TagRecord
```

需要同时明确目标和连接依据时，也可能写成：

```python
.join(TagRecord, TaskRecord.tags)
```

当前关系已经包含目标模型，因此简写为 `.join(TaskRecord.tags)` 更清楚。

### 类属性与对象属性的区别

```python
task.tags
```

表示某个具体任务对象关联的标签列表。

```python
TaskRecord.tags
```

表示 ORM 类上的关系属性，可以用于构造查询、JOIN 和加载策略。

同样：

```python
task.title
```

是具体标题值，而：

```python
TaskRecord.title
```

是可以用于 `.where()` 等查询表达式的 ORM 字段属性。

### 专业术语

- **多对多关系（many-to-many relationship）**：多个任务可以关联多个标签。
- **关联表（association table）**：`task_tags`，负责保存任务与标签的对应关系。
- **ORM 关系属性（ORM relationship attribute）**：例如 `TaskRecord.tags`。
- **关系路径 JOIN（relationship-bound JOIN）**：沿 ORM 已声明的关系执行连接。
- **连接条件（ON clause）**：原生 SQL 中 `ON` 后描述字段如何对应的条件。

### 易错点

1. `.join(TaskRecord.tags)` 不是把标签列表直接交给数据库，而是把类级别的 ORM 关系交给 SQLAlchemy构造查询。
2. `task.tags` 是对象数据；`TaskRecord.tags` 是关系描述，两者用途不同。
3. 连接了多张表，不代表查询结果一定返回多个对象；结果由 `select(...)` 中选择的目标决定。
4. `ForeignKey` 描述数据库字段关系，`relationship()` 描述 Python对象关系，两者职责不同。

---

## SQLAlchemy ORM：使用 selectinload 批量预加载关联对象

### 问题场景

Task Manager 中，`tasks` 与 `tags` 通过 `task_tags` 建立多对多关系：

```text
tasks
   ↑
task_tags
   ↓
tags
```

模型通过 `relationship()` 提供对象关系属性：

```python
class TaskRecord(Base):
    tags: Mapped[list["TagRecord"]] = relationship(
        secondary=task_tags_table,
        back_populates="tasks",
    )
```

查询任务列表后，如果逐个访问 `task.tags`，默认延迟加载可能为每个任务额外执行一次标签查询，形成 N+1 查询问题。

### 核心结论

`selectinload()` 是 SQLAlchemy ORM 的一种**关系预加载策略（relationship eager loading strategy）**。它先查询主对象，再使用额外一条带 `IN (...)` 条件的 SQL，批量加载这批主对象关联的对象。

项目中的典型写法：

```python
statement = (
    select(TaskRecord)
    .options(selectinload(TaskRecord.tags))
    .order_by(TaskRecord.id.asc())
)

with Session(engine) as session:
    tasks = session.scalars(statement).all()

    for task in tasks:
        for tag in task.tags:
            print(tag.name)
```

这里：

- `select(TaskRecord)` 决定查询结果是 `TaskRecord` 对象；
- `.options(...)` 为 ORM 查询增加加载策略；
- `selectinload(TaskRecord.tags)` 要求批量预加载 `tags` 关系；
- `TaskRecord.tags` 是类级别的 ORM 关系属性，不是某个任务对象的标签列表；
- 查询结果类型没有改变，仍然是 `TaskRecord` 对象集合；
- 之后访问 `task.tags` 时，标签通常已经加载完成，不再逐个查询数据库。

### 执行过程

假设本次查询得到任务 1 和任务 2，`selectinload()` 通常分两步执行。

第一步查询主对象：

```sql
SELECT tasks.id, tasks.title, tasks.done, tasks.priority
FROM tasks
ORDER BY tasks.id ASC;
```

SQLAlchemy得到：

```text
TaskRecord(id=1, ...)
TaskRecord(id=2, ...)
```

第二步收集这些对象的主键，批量查询关联对象：

```sql
SELECT task_tags.task_id, tags.id, tags.name
FROM task_tags
JOIN tags
    ON tags.id = task_tags.tag_id
WHERE task_tags.task_id IN (1, 2);
```

第二条 SQL 同时返回任务 1 和任务 2 的标签关系。SQLAlchemy再按照 `task_tags.task_id` 把标签分配到对应对象：

```text
task 1 → [python, database]
task 2 → []
```

因此业务代码仍然只需访问：

```python
task.tags
```

### `selectinload` 名称的含义

这个名称可以拆成：

```text
select + in + load
```

- `select`：额外执行一条 SELECT；
- `in`：使用主键集合构造 `WHERE ... IN (...)`；
- `load`：把查询到的关联对象加载到 ORM 关系属性中。

它不是 Python列表的 `in` 运算，而是描述通常采用的 SQL加载方式。

### 与延迟加载的区别

默认延迟加载（lazy loading）会在第一次访问某个对象的关系属性时查询：

```python
tasks = session.scalars(select(TaskRecord)).all()

for task in tasks:
    print(task.tags)
```

假设有 N 个任务，可能出现：

```text
1条SQL查询全部任务
+ N条SQL分别查询每个任务的标签
= 1 + N条SQL
```

使用 `selectinload()` 后通常变成：

```text
1条SQL查询全部任务
+ 1条SQL批量查询这些任务的标签
= 2条主要业务SQL
```

因此它特别适合列表接口中加载集合关系，例如：

```text
查询任务列表 + 每个任务的标签
查询用户列表 + 每个用户的订单
查询文章列表 + 每篇文章的评论
```

SQLAlchemy首次连接 PostgreSQL时还可能执行版本、Schema等初始化查询；这些不是 N+1 业务查询。只读 Session关闭时日志中的 `ROLLBACK` 也只是结束当前只读事务，不表示查询失败。

### 适用的关系类型

`selectinload()` 针对 `relationship()` 定义的 ORM关系，不只适用于多对多关系。

常见场景包括：

- 一对多：`user.tasks`；
- 多对一：`task.user`；
- 一对一：`user.profile`；
- 多对多：`task.tags`。

当前项目属于：

> 通过 `task_tags` 关联表建立多对多关系，并使用 `selectinload()` 批量预加载任务关联的标签。

普通字段不是关系，不能写：

```python
selectinload(TaskRecord.title)  # 错误：title是普通字段
```

正确目标必须是关系属性：

```python
selectinload(TaskRecord.tags)
```

### 关系预加载与跨表筛选的区别

`selectinload()` 的职责是加载关联对象，不负责根据关联表筛选主对象。

例如“查询拥有 `python` 标签的任务”属于关系路径 JOIN 和跨表筛选：

```python
statement = (
    select(TaskRecord)
    .join(TaskRecord.tags)
    .where(TagRecord.name == "python")
)
```

如果还需要返回这些任务的全部标签，可以同时添加：

```python
statement = (
    select(TaskRecord)
    .join(TaskRecord.tags)
    .where(TagRecord.name == "python")
    .options(selectinload(TaskRecord.tags))
)
```

这里：

- `.join(...).where(...)` 负责筛选哪些任务；
- `.options(selectinload(...))` 负责加载筛选结果的标签列表。

### 与 `joinedload()` 的初步区别

`selectinload()` 通常使用额外的 SELECT批量加载关系：

```text
主对象查询 + 关联对象查询
```

`joinedload()` 通常把关系放进同一条 JOIN查询：

```text
主对象与关联对象的一条JOIN查询
```

对于一对多和多对多集合，JOIN可能让同一个主对象在数据库结果中重复多行；`selectinload()` 往往更直观，也通常适合作为列表接口加载集合关系的起点。具体选择仍要结合数据量、关系类型和查询计划，不能把某一种策略固定为所有场景的最优方案。

### 专业术语

- **关系加载（relationship loading）**：为 ORM对象的关系属性加载关联对象。
- **延迟加载（lazy loading）**：第一次访问关系属性时才执行查询。
- **预加载（eager loading）**：在主查询阶段按指定策略提前加载关系。
- **Select IN loading**：`selectinload()` 使用的批量预加载策略。
- **N+1查询问题（N+1 query problem）**：一次主查询后，又为 N 个对象分别执行 N 次关联查询。
- **多对多关系（many-to-many relationship）**：多个任务可以关联多个标签。
- **关联表（association table）**：在当前项目中是 `task_tags`。
- **加载策略（loader strategy）**：决定 ORM关系何时以及怎样加载的策略。

### 易错点

1. 应传入类级别关系 `TaskRecord.tags`，不能传入某个实例的 `task.tags`。
2. `selectinload()` 不改变 `select(...)` 的返回目标；`select(TaskRecord)` 仍返回 `TaskRecord` 对象。
3. `selectinload()` 负责加载关系，不代替 `.join()` 和 `.where()` 完成跨表筛选。
4. 关系必须先通过 `relationship()` 正确声明，`selectinload()` 才知道如何加载。
5. 标签顺序不会因为使用 `selectinload()` 自动得到保证；需要稳定顺序时应另外声明排序规则。
6. `echo=True` 适合学习和调试，不应把大量SQL日志当作业务输出设计的一部分。
7. 对单个对象访问一个关系时，延迟加载可能只有一次额外查询；N+1问题主要出现在列表遍历并逐个访问关系时。

---

## PostgreSQL、psycopg与SQLAlchemy的职责边界

### 三者处在不同层级

```text
Python业务代码
    ↓
SQLAlchemy：组织数据库操作
    ↓
psycopg：执行与PostgreSQL的实际通信
    ↓
PostgreSQL：执行SQL并保存数据
```

| 组件 | 身份 | 主要职责 |
| --- | --- | --- |
| PostgreSQL | 独立运行的数据库服务 | 保存表和数据，执行SQL，处理约束、事务、锁和索引 |
| psycopg | PostgreSQL的Python驱动 | 建立协议连接，发送SQL和参数，接收结果及数据库错误 |
| SQLAlchemy | Python数据库工具库和ORM | 构造查询、映射对象、管理连接池、Session和事务 |

最短记忆方式：

```text
PostgreSQL负责“存和执行”
psycopg负责“实际传输”
SQLAlchemy负责“组织”
```

PostgreSQL不认识`TaskRecord`、`Session`或FastAPI，只认识数据库、表、列、行、SQL、约束和事务。psycopg不知道“完成任务”等业务含义，只负责让Python按照PostgreSQL协议与数据库通信。SQLAlchemy不保存最终数据，也不替代PostgreSQL；连接PostgreSQL时仍需使用psycopg等驱动。

### SQLAlchemy内部的Engine与Session

“SQLAlchemy负责组织”还可以继续拆分：

```text
Session
    ↓ 请求查询、刷新或提交
Engine / SQLAlchemy Connection
    ↓ 选择方言、连接和驱动
psycopg Connection
    ↓ 通过PostgreSQL协议收发数据
PostgreSQL
```

- **Session**组织ORM对象、对象变化和一次工作范围内的事务。它判断需要查询、插入、更新或删除什么。
- **Engine**保存数据库地址、驱动和方言配置，管理连接池，并为Session或Connection提供底层连接。
- **psycopg**真正建立到PostgreSQL的协议连接，发送SQL与参数，并接收结果。

`engine.connect()`取得的是SQLAlchemy Connection；它内部仍包装或使用psycopg的底层连接。Engine管理“怎样取得和使用连接”，不表示Engine自己实现了PostgreSQL网络协议。

创建Session也不一定立即建立新网络连接。Session通常在第一次查询、flush或commit时才通过Engine取得连接；操作结束后，连接通常归还Engine的连接池供后续请求复用。

### 谁把Python操作变成SQL

不能简单说“Session把Python转成SQL”或“Engine单独把Python转成SQL”。更准确的分工是：

```text
Session组织要做什么
→ SQLAlchemy ORM/Core形成SQL表达式或数据库操作
→ SQLAlchemy编译器使用Engine选定的PostgreSQL方言编译SQL
→ psycopg发送SQL和参数
→ PostgreSQL执行
```

例如：

```python
statement = select(TaskRecord).where(
    TaskRecord.priority == "high"
)
```

`select()`和`where()`先构造SQLAlchemy表达式对象，还没有访问数据库。调用：

```python
tasks = session.scalars(statement).all()
```

时，SQLAlchemy根据PostgreSQL方言把表达式编译成类似：

```sql
SELECT tasks.id, tasks.title, tasks.done, tasks.priority
FROM tasks
WHERE tasks.priority = %(priority_1)s;
```

SQL文本和参数再由psycopg发送给PostgreSQL。只有SQLAlchemy认识的查询表达式和ORM操作能够生成数据库操作；普通Python代码不会自动变成SQL。

修改ORM对象时：

```python
task.done = True
session.commit()
```

Session通过工作单元机制发现对象变化，SQLAlchemy ORM形成`UPDATE`操作，编译系统生成适合PostgreSQL的SQL，psycopg负责发送，PostgreSQL最终执行并提交。

### 一次查询的完整往返

```text
1. FastAPI取得请求参数
2. Python代码决定查询条件
3. SQLAlchemy构造并编译SQL
4. Engine从连接池提供底层连接
5. psycopg发送SQL和参数
6. PostgreSQL解析并执行SQL
7. psycopg接收数据库结果并转换基础类型
8. SQLAlchemy把结果映射为TaskRecord对象
9. Pydantic验证并生成响应数据
10. FastAPI发送JSON响应
```

PostgreSQL才是真正进行筛选、排序、聚合和约束检查的组件；SQLAlchemy负责在Python侧描述这些要求并处理返回结果。

### `commit()`在各层的含义

调用：

```python
session.commit()
```

时，各层参与同一项操作，但职责不同：

```text
Session：检查ORM变化，必要时先flush，并请求提交
Engine/Connection：管理当前连接和事务接口
psycopg：把提交命令发送给PostgreSQL
PostgreSQL：真正完成事务提交，使修改持久生效
```

所以“Session提交事务”“psycopg发送提交命令”和“PostgreSQL完成提交”是在描述同一次操作的不同层级。

### 根据错误来源判断边界

| 现象 | 主要来源 |
| --- | --- |
| `NOT NULL`、`UNIQUE`、外键或SQL语法错误 | PostgreSQL检查并拒绝 |
| 认证失败、连接中断、数据库错误转换为Python异常 | psycopg负责通信和异常呈现 |
| ORM映射错误、relationship配置错误、对象不在Session | SQLAlchemy |
| priority非法、任务不存在时返回404、空标签规则 | Pydantic、FastAPI或Service业务层 |

例如`psycopg.errors.UniqueViolation`表示PostgreSQL发现唯一约束冲突，psycopg把数据库错误转换成Python异常；唯一约束本身不是psycopg制定的。

### 可以怎样替换这些层

不用SQLAlchemy时，可以直接使用：

```text
FastAPI → psycopg → PostgreSQL
```

这时需要手写更多SQL、游标处理、结果转换和事务代码。

保留SQLAlchemy而更换数据库时，需要同时更换数据库方言、连接配置以及相应驱动。例如psycopg专用于PostgreSQL，不能直接连接MySQL。大部分通用ORM代码可能保留，但数据库特有SQL和行为仍可能需要修改。

### 快速判断代码属于哪一层

```text
CREATE TABLE、SELECT、FOREIGN KEY、ON DELETE CASCADE
→ SQL和PostgreSQL

psycopg.connect、cursor.execute、fetchone
→ psycopg驱动

create_engine、Session、select、Mapped、relationship
→ SQLAlchemy

@app.get、Depends、HTTPException
→ FastAPI

BaseModel、Field、Literal、field_validator
→ Pydantic
```

遇到混乱时先问：

```text
数据最终保存在哪里？                  → PostgreSQL
Python靠什么与PostgreSQL实际通信？     → psycopg
项目靠什么组织连接、SQL表达式和ORM对象？ → SQLAlchemy
```

## SQLAlchemy 与 FastAPI：Engine、SessionFactory 和 yield Session依赖

### 问题场景

早期数据库实验在每个脚本中重复创建连接配置：

```python
password = getpass(...)
database_url = URL.create(...)
engine = create_engine(database_url)
```

这种方式适合交互式实验，但不适合长期运行的 FastAPI服务器：服务器导入模块时不能等待人工输入密码，路由也不应该为每次请求重新创建 Engine或忘记关闭 Session。

项目因此建立公共数据库模块：

```text
环境变量
→ database_url
→ Engine
→ SessionFactory
→ 每次请求的Session
```

### 核心结论

- **Engine** 保存数据库方言、驱动、连接地址并管理连接池，应用进程通常创建一个；
- **SessionFactory** 是已经绑定 Engine 的 Session工厂，本身不是 Session；
- **Session** 服务一次请求或业务操作，负责 ORM查询、对象状态和事务；
- **get_session()** 使用 `yield` 把 Session交给 FastAPI，并在请求结束后统一关闭；
- 密码通过环境变量进入进程，不写入源码；
- 依赖函数只管理 Session生命周期，不默认替业务代码提交事务。

### 公共数据库模块

当前设计的核心结构：

```python
import os
from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker


database_password = os.environ["TASK_MANAGER_DB_PASSWORD"]

database_url = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=database_password,
    host="localhost",
    port=5432,
    database="task_manager_learning",
)

engine = create_engine(database_url)
SessionFactory = sessionmaker(bind=engine)


def get_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session
```

### 环境变量与失败时机

```python
os.environ["TASK_MANAGER_DB_PASSWORD"]
```

把 `os.environ` 看作当前进程的环境变量映射。使用方括号读取时，如果变量缺失，会立即出现：

```text
KeyError: 'TASK_MANAGER_DB_PASSWORD'
```

这叫作**快速失败（fail fast）**：程序在配置缺失的位置立即停止，而不是把 `None` 传到数据库连接阶段后才出现更难理解的错误。

环境变量与 Python变量处于不同层次：

```text
操作系统或运行配置：TASK_MANAGER_DB_PASSWORD
                    ↓ os.environ读取
Python变量：database_password
                    ↓ URL.create使用
SQLAlchemy URL对象
```

密码不应硬编码在源码、提交到 Git或打印到日志。PyCharm个人运行配置保存在本机；项目已经通过 `.gitignore` 忽略 `.idea/` 和 `.env`，但敏感文件仍需谨慎管理。

### Engine的生命周期

```python
engine = create_engine(database_url)
```

Engine不是一次请求的实际 Session，也不等同于单个数据库连接。它负责：

- 保存数据库类型与驱动信息；
- 知道怎样连接 PostgreSQL；
- 管理连接池；
- 为 Connection或Session提供底层连接；
- 通过 PostgreSQL方言处理数据库差异。

`create_engine()` 通常采用延迟连接。模块导入并创建 Engine时不一定立即访问 PostgreSQL；第一次执行数据库操作时才从连接池取得连接。

一个应用进程通常复用一个 Engine：

```text
一个Engine
├── 请求1使用的Session
├── 请求2使用的Session
└── 请求3使用的Session
```

不应在每个请求中重新调用 `create_engine()`，否则无法有效复用连接池。

### SessionFactory不是Session

```python
SessionFactory = sessionmaker(bind=engine)
```

`sessionmaker()` 返回一个可调用的 Session工厂，并记住以后创建的 Session应当使用哪个 Engine。

```python
SessionFactory     # 工厂本身
SessionFactory()   # 调用工厂，得到一个Session对象
```

多次调用会创建不同的 Session：

```python
session_1 = SessionFactory()
session_2 = SessionFactory()
```

它们共用 Engine和连接池，但各自维护 ORM对象状态与事务边界。FastAPI中通常让每个请求获得自己的 Session，避免不同请求共享同一工作区和事务状态。

### get_session() 为什么使用 yield

```python
def get_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session
```

`return` 会返回值并立即结束函数；`yield` 会提供值并暂停函数，使框架稍后能够恢复执行并完成资源清理。

FastAPI驱动生成器依赖时，执行顺序是：

```text
请求到达
→ 调用get_session()
→ 进入with并创建Session
→ 执行yield session，函数暂停
→ FastAPI把Session注入路由参数
→ 路由和Service执行数据库操作
→ 路由返回或抛出异常
→ FastAPI恢复get_session()
→ 离开with代码块
→ Session关闭，连接归还连接池
```

因此 `yield` 适合表示具有前后生命周期的资源：

```text
准备资源
→ 提供资源
→ 使用结束后清理资源
```

同类资源还包括文件句柄、网络连接和临时资源。

### Generator类型注解

```python
Generator[Session, None, None]
```

三个类型参数依次表示：

```text
Generator[
    yield出去的值类型,
    外部send进来的值类型,
    生成器最终return的值类型,
]
```

当前依赖函数：

- yield一个 `Session`；
- 不接收外部 `send()` 值；
- 不通过 `return` 返回最终值。

所以写成：

```python
Generator[Session, None, None]
```

### FastAPI依赖注入中的使用方式

路由会声明自己需要 Session：

```python
from fastapi import Depends
from sqlalchemy.orm import Session


def get_tasks(
    session: Session = Depends(get_session),
):
    ...
```

这里的依赖注入过程是：

```text
路由声明依赖Session
→ FastAPI调用get_session()
→ FastAPI取得yield的Session
→ FastAPI把Session作为参数传给路由
```

路由不需要知道 Session怎样创建和关闭，只使用注入的对象完成业务操作。

### 为什么get_session()不自动commit

当前依赖函数只负责资源生命周期：

```text
创建Session
提供Session
关闭Session
```

它不默认执行：

```python
session.commit()
```

原因是事务边界属于业务语义：只读查询不需要提交；写操作应当在所有业务步骤成功后提交；业务失败时应回滚。如果依赖函数无条件自动提交，会让提交时机变得隐藏，也可能在业务错误处理不清晰时保存不应保存的部分修改。

当前阶段采用显式方式：

```python
try:
    # 完成一组相关业务写操作
    session.commit()
except Exception:
    session.rollback()
    raise
```

后续会结合 Service和FastAPI路由进一步确定事务边界。

### 专业术语

- **环境变量（environment variable）**：由操作系统或运行环境提供给程序的配置值。
- **快速失败（fail fast）**：在错误源头尽早报告问题。
- **连接池（connection pool）**：可复用的数据库连接集合。
- **工厂（factory）**：专门负责创建某类对象的对象或函数。
- **Session工厂（Session factory）**：创建已绑定指定 Engine的Session。
- **依赖注入（dependency injection）**：由框架创建依赖并传给使用者。
- **生成器依赖（generator dependency）**：使用 `yield` 提供资源，并在使用后继续执行清理逻辑的依赖。
- **资源生命周期（resource lifecycle）**：资源从创建、使用到释放的完整过程。
- **事务边界（transaction boundary）**：一组操作从事务开始到提交或回滚的范围。

### 易错点

1. `SessionFactory` 是工厂，必须调用 `SessionFactory()` 才得到Session。
2. Engine适合应用级复用，Session适合请求级或业务操作级使用。
3. 不要把同一个Session作为全局变量让所有请求共享。
4. `yield session` 后函数只是暂停，路由完成后还会恢复并退出 `with`。
5. 缺少环境变量产生的 `KeyError` 是配置错误，不是数据库连接错误。
6. `get_session()` 关闭Session不等于提交事务；未提交写操作会在关闭时被回滚。
7. 不要在源码、日志、截图或Git提交中暴露数据库密码。
8. 不要在每个路由中重复创建Engine。

---

## FastAPI：使用 Depends把数据库Session注入路由

### 问题场景

数据库路由同时需要两类输入：

```text
客户端输入：URL中的task_id
服务器资源：SQLAlchemy Session
```

客户端可以请求：

```http
GET /database/tasks/1
```

但客户端不应该创建或传递数据库 Session。Session应由服务器为每次请求创建，并在请求结束后关闭。

### 核心结论

FastAPI的 `Depends()` 用于声明依赖：路由只说明自己需要什么对象，FastAPI负责调用依赖函数、取得返回值或yield值，并把它注入路由参数。

```python
def get_database_task(
    task_id: int,
    session: Session = Depends(get_session),
):
    ...
```

这里：

- `task_id` 来自客户端路径；
- `session` 来自服务器内部的 `get_session()`；
- Session不会作为查询参数或请求体出现在 OpenAPI文档中；
- 请求结束后，FastAPI继续执行生成器依赖的清理阶段。

### `Depends(get_session)` 的组成

```python
session: Session = Depends(get_session)
```

可以拆成：

```python
session: Session
```

表示路由代码拿到的是 SQLAlchemy Session，帮助编辑器和类型检查工具理解可用方法。

```python
Depends(get_session)
```

表示这个参数的值由 `get_session` 依赖函数提供。

应传入函数本身：

```python
Depends(get_session)
```

不要提前调用：

```python
Depends(get_session())  # 错误思路
```

FastAPI需要获得可调用对象，才能在每次请求到达时决定何时创建资源、何时恢复生成器并执行清理。

### 客户端参数与服务器依赖

路径函数签名中的参数不一定都来自HTTP客户端。FastAPI会根据声明方式区分来源：

```python
@app.get("/database/tasks/{task_id}")
def get_database_task(
    task_id: int,
    session: Session = Depends(get_session),
):
    ...
```

参数来源：

```text
task_id
→ 路径中存在{task_id}
→ 客户端提供
→ FastAPI转换并校验为int

session
→ 默认值是Depends(get_session)
→ FastAPI调用服务器依赖提供
→ 客户端不提供
```

因此：

```text
/database/tasks/1   → task_id=1
/database/tasks/abc → int校验失败，返回422
```

### 一次请求的完整生命周期

```text
客户端发送GET /database/tasks/1
→ FastAPI匹配路由并校验task_id
→ FastAPI调用get_session()
→ SessionFactory()创建Session
→ get_session()执行yield session并暂停
→ FastAPI把Session传给路由参数
→ 路由调用session.get(TaskRecord, task_id)
→ 路由构造响应或抛出HTTPException
→ FastAPI生成HTTP响应
→ FastAPI恢复get_session()
→ 离开with SessionFactory()上下文
→ Session关闭，连接归还连接池
```

即使路由抛出异常，依赖清理阶段仍应得到执行。这是把资源管理集中到依赖函数的重要原因。

### `session.get()` 与HTTP 404

```python
task = session.get(TaskRecord, task_id)
```

结果：

```text
找到主键 → TaskRecord对象
没有找到 → None
```

数据库查询不到任务不是Python运行错误，但对HTTP客户端来说，请求的资源不存在，所以路由转换为：

```python
if task is None:
    raise HTTPException(
        status_code=404,
        detail="Task not found",
    )
```

这里体现了分层转换：

```text
数据库层：查询结果为None
HTTP层：资源不存在，返回404
```

### ORM对象不能直接使用dataclass的asdict

项目中原有的领域模型是 dataclass：

```python
@dataclass
class Task:
    ...
```

它可以使用 `dataclasses.asdict()` 或自己定义的 `to_dict()`。

SQLAlchemy模型：

```python
class TaskRecord(Base):
    ...
```

不是 dataclass，默认没有：

```python
task.asdict()
task.to_dict()
```

最小实验可以明确构造响应字典：

```python
return {
    "id": task.id,
    "title": task.title,
    "done": task.done,
    "priority": task.priority,
}
```

后续真实接口会使用 Pydantic响应模型处理 ORM对象，避免在每个路由中长期手工复制字段。

### Depends与普通函数调用的区别

普通调用：

```python
session = get_session()
```

只会得到生成器对象，还需要调用者自己推进生成器并负责关闭。

FastAPI依赖：

```python
session: Session = Depends(get_session)
```

由框架负责：

- 调用依赖；
- 获取yield值；
- 处理嵌套依赖；
- 在请求结束后执行清理；
- 将依赖错误纳入请求处理流程。

### 专业术语

- **依赖（dependency）**：完成当前操作所需的外部对象或能力。
- **依赖注入（dependency injection）**：由框架创建依赖并传给使用者。
- **依赖提供者（dependency provider）**：例如 `get_session()`。
- **请求作用域（request scope）**：资源生命周期覆盖一次HTTP请求。
- **资源清理（resource cleanup）**：请求结束后关闭Session并归还连接。
- **路径参数（path parameter）**：例如 URL中的 `task_id`。
- **HTTP异常转换**：把数据库或业务结果转换为合适的HTTP状态码。

### 易错点

1. 写 `Depends(get_session)`，不要写 `Depends(get_session())`。
2. Session由服务器注入，不是客户端请求参数。
3. 每个请求应获得独立Session，不要共享一个全局Session。
4. `task_id: int` 的格式错误由FastAPI在进入路由前返回422。
5. 查询得到 `None` 时应由HTTP层抛出404，而不是继续访问 `task.id`。
6. SQLAlchemy ORM对象默认没有dataclass的 `asdict()` 方法。
7. `get_session()` 负责关闭Session，不代表它会自动提交业务事务。

---

## SQLAlchemy ORM：Session 常用方法、参数与返回值

### 问题场景

使用公共 `SessionFactory` 查询任务时，需要补充：

```python
with SessionFactory() as session:
    # 查询id=1的TaskRecord
```

此时容易混淆 `get()`、`execute()`、`scalars()`、`scalar()`，以及 `add()`、`flush()`、`commit()`、`rollback()` 各自负责的阶段。

### 核心结论

`Session` 是 SQLAlchemy ORM 的主要工作入口。它通过 Engine取得数据库连接，在一个工作范围内查询并管理 ORM对象、跟踪对象变化、组织 SQL和控制事务。

常用方法可以分为五类：

```text
主键查询：get()
一般查询：execute()、scalars()、scalar()
对象变更：add()、add_all()、delete()
事务控制：flush()、commit()、rollback()
状态同步与资源管理：refresh()、expire()、close()
```

项目中根据主键查询任务的直接答案是：

```python
with SessionFactory() as session:
    task = session.get(TaskRecord, 1)

    if task is None:
        print("Task not found")
    else:
        print(task.title)
```

### Session、事务和对象的关系

Session内部维护一个**身份映射（identity map）**：同一个 Session中，同一个模型和主键通常只对应同一个 Python对象实例。

```python
task1 = session.get(TaskRecord, 1)
task2 = session.get(TaskRecord, 1)

print(task1 is task2)  # 通常为True
```

第一次查询可能访问数据库；第二次查询可能直接复用 Session中已经存在的对象。

Session还实现**工作单元（Unit of Work）**模式：先在内存中收集新增、修改和删除，等到 `flush()` 或 `commit()` 时统一转换成 SQL。

---

### `session.get()`：按照主键查询一个对象

常用形式：

```python
session.get(ModelClass, primary_key)
```

项目示例：

```python
task = session.get(TaskRecord, 1)
```

主要参数：

| 参数 | 作用 | 当前项目示例 |
| --- | --- | --- |
| `entity` | 要查询的 ORM模型类 | `TaskRecord` |
| `ident` | 主键值 | `1` |
| `options` | 可选的关系加载策略 | `[selectinload(TaskRecord.tags)]` |
| `populate_existing` | 是否强制用数据库结果刷新已有对象 | `True` 或默认 `False` |

返回值：

```text
找到    → TaskRecord对象
未找到  → None
```

使用加载选项：

```python
task = session.get(
    TaskRecord,
    1,
    options=[selectinload(TaskRecord.tags)],
)
```

联合主键可以传元组或字典，但当前 `tasks` 只有单个主键 `id`，直接传整数即可。

适用场景：已知主键，只查询一条对象。非主键条件应使用 `select()`。

#### 身份映射命中不等于重新查询数据库

Session以“模型类型+主键”识别已经管理的对象。get在通常情况下先检查身份映射：存在可直接使用、未过期的对象时可以直接返回；不存在或需要重新加载时才查询数据库。因此get返回对象不能单独证明本次发出了SELECT。对象是否仍被引用、是否过期，以及populate_existing等选项也会影响行为，不应把Session理解为永久保存所有查询结果的缓存。

```python
task = TaskRecord(title="任务A")  # 只构造Python对象
session.add(task)               # 登记待插入对象，通常尚未执行INSERT
session.flush()                 # 执行INSERT，数据库生成主键，但没有commit
task_id = task.id
found = session.get(TaskRecord, task_id)
assert found is task           # 当前对象仍被引用且未过期，可以直接复用
```

假设task_id为101，可理解为Session记住“TaskRecord+101→task”。后面的get可能直接沿此对应关系返回task，无需新的SELECT。flush发送的是插入/更新等操作，get可能发送的是查询，两种SQL不能混为一谈。

导入回滚测试在第二条模拟失败前使用`session.get(TaskRecord, created_ids[0]) is not None`，只能说明当前Session能够取得第一条任务对象，不是独立的“确实查询到数据库行”证据。第一条INSERT已经发送的依据是：original_create调用真实TaskService.create_task，后者调用TaskRepository.add_task，其中明确执行session.add和session.flush并成功返回。INSERT发生在当前事务内，不代表commit；随后异常仍能使其回滚。若需要确认是否执行查询，应观察SQL日志或采用明确的重读/数据库检查，不单靠get返回非None推断。

---

### `session.execute()`：执行语句并保留完整行结构

常用形式：

```python
session.execute(statement, params=None)
```

主要参数：

| 参数 | 作用 |
| --- | --- |
| `statement` | SQLAlchemy语句对象，例如 `select(...)` 或 `text(...)` |
| `params` | 可选的参数字典或参数集合 |

返回值通常是 `Result`，其中每一项保持查询行结构。

查询多个字段：

```python
statement = select(TaskRecord.id, TaskRecord.title)
result = session.execute(statement)
rows = result.all()

for row in rows:
    print(row.id, row.title)
```

使用文本 SQL参数：

```python
statement = text(
    "SELECT id, title FROM tasks WHERE id = :task_id"
)

result = session.execute(
    statement,
    {"task_id": 1},
)
```

适用场景：需要每行中的多个字段、多个 ORM实体或完整 `Row` 对象。

---

### `Row`、`RowMapping`与`mappings()`

查询多个字段时：

```python
statement = select(
    TaskRecord.id,
    TaskRecord.priority,
)

row = session.execute(statement).first()
```

这里的`row`是SQLAlchemy的`Row`对象，表现得类似命名元组，不是普通字典。可以使用三种方式读取：

```python
row[0]                         # 按位置读取id
row[1]                         # 按位置读取priority
row.priority                   # 按属性名读取
row._mapping["priority"]       # 通过映射视图读取
```

在SQLAlchemy 2.x中，不应把普通`Row`直接当作字典并依赖：

```python
row["priority"]
```

如果希望直接使用字符串键读取，应先调用`mappings()`：

```python
row = session.execute(statement).mappings().first()

print(row["id"])
print(row["priority"])
```

`mappings()`是`Result`上的结果适配方法。它不会改变SQL、不会重新查询数据库，也不负责定义ORM类与表的映射；它只把后续每一行从`Row`形式呈现为`RowMapping`形式：

```text
Result[Row]
    ↓ mappings()
MappingResult[RowMapping]
```

`RowMapping`支持类似只读字典的接口：

```python
row["priority"]
row.keys()
row.values()
row.items()
```

它不等于可随意修改的普通`dict`。需要普通字典时可以转换：

```python
task_dict = dict(row)
```

不调用`mappings()`时，也可以从普通`Row`取得映射视图：

```python
row = session.execute(statement).first()
priority = row._mapping["priority"]
```

因此两种写法的关系是：

```python
# 先取得Row，再访问它的映射视图
row = session.execute(statement).first()
priority = row._mapping["priority"]

# 让结果直接产生RowMapping
row = session.execute(statement).mappings().first()
priority = row["priority"]
```

`mappings()`之后仍需决定取得多少行：

```python
result.mappings().all()          # 全部行
result.mappings().first()        # 第一行或None
result.mappings().one()          # 必须恰好一行
result.mappings().one_or_none()  # 零行或一行
```

如果字段可能重名，应使用`label()`提供明确的结果键：

```python
statement = select(
    TaskRecord.id.label("task_id"),
    TagRecord.id.label("tag_id"),
)

row = session.execute(statement).mappings().first()

print(row["task_id"])
print(row["tag_id"])
```

查询完整ORM实体时，通常不需要`mappings()`：

```python
task = session.scalars(
    select(TaskRecord)
).first()

print(task.priority)
```

如果对`select(TaskRecord)`使用`mappings()`，每行更接近：

```python
{"TaskRecord": TaskRecord对象}
```

它不会自动展开成`id`、`title`等字段字典，因为查询项是一个完整的ORM实体。

常用选择规则：

| 目标 | 推荐写法 |
| --- | --- |
| 完整ORM对象 | `session.scalars(statement).all()` |
| 多个字段，按位置或属性读取 | `session.execute(statement).all()` |
| 多个字段，按字符串键读取 | `session.execute(statement).mappings().all()` |
| 单个统计值或第一列的一个结果 | `session.scalar(statement)` |

查询结果通常是向前消费的。执行`result.mappings().all()`后，不要再期待同一个`result`能够重新返回相同内容；需要反复处理时，先把`.all()`的结果保存到变量中。

---

### `session.scalars()`：执行语句并提取每行第一个结果元素

常用形式：

```python
session.scalars(statement, params=None)
```

返回 `ScalarResult`，它是一个可遍历的结果容器，不是单个对象，也不是立即生成的普通列表。

选择一个 ORM模型：

```python
statement = select(TaskRecord)
result = session.scalars(statement)
tasks = result.all()
```

每行逻辑结构原本是：

```text
(TaskRecord对象,)
```

`scalars()` 提取后得到：

```text
TaskRecord对象
```

常见后续方法：

| 方法 | 返回行为 |
| --- | --- |
| `.all()` | 返回全部结果；没有结果时是空序列 |
| `.first()` | 返回第一个结果；没有结果时返回 `None` |
| `.one()` | 必须恰好一个；0个或多个都会抛异常 |
| `.one_or_none()` | 允许0个或1个；多个会抛异常 |

注意：

```python
select(TaskRecord.id, TaskRecord.title)
```

如果交给 `scalars()`，只保留每行第一个结果元素 `id`，不会同时返回 `title`。需要多个结果元素时使用 `execute()`。

---

### `session.scalar()`：直接取得第一行的第一个结果元素

常用形式：

```python
session.scalar(statement, params=None)
```

它适合只需要一个标量值或一个对象的场景。

统计任务数：

```python
statement = select(func.count(TaskRecord.id))
task_count = session.scalar(statement)
```

按条件查询一个对象：

```python
statement = select(TaskRecord).where(TaskRecord.id == 1)
task = session.scalar(statement)
```

返回行为：

```text
有结果  → 第一行的第一个结果元素
无结果  → None
```

`scalar()` 不负责确认查询结果是否恰好一行。如果业务要求“必须恰好一个”，可使用：

```python
task = session.scalars(statement).one()
```

#### 标签示例：单列值与整个ORM对象

假设tags有两行：(1, "python")、(2, "sql")。先按id排序以确定示例结果：

```python
names_query = select(TagRecord.name).order_by(TagRecord.id)
name = session.scalar(names_query)              # "python"
names = session.scalars(names_query).all()      # ["python", "sql"]

tags_query = select(TagRecord).order_by(TagRecord.id)
tag = session.scalar(tags_query)                # 第一条TagRecord对象
tags = session.scalars(tags_query).all()        # 两个TagRecord对象组成的列表
```

“第一个结果元素”由select选择的内容决定，不是固定取数据库第一列id。select(TagRecord.name)选择字符串值；select(TagRecord)选择整个模型对象，因此scalar可返回对象，scalars也可返回一组对象。scalars本身返回ScalarResult容器，不是列表，调用all后才收集结果；无匹配时all返回[]，scalar返回None。每行若选择多个结果项，scalar/scalars仅保留第一个结果项，需要完整行应使用execute。

导入回滚测试中的`session.scalar(select(TagRecord).where(TagRecord.name == tag_name)) is None`检查指定标签不存在；若存在，则返回一个TagRecord对象。scalar即使遇到多行也只取首行，不验证唯一性。要求“最多一行”时使用`session.scalars(statement).one_or_none()`：零行返回None，一行返回该项，多行抛MultipleResultsFound；它与要求恰好一行的one不同。

三者对比：

| 方法 | 返回重点 | 常见用途 |
| --- | --- | --- |
| `execute()` | 完整 `Row` | 多字段、多实体查询 |
| `scalars()` | 每行第一个元素组成的结果容器 | 多个 ORM对象或多个单值 |
| `scalar()` | 第一行的第一个元素 | COUNT或预期一个结果 |

---

### `session.add()`：把一个对象加入工作单元

常用形式：

```python
session.add(instance)
```

参数：

| 参数 | 作用 |
| --- | --- |
| `instance` | 要交给 Session管理的一个 ORM对象 |

返回值是 `None`。

```python
new_task = TaskRecord(
    title="学习Session",
    priority="normal",
)

session.add(new_task)
```

新对象从临时状态进入待保存状态；此时不保证已经执行 INSERT。不要写：

```python
new_task = session.add(new_task)  # 错误：new_task会变成None
```

从当前 Session查询出来的持久对象已经被 Session管理，修改属性时通常不需要再次 `add()`：

```python
task = session.get(TaskRecord, 1)
task.priority = "high"
session.commit()
```

---

### `session.add_all()`：一次加入多个对象

常用形式：

```python
session.add_all(instances)
```

参数 `instances` 是 ORM对象集合：

```python
session.add_all(
    [
        TaskRecord(title="任务A"),
        TaskRecord(title="任务B"),
    ]
)
```

返回值是 `None`。它只是批量加入当前工作单元，最终仍需 `flush()` 或 `commit()`。

---

### `session.delete()`：把一个持久对象标记为待删除

常用形式：

```python
session.delete(instance)
```

参数 `instance` 是要删除的 ORM对象，返回值是 `None`。

```python
task = session.get(TaskRecord, 5)

if task is not None:
    session.delete(task)
    session.commit()
```

`delete()` 通常不会立刻执行 DELETE。它先标记对象，下一次 `flush()` 或 `commit()` 时才执行 SQL。

关系对象的删除还会受到 ORM cascade和数据库 `ON DELETE CASCADE` 配置影响，需要结合关系映射单独判断。

---

### `session.flush()`：把内存变化同步到当前数据库事务

常用形式：

```python
session.flush()
```

通常不传参数，返回值是 `None`。

它会把待处理变化转换成 SQL：

```text
新增对象 → INSERT
修改属性 → UPDATE
删除对象 → DELETE
```

但 `flush()` 不会提交事务：

```python
session.add(new_task)
session.flush()

print(new_task.id)  # 通常已经得到数据库生成的ID

session.rollback()  # 仍然可以撤销INSERT
```

常见用途：

- 提交前需要获得自动生成的主键；
- 后续操作依赖前一步已经写入的结果；
- 希望提前触发数据库约束检查。

SQLAlchemy在执行某些查询之前可能自动 flush，这叫 **autoflush**。`commit()` 也会无条件先执行必要的 flush。

如果 flush因唯一约束、外键或非空约束失败，继续复用同一个 Session之前必须显式：

```python
session.rollback()
```

#### Repository写入为什么使用`add() + flush()`而不直接`commit()`

当前`TaskRepository.add_task()`接收一个已经构造好的`TaskRecord`，把它登记到当前Session并提前发送INSERT：

```python
def add_task(self, task: TaskRecord) -> TaskRecord:
    self.session.add(task)
    self.session.flush()
    return task
```

这个方法的参数和返回值分别是：

| 项目 | 含义 |
| --- | --- |
| `task`参数 | 上层已经构造好的`TaskRecord`对象 |
| 返回值 | 同一个`TaskRecord`对象；`flush()`后通常已有数据库生成的ID |

`Session.add()`返回`None`，因此Repository不能把它的返回值赋回`task`。`add_task()`显式返回业务对象，是Repository自身设计的接口，不是`Session.add()`的返回值。

Repository在这里不执行`commit()`，因为创建一项完整业务数据可能包含多个步骤：

```text
创建任务
    ↓
查询或创建标签
    ↓
建立任务与标签关联
    ↓
全部成功后提交事务
```

如果第一步立即提交，而后续标签操作失败，数据库可能留下部分完成的数据。当前职责边界是：

```text
Repository：执行数据库读写，并在需要ID或提前检查约束时flush
上层Service或请求事务边界：所有业务步骤成功后commit，失败时rollback
```

`flush()`会产生真实SQL和数据库约束错误，但仍不结束事务。可能出现的唯一约束、外键、非空约束等异常暂时继续向上抛出；Repository不把它们转换成`HTTPException`，因为HTTP状态码属于路由层。

Repository测试直接注入`database_session`，不经过TestClient：

```python
repository = TaskRepository(database_session)
task = TaskRecord(title="pytest Repository创建测试")

saved_task = repository.add_task(task)

assert saved_task is task
assert saved_task.id is not None
```

测试本身和Repository都不提交，最终由fixture控制的外层事务统一回滚。这既验证了`add_task()`能够得到ID，也保留了测试隔离。

#### 为什么创建调用`add_task()`，更新只返回原对象

`TaskService.create_task()`中的任务是刚构造的ORM对象：

```python
task = TaskRecord(
    title=title,
    priority=priority,
)
```

它最初处于临时状态（transient），尚未被Session管理，也没有数据库生成的ID。因此创建流程需要调用：

```python
return self.repository.add_task(task)
```

Repository内部通过`session.add(task)`将新对象加入工作单元，再通过`flush()`发送`INSERT`并取得ID。这里返回的是Repository显式返回的同一个`TaskRecord`，不是`Session.add()`的返回值。

`TaskService.update_task()`的对象来源不同：

```python
task = self.repository.get_by_id(task_id)
```

查询得到的`task`已经是当前Session管理的持久化对象（persistent）。直接修改属性时，SQLAlchemy会记录变化：

```python
task.title = cleaned_title
task.priority = cleaned_priority
task.tags = updated_tags
```

因此更新方法最后只需：

```python
return task
```

请求边界随后执行`session.commit()`，SQLAlchemy会先自动`flush()`，把已记录的变化转换为`UPDATE`和关系表操作，再提交事务。更新流程不需要再次调用`repository.add_task(task)`；虽然对当前Session中的持久对象重复调用`add()`通常不会插入第二行，但它没有必要，也会混淆“添加新任务”这一Repository方法的语义。

```text
创建：新对象（transient）→ add() → flush()执行INSERT → 返回带ID的对象
更新：查询对象（persistent）→ 修改属性 → commit()前自动flush执行UPDATE
```

| 场景 | 对象进入Service时的状态 | Service返回方式 | 最终持久化时机 |
| --- | --- | --- | --- |
| 创建任务 | 新对象尚未被Session管理 | `repository.add_task(task)` | Repository先`flush()`取得ID，Router最终`commit()` |
| 更新任务 | 查询所得对象已由Session管理 | `return task` | Router的`commit()`自动刷新修改 |

---

### `session.commit()`：提交当前事务

常用形式：

```python
session.commit()
```

没有常用参数，返回值是 `None`。

执行过程：

```text
先执行必要的flush
→ 向数据库发送COMMIT
→ 当前事务结束
```

```python
session.add(new_task)
session.commit()
```

成功提交后，普通 `rollback()` 不能撤销已经结束的事务。要恢复数据，需要在新事务中执行补偿操作。

SQLAlchemy默认会在 commit后让 Session内对象进入过期状态；下一次访问属性时可能重新查询数据库，以获得最新值。这个行为由 `expire_on_commit` 配置控制，后续接入 FastAPI响应时再具体处理。

---

### `session.rollback()`：回滚当前尚未提交的事务

常用形式：

```python
session.rollback()
```

没有常用参数，返回值是 `None`。

```python
task.priority = "high"
session.flush()
session.rollback()
```

它可以撤销当前事务中尚未提交的 INSERT、UPDATE和DELETE。它不能撤销之前已经成功 `commit()` 的事务。

发生数据库异常后的常见结构：

```python
try:
    # 修改ORM对象
    session.commit()
except Exception:
    session.rollback()
    raise
```

如果当前没有活动事务，调用 `rollback()` 通常安静结束。

---

### `session.refresh()`：立即从数据库重新读取一个对象

常用形式：

```python
session.refresh(instance, attribute_names=None)
```

主要参数：

| 参数 | 作用 |
| --- | --- |
| `instance` | 要刷新的 ORM对象 |
| `attribute_names` | 可选，只刷新指定属性名 |

刷新全部常规属性：

```python
session.refresh(task)
```

只刷新指定属性：

```python
session.refresh(task, ["title", "priority"])
```

`refresh()` 会立即执行查询，用数据库当前值覆盖对象中对应属性的值。它不是提交方法，也不能替代 `commit()`。

它的返回值是 `None`，作用体现在传入的 ORM 对象本身。传入对象应当是当前 Session 管理的持久化对象；对象尚未持久化、已被删除或不再处于可刷新状态时，可能抛出 SQLAlchemy 异常。

当前完成任务接口中的典型顺序是：

```python
completed_task.done = True
session.commit()
session.refresh(completed_task)

return completed_task
```

执行过程可以理解为：

```text
修改Python对象
→ commit()先flush并执行UPDATE，再提交事务
→ refresh()立即执行SELECT
→ 用数据库提交后的值更新同一个ORM对象
→ FastAPI序列化该对象
```

这里的 `done=True` 是应用代码直接设置的，因此在没有数据库触发器或其他数据库端修改时，通常不刷新也能得到预期值。显式调用 `refresh()` 的意义是明确保证后续使用的是数据库提交后的状态。数据库自动生成字段、默认值或触发器可能修改数据时，这一点更有价值。

`refresh()` 默认主要刷新对象自身的列属性，例如任务的 `id`、`title`、`done` 和 `priority`。它不等同于重新执行带 `selectinload()` 的查询，也不应被理解为自动重新预加载全部关系属性；需要明确刷新或预加载 `tags` 等关联关系时，应使用相应的关系加载方式。

与默认的 `expire_on_commit=True` 对比：`commit()` 后对象属性通常会被标记为过期，之后访问时可能按需重新查询；`refresh()` 则是在代码指定的位置立即查询，使重新加载的时机更明确。

---

### `session.expire()` 与 `expire_all()`：标记对象数据需要重新加载

标记一个对象：

```python
session.expire(task)
```

只标记指定属性：

```python
session.expire(task, ["title"])
```

标记 Session中的全部对象：

```python
session.expire_all()
```

`expire()` 通常不会立刻查询；下一次访问过期属性时才重新加载。对比：

expire_all无参数，返回None；它使Session所管理对象已加载的状态过期，对象本身仍在，不删除行或提交事务。例：task.done原为False，赋值True只先改变内存；flush将更新发送到数据库事务，随后expire_all标记状态需要重读，下一次访问task.done按需查询并得到事务内的值。因此导入测试先调用含最终flush的导入函数，再expire_all并重查，避免只检查内存赋值。过期会丢弃尚未flush的相关属性修改，所以不能随意在flush之前执行；重新读到更新也不代表已提交，当前事务仍可回滚。

```text
refresh() → 立即查询数据库
expire()  → 标记过期，下次访问时再查询
```

---

### `session.close()`：结束Session并释放资源

常用形式：

```python
session.close()
```

它会释放 Session持有的连接和事务资源，并清理 Session管理的对象状态。存在尚未结束的事务时，关闭过程会撤销该事务。

优先使用上下文管理器：

```python
with SessionFactory() as session:
    task = session.get(TaskRecord, 1)
```

离开 `with` 时自动关闭，相当于确保调用 `close()`。但关闭 Session不会自动提交写操作：需要保存时仍要显式调用 `commit()`。

---

### `session.begin()`：建立自动提交或回滚的事务块

基本形式：

```python
with session.begin():
    session.add(new_task)
```

行为：

```text
代码块正常结束 → commit
代码块抛出异常 → rollback
```

如果使用 `sessionmaker`，还可以把创建 Session和事务边界合并：

```python
with SessionFactory.begin() as session:
    session.add(new_task)
```

当前项目先继续使用显式 `commit()` 和 `rollback()`，便于学习事务边界；之后组织 Service事务时再选择合适形式。

---

### 常用属性：查看Session正在跟踪的变化

以下是属性，不是方法：

```python
session.new
session.dirty
session.deleted
```

含义：

| 属性 | 内容 |
| --- | --- |
| `session.new` | 已加入但尚未持久化的新对象 |
| `session.dirty` | 属性发生变化、可能需要UPDATE的对象 |
| `session.deleted` | 已标记为待删除的对象 |

它们主要用于调试和理解 Session状态，业务代码通常不需要手工操作这些集合。

### 当前项目的选择指南

| 需求 | 推荐方法 |
| --- | --- |
| 已知任务主键，查询一个任务 | `session.get(TaskRecord, task_id)` |
| 按优先级、完成状态等条件查询多个任务 | `session.scalars(select(...)).all()` |
| 查询多个指定字段或多个实体 | `session.execute(select(...)).all()` |
| 查询任务总数 | `session.scalar(select(func.count(...)))` |
| 新增一个任务 | `session.add(task)` 后 `commit()` |
| 新增多个任务 | `session.add_all(tasks)` 后 `commit()` |
| 修改任务 | 修改对象属性后 `commit()` |
| 删除任务 | `session.delete(task)` 后 `commit()` |
| 提交前获得数据库生成的ID | `session.flush()` |
| 撤销当前未提交操作 | `session.rollback()` |
| 立即重新读取数据库值 | `session.refresh(task)` |
| 确保资源释放 | `with SessionFactory() as session` |

### 易错点

1. `session.add()`、`add_all()`、`delete()`、`flush()`、`commit()` 和 `rollback()` 都不返回业务对象，不要用返回值覆盖原变量。
2. `flush()` 已执行 SQL但尚未提交；`commit()` 才结束并提交当前事务。
3. `rollback()` 只能撤销当前未提交事务，不能撤销已经成功 commit的事务。
4. `scalars()` 返回结果容器；要取得全部对象还需 `.all()`。
5. `scalar()` 只取得第一行的第一个元素，不验证是否存在多行。
6. 多字段查询通常使用 `execute()`，否则 `scalars()`只保留每行第一个结果元素。
7. 从当前 Session查询出的持久对象，修改属性时通常无需再次 `add()`。
8. flush失败后如果还要复用同一个 Session，必须先显式 `rollback()`。
9. `with SessionFactory() as session` 保证关闭Session，不代表自动提交写操作。
10. SQLAlchemy 2.x新代码优先使用 `select()` 配合 `execute()`、`scalars()`，不把旧式 `session.query()` 作为当前项目主写法。

## FastAPI响应模型与ORM对象转换

### Pydantic与SQLAlchemy分别负责什么

二者都可能用Python类描述“任务”，但所处边界不同：

| 工具 | 身份与主要职责 | 当前项目中的典型对象 |
| --- | --- | --- |
| SQLAlchemy | Python数据库工具库和ORM；负责映射Python对象与数据库表、构造和执行数据库操作、管理Session与事务 | `TaskRecord`、`TagRecord`、`Session` |
| Pydantic | 数据验证与序列化库；负责检查请求和响应的数据结构、类型及业务约束，并把数据整理为适合API输出的形式 | `TaskCreate`、`TaskUpdate`、`TaskResponse` |

ORM（对象关系映射，Object-Relational Mapping）让一条数据库记录在Python中表现为对象。例如，`TaskRecord`类对应`tasks`表，一个`TaskRecord`实例对应其中一行；`session.add()`、`select()`和`session.get()`等操作由SQLAlchemy转换成数据库操作。

Pydantic模型不负责把数据写入数据库。它声明接口允许接收或返回哪些字段，并在运行时完成验证和序列化。例如，`TaskCreate`约束客户端可以提交什么，`TaskResponse`约束服务器可以向客户端返回什么。

当前创建接口的数据链可以概括为：

```text
客户端JSON
    ↓ FastAPI交给Pydantic
TaskCreate：验证和整理请求数据
    ↓ 路由调用Service与Repository
TaskRecord：SQLAlchemy ORM对象，参与数据库写入
    ↓ 路由返回对象，FastAPI按照response_model处理
TaskResponse：Pydantic验证响应字段并完成序列化
    ↓
客户端收到JSON
```

路由直接`return new_task`时，`new_task`在服务器内部仍是`TaskRecord`对象。转换不是由Python编译器完成，而是FastAPI在运行时根据`response_model=TaskResponse`调用Pydantic：Pydantic在启用`from_attributes=True`后按字段名读取`new_task.id`、`new_task.title`等属性，验证并序列化响应。客户端最终收到的是JSON，不是Python中的`TaskResponse`实例。

### 为什么需要`response_model`

Python函数能够直接返回字典或列表，但这只说明数据可以被转换成JSON，并不能保证返回结构符合接口约定。FastAPI路由中的`response_model`用于声明和检查响应结构：

```python
@app.get(
    "/database/tasks",
    response_model=list[DatabaseTaskResponse],
)
def get_database_tasks(...):
    ...
```

这里的含义是：接口必须返回一个列表，列表中的每一项都必须符合`DatabaseTaskResponse`。FastAPI会在发送响应前让Pydantic完成验证和序列化，并根据该模型生成OpenAPI文档。

响应模型可以检查：

- 必需字段是否存在；
- 字段值能否满足声明的类型；
- 列表中的每个元素是否符合模型；
- 最终响应应当暴露哪些字段。

当前实验把`priority`误写成`int`时，数据库查询本身正常，但实际值`"high"`和`"normal"`无法解析为整数，因此FastAPI抛出`ResponseValidationError`。这说明响应验证发生在路由函数取得返回值之后、HTTP响应发送之前。

```text
查询数据库
    ↓
路由函数组织返回值
    ↓
response_model验证并序列化
    ↓
发送JSON响应
```

### `ConfigDict(from_attributes=True)`的作用

普通Pydantic模型通常从字典中读取字段：

```python
{"id": 1, "title": "学习PostgreSQL"}
```

SQLAlchemy查询得到的是ORM对象，数据通过属性访问：

```python
task.id
task.title
```

配置：

```python
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
```

表示Pydantic验证对象时，可以从`task.id`、`task.title`这样的对象属性中读取模型字段。它不会改变数据库表，也不会把ORM模型变成Pydantic模型，只决定Pydantic如何取得待验证的数据。

`model_config`是Pydantic识别的模型级配置，不是客户端需要提供的数据字段。`ConfigDict(from_attributes=True)`创建并返回一份配置，其中`from_attributes`表示允许从`对象.属性`读取数据；模型仍然会按照字段声明继续执行类型验证。

### `model_validate()`：启动完整模型验证

```python
response = TaskResponse.model_validate(task)
```

`model_validate()`是`BaseModel`提供的类方法。它接收一个字典或对象，读取全部所需字段、执行Pydantic标准类型验证和已经注册的自定义验证器，成功后返回一个新的`TaskResponse`实例；验证失败则抛出`ValidationError`。传入ORM对象时，`from_attributes=True`使它能够读取`task.id`、`task.tags`等属性。

在导入模型测试中的同一调用形式为：

```python
data = {"id": 3, "title": " 学习导入 "}
validated_task = LegacyTaskInput.model_validate(data)
assert validated_task.title == "学习导入"
```

`LegacyTaskInput`决定采用哪一套规则；`.model_validate`是类方法，括号里的data是传给它的第一个参数，即待验证数据。本次无需设置其他可选参数，严格程度沿用字段配置。输入data仍是字典，使用data["title"]访问；返回validated_task是模型实例，使用validated_task.title访问，不是HTTP Response，无需response.json()。不要将整个字典作为一个位置参数写成LegacyTaskInput(data)来代替该调用；模型直接构造通常接收字段关键字参数。调用本身不读取文件或写数据库。

#### `Model(**data)`与`Model.model_validate(data)`的区别

对于当前LegacyTaskInput模型，当data是键名为字符串的普通字段字典时，两种写法都可以创建模型并执行字段校验、默认值补充和自定义验证器：

```python
data = {"id": 1, "title": "任务"}
task_a = LegacyTaskInput(**data)
task_b = LegacyTaskInput.model_validate(data)
```

`**data`是Python的关键字参数展开，第一行构造相当于`LegacyTaskInput(id=1, title="任务")`；model_validate则把整个data作为一个参数交给Pydantic。不能笼统地说构造方式不会校验，或者不能使用`**data`。

读取不可信JSON时，顶层是列表不代表每个元素都是字典。例如`[{"id": 1, "title": "任务"}, 123]`中，第二项数字不能进行关键字参数展开。`LegacyTaskInput(**123)`会先在Python调用阶段抛TypeError，尚未进入模型校验；`LegacyTaskInput.model_validate(123)`则由Pydantic检查输入并抛ValidationError。即使输入是字典，关键字参数展开也要求键为字符串。

本次读取函数因此选择`LegacyTaskInput.model_validate(item)`，使“元素本身不是合法模型输入”和“字段内容不合法”都通过Pydantic的ValidationError处理。它返回校验后的LegacyTaskInput实例，不会把源字典原地变成模型，也不会写数据库。`results.append(LegacyTaskInput.model_validate(item))`表示先校验当前项，成功后才把模型实例加入结果列表；失败时异常传播，本次append不会执行。

它与`field_validator()`职责不同：

```text
model_validate()   → 发起一次完整验证并创建模型实例
field_validator()  → 注册某个字段在验证过程中的自定义处理规则
```

装饰器写法：

```python
@field_validator("tags", mode="before")
@classmethod
def convert_tags(cls, tags):
    ...
```

概念上相当于先把函数转换为类方法，再交给`field_validator(...)`登记：

```python
convert_tags = classmethod(convert_tags)
convert_tags = field_validator("tags", mode="before")(convert_tags)
```

这一步只登记规则，不会立刻验证数据，也不会创建`TaskResponse`。以后调用`TaskResponse.model_validate(...)`、直接构造`TaskResponse(...)`，或者FastAPI按照`response_model=TaskResponse`处理返回值时，Pydantic才会在完整验证流程中调用该验证器。

### ORM模型与API响应模型的职责

| 模型 | 主要职责 |
| --- | --- |
| SQLAlchemy ORM模型 | 表名、列、主键、外键、关联关系以及数据库读写 |
| Pydantic响应模型 | 客户端可以看到的字段、字段类型、响应验证和OpenAPI描述 |

两种模型都可能描述任务，但用途不同。数据库中的内部字段不一定需要返回给客户端；API中的计算字段也不一定直接对应一列数据库字段。

### 为什么当前标签不能只靠`from_attributes`直接转换

`TaskRecord.tags`的实际类型是：

```python
list[TagRecord]
```

现有API希望输出：

```python
list[str]
```

`from_attributes=True`可以读取`task.tags`，但不会自行猜测要从每个`TagRecord`中提取`name`。因此当前接口仍需要显式转换：

```python
"tags": [tag.name for tag in task.tags]
```

转换后的字典再交给响应模型检查。后续可以把这种转换集中到专用的响应转换逻辑中，但不能因为启用了`from_attributes`就认为任意不同的数据结构都能自动匹配。

### 当前项目中的类型对应

```python
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool
    priority: str
    tags: list[str]
```

其中`priority`在数据库和API中都是`"high"`、`"normal"`等文本，因此应声明为`str`；声明为`int`会被响应验证拒绝。

### 使用`field_validator()`转换单个响应字段

当ORM属性的数据形状与API字段不同，可以在Pydantic验证字段之前先进行转换。例如，ORM中的标签是`list[TagRecord]`，API需要`list[str]`：

```python
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool
    priority: str
    tags: list[str]

    @field_validator("tags", mode="before")
    @classmethod
    def convert_tags(cls, tags):
        return [
            tag if isinstance(tag, str) else tag.name
            for tag in tags
        ]
```

正式`/tasks`接口使用`task_routes.py`中的`TaskResponse`；迁移期间保留的演示接口使用`database_api_demo.py`中的`DatabaseTaskResponse`。它们是两个独立模型，各自的方法不会互相生效。讲解或修改时应先确认当前路由实际引用的是哪个响应模型。

装饰器必须位于类的内部，并紧贴被装饰的`convert_tags()`方法。把它们放到`class TaskResponse`上方会改为装饰整个类，使Pydantic模型不再是FastAPI期望的正常模型类型。

`mode="before"`表示先接收原始的`list[TagRecord]`并运行转换，再按照`tags: list[str]`进行类型验证：

```text
list[TagRecord]
    ↓ field_validator(mode="before")
list[str]
    ↓ Pydantic字段验证
合格的响应字段
```

`isinstance(tag, str)`判断当前元素是否为字符串，返回`True`或`False`，不会修改数据：

```python
tag if isinstance(tag, str) else tag.name
```

- 元素已经是`str`时，直接保留`tag`；
- 元素是`TagRecord`时，读取`tag.name`；
- 最终把`list[str]`和`list[TagRecord]`统一转换为响应模型要求的`list[str]`。

条件表达式只执行被选中的分支，所以字符串元素不会再访问不存在的业务属性`tag.name`。这里仍然假定非字符串元素具有`name`属性；如果传入整数等其他对象，代码仍会抛出`AttributeError`。`isinstance()`通常比`type(tag) == str`更合适，因为它也认可`str`的子类。

### 一个验证器绑定多个字段

```python
@field_validator("title", "priority", mode="before")
@classmethod
def strip_text(cls, value):
    if isinstance(value, str):
        return value.strip()
    return value
```

Pydantic会在验证`title`和`priority`时分别调用一次该方法。`value`接收的是当前字段的实际值，不是字符串`"title"`或`"priority"`。例如输入标题和优先级时，执行过程可理解为：

```python
strip_text(TaskResponse, title的原始值)
strip_text(TaskResponse, priority的原始值)
```

每次返回值只进入当次对应字段的后续验证。如果确实需要知道当前处理的字段名，可以增加`ValidationInfo`参数并读取`info.field_name`。

### `self`、`cls`与静态方法

普通实例方法：

```python
def method(self, value):
    ...
```

调用`object.method(value)`时，Python自动把当前对象作为第一个参数`self`传入。它用于读取或修改具体对象的数据，例如`self.title`。

类方法：

```python
@classmethod
def method(cls, value):
    ...
```

调用`SomeClass.method(value)`时，Python自动把类本身作为第一个参数`cls`传入。它可以读取类级别的信息，或者创建该类的对象。Pydantic字段验证器按类方法形式声明，因此第一个参数写`cls`。

静态方法：

```python
@staticmethod
def method(value):
    ...
```

它既不自动接收实例，也不自动接收类，只是放在类命名空间中的普通函数。

如果一个类方法没有使用`cls`，PyCharm可能从普通Python代码角度建议把它改为静态方法。但框架装饰器可能要求特定调用协议；Pydantic的`field_validator`继续使用官方推荐的`@classmethod`结构，不按该通用建议改成静态方法。

如果`@classmethod`错误地放在类上方，而方法本身没有被它装饰，PyCharm就会把方法识别成普通实例方法，并提示第一个参数应该命名为`self`。这不是要求把验证器参数改成`self`，而是在提示装饰器位置不正确。

## 可变默认值与`default_factory`

### 为什么`tags`不能只声明类型

```python
tags: list[str]
```

这表示`tags`是必填字段。客户端没有提交`tags`时，Pydantic会认为请求缺少字段并返回`422`。

当前业务允许创建没有标签的任务，所以使用：

```python
tags: list[str] = Field(default_factory=list)
```

这表示客户端可以省略`tags`；省略时，Pydantic为当前模型对象生成空列表`[]`。

### 什么是可变对象

列表可以在原对象上被修改，因此属于可变对象：

```python
tags = []
tags.append("python")

print(tags)
# ["python"]
```

如果两个变量指向同一个列表，通过其中一个变量修改列表，另一个变量也会看到变化：

```python
shared_tags = []
task_a_tags = shared_tags
task_b_tags = shared_tags

task_a_tags.append("python")

print(task_b_tags)
# ["python"]

print(task_a_tags is task_b_tags)
# True
```

这里没有两个列表，只有一个列表和多个指向它的变量。

### 普通Python函数的可变默认参数问题

下面的默认列表在函数定义时只创建一次：

```python
def create_task(title, tags=[]):
    tags.append(title)
    return tags
```

连续调用时会重复使用同一个默认列表：

```python
print(create_task("任务A"))
# ["任务A"]

print(create_task("任务B"))
# ["任务A", "任务B"]
```

普通函数通常改为使用`None`：

```python
def create_task(title, tags=None):
    if tags is None:
        tags = []

    tags.append(title)
    return tags
```

这样每次省略`tags`时都会在函数内部创建一个新列表。

### `default_factory=list`的执行过程

`default_factory`保存的是创建默认值的方法：

```python
default_factory=list
```

这里使用`list`，而不是`list()`：

```python
list    # 可以在以后被调用的列表类型
list()  # 现在立刻创建出的空列表
```

Pydantic创建模型对象时，内部行为可以近似理解为：

```python
if 客户端没有提供tags:
    tags = list()
```

每创建一个模型对象，都会重新调用一次`list()`：

```python
task_a = DatabaseTaskCreate(title="任务A")
task_b = DatabaseTaskCreate(title="任务B")

task_a.tags.append("python")

print(task_a.tags)
# ["python"]

print(task_b.tags)
# []

print(task_a.tags is task_b.tags)
# False
```

两个任务因此拥有彼此独立的标签列表。

同样的写法也适用于其他可变容器：

```python
names: list[str] = Field(default_factory=list)
settings: dict[str, str] = Field(default_factory=dict)
selected_ids: set[int] = Field(default_factory=set)
```

### Pydantic中的补充说明

现代Pydantic通常也会复制直接声明的不可哈希可变默认值，因此以下写法通常不会让不同模型实例共享同一个列表：

```python
tags: list[str] = []
```

当前项目仍使用`Field(default_factory=list)`，因为它能更明确地表达设计意图：每个模型实例需要在创建时获得自己的新列表。这种写法也与`dataclass`等常见Python数据模型处理可变默认值的方式一致。

可以把`default_factory`理解为：

```text
不提前保存一个默认对象
→ 保存创建默认对象的方法
→ 每次需要默认值时重新创建
```

## SQLAlchemy对象状态与`autoflush`警告

### 本次警告的现象

创建带标签的任务时曾出现：

```text
SAWarning: Object of type <TaskRecord> not in session,
add operation along 'TagRecord.tasks' won't proceed
```

接口最终仍然创建成功，但该警告说明SQLAlchemy在某次同步过程中发现了一个关联对象尚未加入Session。能得到正确结果不代表执行顺序合理，不能把`SAWarning`一律当作无关提示。

### ORM对象的三个基础状态

创建对象后：

```python
new_task = TaskRecord(title="学习事务", priority="high")
```

此时它是临时状态（transient）：只是普通Python对象，Session尚不知道它的存在。

执行：

```python
session.add(new_task)
```

对象进入待持久化状态（pending）：已经被Session管理，等待执行`INSERT`。

SQL执行并成功持久化后，对象进入持久状态（persistent）：它对应数据库中的一行，并继续由当前Session管理。

```text
创建ORM对象
    ↓ transient
session.add()
    ↓ pending
flush或commit成功
    ↓ persistent
```

### `autoflush`是什么

刷新（flush）表示把Session中待处理的变化转换成SQL并发送给数据库，但此时事务不一定已经提交。SQLAlchemy在执行查询前，可能自动进行一次刷新，这叫自动刷新（autoflush）。

常见触发场景：

```python
session.scalar(select(...))
session.execute(select(...))
session.commit()
```

查询前自动刷新是为了让紧接着的查询能够看到当前事务刚刚产生的变化。

### 为什么原来的顺序触发警告

原来的核心顺序是：

```python
new_task = TaskRecord(...)

for tag_name in cleaned_tags:
    tag_record = session.scalar(select(...))
    new_task.tags.append(tag_record)

session.add(new_task)
```

第一次`append()`已经在内存中建立了任务和标签关系，但`new_task`仍处于transient状态。下一轮`session.scalar()`触发autoflush时，SQLAlchemy从已受Session管理的`TagRecord`一侧看到了`new_task`，却发现它不在Session中，因此发出警告。

### 数据库演示接口采用的修正顺序

创建任务后立即加入Session，再查询和建立关系：

```python
new_task = TaskRecord(
    title=task_data.title,
    priority=task_data.priority,
)

session.add(new_task)

for tag_name in cleaned_tags:
    tag_record = session.scalar(
        select(TagRecord).where(TagRecord.name == tag_name)
    )

    if tag_record is None:
        tag_record = TagRecord(name=tag_name)

    new_task.tags.append(tag_record)

session.commit()
```

此时即使查询触发autoflush，`new_task`也已经处于pending状态，SQLAlchemy能够统一跟踪任务、标签和中间表关联。

autoflush可能提前发送`INSERT`，但不等于提前提交事务。只要尚未成功`commit()`，同一事务仍可以在失败时回滚。

### Service迁移中采用的另一种修正方式

迁移到`TaskService`后，任务由Repository在最后统一加入Session。若在逐个查询标签的同时立即执行：

```python
task.tags.append(tag_record)
```

就会再次形成“受Session管理的已有标签关联了transient任务”的状态。下一次`get_tag_by_name()`执行查询并触发autoflush时，会出现相同警告。

本次没有为了压制警告使用`no_autoflush`，而是调整对象关系的建立时机：先完成所有标签查询和对象创建，再一次性关联任务。

```python
task_tags: list[TagRecord] = []

for tag_name in cleaned_tags:
    tag_record = repository.get_tag_by_name(tag_name)

    if tag_record is None:
        tag_record = TagRecord(name=tag_name)

    task_tags.append(tag_record)

task.tags = task_tags
return repository.add_task(task)
```

这里需要区分两个列表：

```text
cleaned_tags → list[str]，保存规范化后的标签名称
task_tags    → list[TagRecord]，保存准备建立关系的ORM对象
```

新的执行顺序是：

```text
清理并去重标签名称
    ↓
完成所有TagRecord查询或构造
    ↓
一次性设置task.tags
    ↓
Repository执行add与flush
```

查询期间还没有建立“持久标签→临时任务”的反向关系，因此autoflush不会遇到无法纳入工作单元的`TaskRecord`。最终`Repository.add_task()`将完整对象图加入Session，关系级联可以统一处理任务、标签和关联表。

验收时可以把`SAWarning`临时提升为异常，而不是只观察输出中是否碰巧没有warning：

```python
import warnings
from sqlalchemy.exc import SAWarning

warnings.simplefilter("error", SAWarning)
```

这样只要相同警告再次出现，验收程序就会立即失败。警告消失后仍需运行完整回归测试，并检查外层测试事务是否回滚。

## 使用`Literal`限制请求字段的固定取值

### `str`只能限制类型，不能限制具体内容

下面的声明：

```python
priority: str
```

只表示`priority`必须是字符串。`"low"`、`"high"`和`"urgent"`都属于字符串，因此Pydantic不会仅凭`str`判断其中哪个符合业务规则。

同样，下面的更新逻辑只判断客户端是否提交了字段，然后进行赋值，并不包含合法性检查：

```python
if "priority" in update_data:
    task.priority = update_data["priority"]
```

### `Literal`表示只能使用列出的固定值

```python
from typing import Literal

Priority = Literal["low", "normal", "high"]
```

`Priority`不是运行时生成的新类，而是一个类型约束，表示值只能是三个字符串字面值之一。创建和更新模型可以共享它：

```python
class DatabaseTaskCreate(BaseModel):
    priority: Priority = "normal"


class DatabaseTaskUpdate(BaseModel):
    priority: Priority | None = None
```

合法请求会进入路由：

```json
{"priority": "high"}
```

非法请求会在路由函数执行前被Pydantic拒绝并返回`422`：

```json
{"priority": "urgent"}
```

因为验证发生在赋值和`commit()`之前，非法值不会写入数据库。`Literal`默认区分大小写；当前接口要求客户端提交小写值。

### 创建和更新必须使用同一条规则

如果只限制更新模型，创建接口仍可能写入非法优先级；如果只限制创建模型，已有任务又可能被更新成非法值。因此两种请求模型都使用同一个`Priority`类型，避免规则分叉。

### 输入校验、业务校验和数据库约束的分工

| 层级 | 主要职责 | 当前例子 |
| --- | --- | --- |
| Pydantic请求模型 | 尽早拒绝非法HTTP输入 | `Literal["low", "normal", "high"]` |
| Service业务层 | 保证从HTTP之外调用业务操作时规则仍成立 | 原`TaskManager`中的优先级校验 |
| PostgreSQL约束 | 阻止任何程序写入非法数据 | 后续可增加`CHECK`约束 |

Pydantic校验不能代替数据库的最终完整性保护，数据库约束也不能代替友好的HTTP输入错误。当前数据库演示接口直接操作ORM，没有调用原来的Service，所以必须在数据库版请求模型中明确输入规则。后续学习Alembic时，再通过迁移为已有表增加数据库级`CHECK`约束。

## SQLAlchemy动态过滤与PostgreSQL关键词匹配

### 一个查询对象逐步追加条件

列表接口的过滤条件取决于客户端实际提交的查询参数。先建立基础查询，再按需追加条件：

```python
statement = select(TaskRecord).options(
    selectinload(TaskRecord.tags)
)

if priority is not None:
    statement = statement.where(
        TaskRecord.priority == priority
    )

if done is not None:
    statement = statement.where(
        TaskRecord.done == done
    )
```

`where()`返回新的`Select`对象，所以要把结果重新赋给`statement`。不要在每个分支中重新执行`select(TaskRecord)`，否则之前追加的条件可能丢失。

多个独立的`where()`默认组合为SQL的`AND`：

```sql
WHERE priority = 'high' AND done = false
```

所有条件拼接完成后再统一排序和执行：

```python
statement = statement.order_by(TaskRecord.id.asc())
tasks = session.scalars(statement).all()
```

这样每次请求只执行最终需要的任务查询，而不会先查询全部任务再重复查询。

### 为什么布尔查询参数要判断`is not None`

可选布尔参数存在三种业务状态：

```text
None  → 客户端没有提交，不按done筛选
True  → 只查询已完成任务
False → 只查询未完成任务
```

如果写成`if done:`，客户端明确提交的`false`会因为真假值为假而被跳过。正确写法是：

```python
if done is not None:
    statement = statement.where(TaskRecord.done == done)
```

### `ILIKE`与包含匹配

PostgreSQL的`ILIKE`用于不区分大小写的文本匹配。SQLAlchemy写法：

```python
TaskRecord.title.ilike(f"%{cleaned_keyword}%")
```

大致对应：

```sql
WHERE title ILIKE '%postgres%'
```

通配符的位置决定匹配方式：

```text
postgres%   → 以postgres开头
%postgres   → 以postgres结尾
%postgres%  → 任意位置包含postgres
```

`ILIKE`本身已经忽略英文大小写，因此先调用`lower()`不是当前查询的必要条件。SQLAlchemy会把构造出的匹配字符串作为绑定参数传给数据库，这与把客户端内容直接拼入完整SQL语句不同。

### 关键词清理和空输入

```python
cleaned_keyword = keyword.strip()

if not cleaned_keyword:
    raise HTTPException(
        status_code=400,
        detail="Keyword cannot be empty",
    )
```

`strip()`只删除首尾空白字符，不会删除文本内部空格或普通符号。未提供`keyword`时值为`None`，不增加条件；提交空字符串或纯空白时，清理后为空并返回`400`。

### 当前查询数量

使用`selectinload(TaskRecord.tags)`时：

- 查询得到任务：通常先查询任务，再批量查询这些任务的标签，共2条主要`SELECT`；
- 查询没有任务：没有任务ID需要加载标签，只执行任务查询，共1条主要`SELECT`。

这仍然避免了逐个任务查询标签造成的N+1问题。

## 使用关系`any()`过滤多对多关联

### 任务、标签和关联表

当前关系结构：

```text
tasks.id
    ↓ task_tags.task_id
task_tags.tag_id
    ↓ tags.id
tags.name
```

ORM通过`TaskRecord.tags`把中间表封装成任务的标签集合。查询“至少存在一个名称为python的关联标签”的任务时，可以写：

```python
statement = statement.where(
    TaskRecord.tags.any(
        TagRecord.name == cleaned_tag
    )
)
```

`any()`表达的是：当前任务关联的标签集合中，是否至少有一个元素满足括号内的条件。数据库通常会把它转换成通过`task_tags`和`tags`检查关联记录的`EXISTS`条件。

### 为什么这里使用`any()`

当前查询的返回主体仍然是`TaskRecord`，只需要根据关联标签判断任务是否入选。使用关系`any()`可以直接表达该意图，也不会因为一个任务拥有多个标签而产生重复任务行。

手工`JOIN`同样可以完成关联过滤，但通常还要考虑重复行、连接条件和去重。需要同时返回多张表字段或进行复杂聚合时，再根据查询目标选择显式`JOIN`。

### 过滤条件和关联加载是两件事

```text
TaskRecord.tags.any(...)       → 决定哪些任务入选
selectinload(TaskRecord.tags)  → 加载入选任务的全部标签
```

一个任务拥有`python`和`database`两个标签时，`tag=python`会让该任务入选；响应仍返回两个标签，因为API返回的是任务完整信息，而不是只返回参与匹配的标签。

### 标签查询参数的规范化

当前项目保存标签时统一清理首尾空白并转成小写，所以查询参数使用同一规则：

```python
cleaned_tag = tag.strip().lower()
```

随后必须检查清理后的变量：

```python
if not cleaned_tag:
    raise HTTPException(
        status_code=400,
        detail="Tag cannot be empty",
    )
```

不能在清理后继续检查原始`tag`。例如原始值`"   "`是真值，但`cleaned_tag`已经是空字符串；检查原始变量会让纯空格绕过校验，最终被当作不存在的标签查询并错误返回`200 []`。

### 与其他过滤条件组合

标签条件继续追加到同一个`statement`，会与优先级、完成状态和关键词形成`AND`：

```text
priority条件
AND done条件
AND title关键词条件
AND 关联标签存在条件
```

无匹配任务时只执行任务查询；有匹配任务时，`selectinload`再批量查询这些任务的全部标签。

## Pydantic部分更新：`model_dump(exclude_unset=True)`

### `model_dump()`的作用

FastAPI把请求体解析为Pydantic模型对象后，字段通常通过属性访问：

```python
task_update.title
task_update.priority
task_update.tags
```

调用：

```python
task_update.model_dump()
```

会把模型转换成Python字典。例如：

```python
{
    "title": "学习数据库",
    "priority": None,
    "tags": None,
}
```

`model_dump()`返回的是Python的`dict`，不是JSON字符串。需要JSON字符串时使用`model_dump_json()`。

### `exclude_unset=True`的含义

`unset`表示客户端没有设置、没有提交该字段：

```python
update_data = task_update.model_dump(exclude_unset=True)
```

这段代码表示：转换成字典时，只保留客户端在本次请求中明确提交过的字段。

假设请求模型是：

```python
class DatabaseTaskUpdate(BaseModel):
    title: str | None = None
    priority: str | None = None
    tags: list[str] | None = None
```

客户端只提交：

```json
{
  "title": "学习数据库"
}
```

执行`model_dump(exclude_unset=True)`后得到：

```python
{
    "title": "学习数据库"
}
```

`priority`和`tags`没有变成特殊值，而是根本不存在于`update_data`中：

```python
"title" in update_data     # True
"priority" in update_data  # False
"tags" in update_data      # False
```

这使PATCH接口能够只修改客户端明确提交的字段，并保留其他数据库字段的原值。

### 省略字段、`null`和空列表的区别

#### 客户端省略字段

请求：

```json
{
  "priority": "high"
}
```

结果：

```python
{
    "priority": "high"
}
```

`title`和`tags`不在字典中，因此保持原值。

#### 客户端明确提交`null`

请求：

```json
{
  "title": null
}
```

结果：

```python
{
    "title": None
}
```

虽然值是`None`，但客户端明确提交了该字段，所以`exclude_unset=True`仍然会保留它。当前项目使用额外的业务检查拒绝`null`：

```python
for field_name, value in update_data.items():
    if value is None:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} cannot be null",
        )
```

#### 客户端明确提交空列表

请求：

```json
{
  "tags": []
}
```

结果：

```python
{
    "tags": []
}
```

空列表既不是“没有提交”，也不是`None`。在当前业务中，它表示客户端明确要求清空任务标签。

因此应判断键是否存在：

```python
if "tags" in update_data:
    task.tags.clear()
```

不要写成：

```python
if update_data.get("tags"):
    ...
```

因为空列表的真假值是`False`，这种写法会错误地跳过清空操作。

### 与`exclude_none=True`的区别

`exclude_unset=True`排除客户端没有提交的字段；客户端明确提交的`null`仍会保留为`None`。

`exclude_none=True`排除所有值为`None`的字段，不关心客户端有没有明确提交。

对于请求：

```json
{
  "title": null
}
```

两者结果不同：

```python
task_update.model_dump(exclude_unset=True)
# {"title": None}

task_update.model_dump(exclude_none=True)
# {}
```

当前项目要求客户端明确提交`null`时返回错误。如果使用`exclude_none=True`，程序就无法区分“客户端没有提交title”和“客户端明确提交title=null”。因此部分更新采用`exclude_unset=True`。

### 当前项目中的完整流程

```python
update_data = task_update.model_dump(exclude_unset=True)

for field_name, value in update_data.items():
    if value is None:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} cannot be null",
        )

if "title" in update_data:
    task.title = update_data["title"]

if "priority" in update_data:
    task.priority = update_data["priority"]

if "tags" in update_data:
    # []表示清空标签；非空列表表示替换标签
    ...
```

可以概括为：

```text
没有提交字段 → 不进入update_data，保留数据库原值
提交普通值   → 进入update_data，执行更新
提交[]       → 进入update_data，执行清空操作
提交null     → 进入update_data，再由业务代码拒绝
```

`exclude_unset=True`判断的是客户端有没有提交字段，而不是字段值是否为空。

### 不直接改写传入的`update_data`

字典是可变对象。函数接收字典参数时，参数和调用者的变量通常指向同一个字典，而不是自动得到一份副本：

```python
def normalize_update(update_data: dict):
    update_data["priority"] = update_data["priority"].strip().lower()


data = {"priority": " HIGH "}
normalize_update(data)

print(data)
# {"priority": "high"}
```

函数内部的修改同时改变了调用者持有的`data`。这种除了返回值之外还改变外部状态的行为叫作副作用（side effect）。业务函数更新`task`是预期效果，但顺便改写调用者传入的原始请求数据通常没有必要，可能带来以下问题：

- 调用者无法继续使用原始输入做日志、审计或比较；
- 从函数调用形式上不容易看出参数会被改写；
- 多个步骤或测试复用同一个字典时可能互相影响；
- 校验中途抛出异常时，输入数据可能已经被修改了一部分。

字段较少时，优先把清理后的值保存在局部变量中：

```python
if "priority" in update_data:
    priority = update_data["priority"].strip().lower()

    if priority not in {"low", "normal", "high"}:
        raise ValueError("Invalid priority")

    task.priority = priority
```

这样`update_data`保留原始输入，`priority`保存规范化结果，合法值最终赋给需要更新的ORM对象。

### 用浅复制保存完整的规范化数据

如果字段较多，并且校验、更新或日志等后续步骤都需要使用一整份规范化数据，可以先创建新字典：

```python
normalized_data = update_data.copy()

normalized_data["title"] = normalized_data["title"].strip()
normalized_data["priority"] = (
    normalized_data["priority"].strip().lower()
)
```

`dict.copy()`执行浅复制（shallow copy）：创建新的外层字典，但不会递归复制字典内部的所有对象。

```python
update_data is normalized_data
# False：不是同一个字典对象

update_data == normalized_data
# 刚复制完成时为True：两个字典内容相等
```

对于字符串、整数、布尔值和`None`等不可变对象，浅复制通常已经足够。给新字典的键赋新值，只会改变新字典：

```python
normalized_data["priority"] = "high"
```

常见的字典浅复制写法包括：

```python
copy_data = original.copy()
copy_data = dict(original)
copy_data = {**original}
```

三种写法都会创建新的外层字典，其中`copy()`最直接地表达“复制当前字典”的意图。

### 浅复制不会隔离嵌套的可变对象

如果字典中包含列表、字典或集合，浅复制后的两个外层字典仍然会引用同一个嵌套对象：

```python
original = {
    "title": "学习数据库",
    "tags": ["python", "database"],
}
copy_data = original.copy()

original is copy_data
# False

original["tags"] is copy_data["tags"]
# True
```

因此，原地修改共享的标签列表会同时影响两个字典：

```python
copy_data["tags"].append("pytest")

print(original["tags"])
# ["python", "database", "pytest"]
```

但给新字典的`tags`键赋一个新列表不会影响原字典：

```python
copy_data["tags"] = [
    tag.strip().lower()
    for tag in copy_data["tags"]
]
```

列表推导式创建了新列表，随后只有`copy_data["tags"]`改为引用它。当前项目可以采用这种组合：

```python
normalized_data = update_data.copy()

if "title" in normalized_data:
    normalized_data["title"] = normalized_data["title"].strip()

if "priority" in normalized_data:
    normalized_data["priority"] = (
        normalized_data["priority"].strip().lower()
    )

if "tags" in normalized_data:
    normalized_data["tags"] = [
        tag.strip().lower()
        for tag in normalized_data["tags"]
    ]
```

这段代码通过浅复制隔离外层字典，并通过创建新列表隔离嵌套的`tags`。

### 深复制及其使用边界

深复制（deep copy）会递归复制嵌套对象：

```python
from copy import deepcopy

copy_data = deepcopy(original)

original["tags"] is copy_data["tags"]
# False
```

此时原地修改`copy_data["tags"]`不会影响`original["tags"]`。但深复制会创建更多对象，消耗更多时间和内存，某些数据库连接、文件句柄或框架对象也不适合随意深复制。不要因为数据存在嵌套就机械地使用`deepcopy()`。

当前项目的判断原则是：

```text
字段少，只使用一次             → 使用局部变量
需要完整的规范化字典           → 浅复制外层字典
浅复制后需要处理嵌套列表       → 创建新列表并重新赋值
确实需要隔离复杂的多层可变结构 → 再考虑deepcopy()
```

核心规则是：浅复制只隔离外层容器；其中嵌套的可变对象仍然共享。

## pytest 测试发现、测试函数与断言

安装 pytest 只是让项目具备测试工具，并不会在每次修改代码后自动执行测试。需要在终端运行 `python -m pytest`，或者在 PyCharm 中运行 pytest 配置，pytest 才会开始收集并执行测试。

### pytest 如何发现测试

pytest 默认分两层筛选测试：

```text
运行 pytest
    ↓
递归寻找 test_*.py 或 *_test.py 文件
    ↓
在这些文件中寻找 test_* 函数
    ↓
执行收集到的测试函数
```

因此，下面的文件和函数可以被默认发现：

```python
# tests/test_model.py

def test_task_title():
    ...
```

常见情况如下：

| 文件名 | 函数名 | 默认是否作为测试执行 |
| --- | --- | --- |
| `test_model.py` | `test_create_task()` | 是 |
| `model_test.py` | `test_create_task()` | 是 |
| `model.py` | `test_create_task()` | 否，文件名不符合默认规则 |
| `test_model.py` | `check_create_task()` | 否，函数名不符合默认规则 |

测试类也可以被发现：类名通常以 `Test` 开头，类中的测试方法仍以 `test_` 开头。当前阶段先使用顶层测试函数，避免一次增加过多结构。

### 名称以`test_`开头的可调用对象也可能被误收集

“pytest寻找`test_*`函数”是便于入门的简化说法。更准确地说，pytest会检查名称符合测试规则、并且可以被调用的对象。因此，辅助对象如果同时满足以下条件，也可能被误认为测试：

```text
名称以test_开头
+
对象是callable
```

例如：

```python
test_app = FastAPI()
```

`test_app`不是测试函数，而是保存路由和依赖覆盖的FastAPI应用实例。但FastAPI实现了`__call__`，所以：

```python
callable(test_app)
# True
```

FastAPI实例需要可调用，是因为ASGI服务器会用近似下面的形式调用应用：

```python
await app(scope, receive, send)
```

三个参数的含义是：

- `scope`：请求类型、路径、方法和请求头等连接信息；
- `receive`：接收请求数据的异步函数；
- `send`：发送响应数据的异步函数。

pytest看到`test_app`的名称和可调用特征后，可能把它加入测试收集，并把`scope`、`receive`、`send`误当成测试所需的fixture。项目没有这些fixture时，可能出现类似：

```text
fixture 'scope' not found
```

也可能因pytest或插件版本不同而表现为额外的收集警告或错误。这属于测试发现阶段的命名冲突，不代表FastAPI业务代码有错。

辅助应用应使用不会匹配测试命名规则的名称：

```python
demo_app = FastAPI()
```

然后让真正的测试函数保留`test_`前缀：

```python
def test_dependency_override(override_client):
    ...
```

这样职责清晰：

```text
demo_app                 → 测试使用的辅助FastAPI应用
test_dependency_override → pytest应当收集的测试函数
```

技术上可以设置`test_app.__test__ = False`阻止收集，但直接使用`demo_app`、`example_app`或`app`等清晰名称更容易维护。

### `assert`负责判断结果

pytest 负责发现并调用测试函数，`assert`负责判断实际结果是否符合预期：

```python
def test_tasks_have_independent_tag_lists():
    task_a = Task(id=1, title="任务A")
    task_b = Task(id=2, title="任务B")

    task_a.tags.append("python")

    assert task_a.tags == ["python"]
    assert task_b.tags == []
```

每条 `assert` 的条件为真时继续执行；条件为假时，该测试失败，pytest会显示失败位置、实际值和预期值。上面的第二条断言用于确认两个任务没有共享同一个默认标签列表。

### fixture 为什么不以 `test_` 开头

fixture 是测试的准备函数，不是一个独立测试，所以通常使用描述资源的名称，例如 `sample_task`：

```python
@pytest.fixture
def sample_task():
    return Task(id=1, title="学习 pytest")
```

它不会因为运行 pytest 就被当作独立测试执行。只有测试函数声明了同名参数时，pytest才会调用它并注入返回值。

## 依赖注入：pytest fixture 与 FastAPI Depends

依赖注入（Dependency Injection，简称 DI）是指：一个函数需要某个对象或资源时，不在函数内部自行创建，而是由外部准备好以后传入函数。

这里的“依赖”就是函数完成工作所需要的对象，例如任务对象、数据库会话或测试客户端。

### 不使用依赖注入

测试函数自己创建需要的任务对象：

```python
def test_task_title():
    task = Task(id=1, title="学习 pytest")
    assert task.title == "学习 pytest"
```

这种写法在测试较少时很直观，但多个测试需要相同准备过程时会产生重复代码。

### pytest fixture 的依赖注入

fixture 负责准备测试需要的数据或资源：

```python
import pytest


@pytest.fixture
def sample_task():
    return Task(id=1, title="学习 pytest")
```

测试函数只需声明一个与 fixture 同名的参数：

```python
def test_task_title(sample_task):
    assert sample_task.title == "学习 pytest"
```

pytest 的执行过程是：

```text
发现测试函数 test_task_title
        ↓
发现参数 sample_task
        ↓
找到同名 fixture
        ↓
调用 fixture 并取得返回值
        ↓
把返回值传给测试函数
        ↓
执行测试
```

测试函数不需要主动调用 `sample_task()`。pytest 根据测试函数的参数名找到对应 fixture，并把 fixture 的返回值注入该参数。

fixture 可以集中处理测试数据的创建、数据库连接、事务回滚和资源关闭，使测试函数只关注需要验证的行为。

### fixture 的默认 `function` 作用域

没有显式指定 `scope` 时，fixture 默认使用函数级作用域：

```python
@pytest.fixture
def sample_task():
    return Task(...)
```

等价于：

```python
@pytest.fixture(scope="function")
def sample_task():
    return Task(...)
```

每个需要 `sample_task` 的测试函数开始前，pytest都会重新执行一次fixture。因此，不同测试拿到不同的`Task`实例：

```text
测试A请求 sample_task → fixture创建实例A
测试B请求 sample_task → fixture创建实例B
```

一个测试修改实例A的标签，不会污染另一个测试拿到的实例B。这是测试隔离的基础。

在同一个测试执行期间，同一个fixture的结果会被缓存。如果一条依赖链多次请求同一个fixture，pytest通常复用该测试本次执行中已经创建的对象，而不会反复准备同一份资源。测试函数结束后，函数级fixture的这次使用周期也随之结束。

数据库测试会沿用相同思想：每个测试获得独立的会话和测试数据，并在测试结束后回滚或清理，防止测试之间相互影响。

### 与 FastAPI Depends 的联系

FastAPI 的 `Depends` 也属于依赖注入：

```python
def get_tasks(
    session: Session = Depends(get_session),
):
    ...
```

FastAPI 调用 `get_session()` 获得数据库会话，再把它传给接口函数的 `session` 参数。接口函数只负责使用会话，不负责决定会话如何创建。

两者的核心思想相同，但声明方式和执行者不同：

| 场景 | 声明方式 | 负责注入的框架 |
| --- | --- | --- |
| pytest | `def test_xxx(sample_task)` | pytest |
| FastAPI | `session = Depends(get_session)` | FastAPI |

依赖注入的主要价值包括减少重复准备代码、分离资源创建与业务使用、方便替换依赖，以及便于测试和清理资源。

## 使用 FastAPI `TestClient` 测试 HTTP 行为

`TestClient`让测试代码像客户端一样调用FastAPI应用，但不需要启动Uvicorn，也不需要监听真实网络端口：

```text
pytest测试函数
    ↓ client.get() / client.post()
TestClient
    ↓
FastAPI路由、参数校验、依赖和异常处理
    ↓
Response对象
```

它仍会经过应用的请求处理流程，因此可以验证状态码、JSON响应、请求校验和异常转换。

### 创建测试客户端

可以用fixture统一创建客户端：

```python
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    return TestClient(app)
```

测试函数声明`client`参数后，pytest会把`TestClient`实例注入测试函数：

```python
def test_unknown_route_returns_404(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
```

`response.status_code`是HTTP状态码，`response.json()`把JSON响应体解析为Python对象。

### 断言进行精确比较

字符串比较区分大小写、空格和标点：

```python
{"detail": "Not Found"}   # 实际结果
{"detail": "Not found."}  # 不相等：大小写和句号不同
```

测试失败时要先阅读pytest给出的“实际值”和“预期值”，再判断是业务实现错误，还是测试中的预期写错。不能为了让测试通过而直接修改实现或断言；应先根据接口约定确认哪一侧正确。

### `failed`、`passed`和`warning`需要分开判断

- `failed`：至少一个断言失败，或测试执行时抛出未处理异常。
- `passed`：测试范围内的断言全部成立。
- `warning`：依赖弃用、兼容性或潜在问题提示，本身不等于测试失败。

出现`1 passed, 1 warning`表示测试已经通过，但警告仍应单独查看和安排处理；出现`1 failed, 1 warning`时，失败原因和警告也可能是两个无关问题。

### 本项目处理过的两类pytest warning

第一类来自测试客户端依赖。当前Starlette的`TestClient`推荐使用`httpx2`；只安装旧的`httpx`仍能运行，但会发出弃用警告。项目显式安装并固定：

```text
httpx2==2.13.1
```

安装后数据库测试从`6 passed, 1 warning`变为`6 passed`。保留环境中已有的`httpx`，因为其他工具仍可能依赖它；不需要为解决该警告卸载其他包。

第二类来自pytest测试发现。模块顶层曾定义：

```python
test_app = FastAPI()
```

名称以`test_`开头，而FastAPI实例又是可调用对象，pytest尝试把它当作测试收集，产生`PytestCollectionWarning`。辅助对象不应使用测试函数命名规则，改为：

```python
demo_app = FastAPI()
```

即可消除误收集。最终完整套件结果为`15 passed`且没有warning。

### `TestClient(app)`具体创建了什么

项目中的`app`是FastAPI应用对象：

```python
app = FastAPI(title="Task Manager3.0")
```

它保存路由、请求模型、依赖和异常处理器等应用信息。`TestClient(app)`根据这个应用创建测试客户端：

```python
@pytest.fixture
def client():
    return TestClient(app)
```

正常运行时，请求要经过真实网络和Uvicorn：

```text
浏览器或requests → localhost端口 → Uvicorn → FastAPI app
```

使用`TestClient`时，请求在当前Python进程内交给应用：

```text
pytest → TestClient → FastAPI app
```

它没有启动真实服务器或占用端口，但仍会执行路由匹配、参数和请求体验证、依赖注入、接口函数、异常处理及响应转换。

测试函数中的`client`不是fixture函数本身，而是fixture返回的`TestClient`实例：

```text
pytest发现client参数
    ↓
调用同名fixture
    ↓
执行TestClient(app)
    ↓
将客户端实例注入测试函数
```

应用存在启动和关闭生命周期资源时，可以使用上下文管理器：

```python
@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
```

当前入门测试没有复杂生命周期资源，直接返回客户端已经足够。

### `get`、`post`、`patch`和`delete`

这些方法分别构造不同HTTP方法的请求，并统一返回`Response`响应对象：

| 方法 | 常见用途 | Task Manager示例 |
| --- | --- | --- |
| `get()` | 查询资源 | 查询任务列表或任务详情 |
| `post()` | 创建资源或提交操作 | 创建任务 |
| `patch()` | 部分更新资源 | 修改标题、优先级或标签 |
| `delete()` | 删除资源 | 删除指定任务 |

#### `get()`查询

```python
response = client.get("/tasks/2")
```

路径中的`2`会作为路径参数交给FastAPI。查询条件推荐通过`params`传递：

```python
response = client.get(
    "/tasks",
    params={
        "done": False,
        "priority": "high",
    },
)
```

它对应类似：

```text
/tasks?done=false&priority=high
```

GET通常用于读取，不应产生业务数据修改。

#### `post()`创建

```python
response = client.post(
    "/tasks",
    json={
        "title": "学习 pytest",
        "priority": "high",
        "tags": ["python"],
    },
)
```

`json=`会把Python对象编码为JSON请求体，并设置相应内容类型。不要把请求体与查询参数混淆：

```text
json=...   → JSON请求体
params=... → URL查询参数
```

创建成功常返回`201`。创建测试会执行实际写入逻辑，建立测试隔离之前，只测试会被请求模型提前拒绝的非法输入。

#### 创建响应的`201`与查询响应的`200`

`200 OK`和`201 Created`都表示请求成功，但表达的成功类型不同：

| 状态码 | 含义 | 当前项目中的典型场景 |
| --- | --- | --- |
| `200 OK` | 请求正常处理并返回结果 | 查询任务详情、更新或完成任务成功 |
| `201 Created` | 请求成功并创建了新资源 | 创建新任务成功 |

创建接口显式声明：

```python
@app.post(
    "/database/tasks",
    status_code=201,
)
```

因此创建请求应验证：

```python
response = client.post("/database/tasks", json={...})
assert response.status_code == 201
```

取得新任务ID后再查询详情：

```python
task_id = response.json()["id"]
detail_response = client.get(f"/database/tasks/{task_id}")

assert detail_response.status_code == 200
```

这两条断言分别验证两个接口约定：

```text
POST创建新任务 → 201 Created
GET读取已有任务 → 200 OK
```

HTTP方法本身不会强制决定状态码；最终状态码由接口实现声明。FastAPI路径操作没有指定其他成功状态码时通常默认返回`200`，而创建接口需要通过`status_code=201`明确表达资源已创建。

HTTP状态码不是为每个项目随意发明的数字。它们的基本含义由HTTP规范约定，接口设计者需要根据实际结果选择合适的标准状态码。项目可以自行设计具体错误信息和业务规则，但不能把`404 Not Found`重新解释成“创建成功”。

当前后端开发中常见的状态码包括：

| 状态码 | 标准含义 | 常见使用场景 |
| --- | --- | --- |
| `200 OK` | 请求成功 | 查询、返回正文的更新操作 |
| `201 Created` | 成功创建资源 | `POST /tasks`创建任务 |
| `204 No Content` | 成功且没有响应正文 | 删除成功且无需返回内容 |
| `400 Bad Request` | 请求不符合当前业务规则 | 空标签、业务层判断出的非法优先级 |
| `401 Unauthorized` | 尚未通过身份认证 | 未登录、Token无效 |
| `403 Forbidden` | 身份已确认但没有权限 | 普通用户访问管理员功能 |
| `404 Not Found` | 目标资源不存在 | 查询不存在的任务 |
| `409 Conflict` | 请求与资源当前状态冲突 | 唯一值冲突、并发版本冲突 |
| `422 Unprocessable Entity` | 请求结构或字段校验失败 | 缺字段、类型错误、Pydantic约束失败 |
| `500 Internal Server Error` | 服务端出现未处理异常 | 意外程序错误或未处理的数据库错误 |

服务器声明状态码与测试验证状态码属于同一个接口约定的两端：

```python
@task_router.post("", status_code=201)
def create_task(...):
    ...


response = client.post("/tasks", json={...})
assert response.status_code == 201
```

- 路由中的`status_code=201`规定服务器创建成功时返回的状态码。
- 测试中的断言验证服务器是否遵守该约定。

状态码使用标准含义，错误响应正文则可以结合项目自行设计：

```python
raise HTTPException(
    status_code=404,
    detail="Task not found",
)
```

其中`404`来自HTTP规范，`"Task not found"`是本项目给客户端的具体说明。对于边界相近的业务情况，设计者有时需要在多个标准状态码中作出选择，例如根据接口语义决定使用`400`还是`409`；这种选择需要保持一致并写入测试，而不是创造新的含义。

FastAPI还提供可读的状态码常量：

```python
from fastapi import status

@task_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_task(...):
    ...


assert response.status_code == status.HTTP_201_CREATED
```

`status.HTTP_201_CREATED`与整数`201`完全等价。常量的优势是名称直接表达含义，并减少记错数字的可能；当前项目继续直接使用`201`也没有问题。

#### `patch()`部分更新

```python
response = client.patch(
    "/tasks/2",
    json={"priority": "high"},
)
```

PATCH通常只修改显式提交的字段。省略`tags`表示保留原值，提交`"tags": []`则可表示明确清空标签。成功常返回`200`。有效更新会修改数据，因此也需要隔离。

#### `delete()`删除

```python
response = client.delete("/tasks/2")
```

成功响应由接口设计决定，常见形式有：

- `200`并返回删除结果；
- `204 No Content`且没有响应体；
- 目标不存在时返回`404`。

对于`204`响应，应检查：

```python
assert response.content == b""
```

不要调用`response.json()`解析不存在的JSON正文。

### 常用请求参数

| 参数 | 作用 | 示例 |
| --- | --- | --- |
| 路径 | 指定接口地址 | `client.get("/tasks/2")` |
| `params` | URL查询参数 | `params={"done": False}` |
| `json` | JSON请求体 | `json={"title": "任务"}` |
| `headers` | HTTP请求头 | `headers={"Authorization": "Bearer ..."}` |
| `cookies` | Cookie数据 | `cookies={"session_id": "..."}` |
| `data` | 表单数据 | `data={"username": "alice"}` |
| `files` | 文件上传 | `files={"file": (...)}` |
| `content` | 原始字符串或字节请求体 | `content=b"raw bytes"` |
| `follow_redirects` | 是否自动跟随重定向 | `follow_redirects=False` |

普通FastAPI JSON接口当前主要使用路径、`params`和`json`；其他参数在认证、表单、上传和重定向等实际需求出现时学习。

#### `json=`、`data=`和`content=`的区别

三者都可以携带请求体，但编码格式、`Content-Type`和适用接口不同：

| 参数 | 请求体格式 | 常见`Content-Type` | 适用场景 |
| --- | --- | --- | --- |
| `json=` | JSON | `application/json` | Pydantic `BaseModel`请求体 |
| `data=` | HTML表单编码 | `application/x-www-form-urlencoded` | FastAPI `Form()`参数 |
| `content=` | 原始字符串或字节 | 由调用者指定或推断 | 纯文本、XML、原始字节或异常格式测试 |

当前数据库创建接口接收Pydantic模型：

```python
def create_database_task(task_data: DatabaseTaskCreate):
    ...
```

因此应使用：

```python
response = database_client.post(
    "/database/tasks",
    json={
        "title": "测试任务",
        "priority": "high",
    },
)
```

`TestClient`会把Python字典编码为JSON，并自动设置：

```http
Content-Type: application/json
```

实际请求体类似：

```json
{
  "title": "测试任务",
  "priority": "high"
}
```

使用`data=`传入字典时，客户端通常把它编码成表单：

```python
response = client.post(
    "/login",
    data={
        "username": "alice",
        "password": "123456",
    },
)
```

请求体近似为：

```text
username=alice&password=123456
```

它适合服务端使用`Form()`接收的接口，不适合当前`DatabaseTaskCreate` JSON模型。把`data=`误用于JSON接口时，FastAPI可能因为媒体类型和请求体结构不符合要求而返回`422`。

需要区分两个表面相同的失败结果：

```python
json={}
```

表示发送了合法的空JSON对象，但缺少`title`等必填字段；而：

```python
data={}
```

表示发送空表单或空请求体，但接口要求JSON模型。两者都可能返回`422`，失败原因却不同。因此测试非法输入时不能只看状态码，还应检查`detail`中的错误类型或位置，确认真正验证了预期规则。

原始正文可以使用`content=`：

```python
response = client.post(
    "/raw",
    content=b"raw bytes",
    headers={"content-type": "application/octet-stream"},
)
```

当前阶段可以记为：

```text
Pydantic BaseModel请求体 → json=
FastAPI Form表单参数      → data=
原始文本或字节            → content=
```

### `Response`常用内容

#### 创建请求中的`response_a`是什么

```python
response_a = database_client.post(
    "/database/tasks",
    json={
        "title": "pytest标签过滤A",
        "tags": ["pytest-filter-python", "pytest-filter-database"],
    },
)
```

`response_a`接收的是HTTP响应对象`Response`，包含状态码、响应头和响应体。它不是任务字典，也不是JSON文本。

```python
response_a.status_code  # 201等HTTP状态码
response_a.headers      # 响应头
response_a.text         # 响应体的字符串形式
task_a = response_a.json()  # 解析JSON响应体，当前接口得到Python字典
task_id = task_a["id"]
```

请求中的`json={...}`接收Python字典并将其编码为JSON；响应上的`response_a.json()`反向解析JSON并返回Python对象。当前创建接口返回JSON对象，所以解析结果是字典；列表接口返回JSON数组，所以解析结果是列表。具体返回类型取决于响应体内容。

所有请求方法都会返回响应对象：

```python
response = client.get("/tasks")
```

常用属性和方法包括：

| 写法 | 含义 |
| --- | --- |
| `response.status_code` | HTTP状态码 |
| `response.json()` | 将JSON响应解析为Python对象 |
| `response.text` | 字符串形式的响应体 |
| `response.content` | 字节形式的响应体 |
| `response.headers` | 响应头 |
| `response.cookies` | 响应中的Cookie |
| `response.url` | 最终请求URL |

`json`是方法，必须写括号：

```python
response.json()
```

#### `response.json()`的返回值

`Response.json()`读取HTTP响应体中的JSON文本，将其解析为对应的Python对象并返回。它的方向是：

```text
JSON响应体 → Python对象
```

例如创建任务接口返回：

```json
{
  "id": 8,
  "title": "pytest更新删除测试",
  "done": false,
  "priority": "low",
  "tags": ["pytest-before-update"]
}
```

执行：

```python
created_task = create_response.json()
```

得到的是Python字典：

```python
{
    "id": 8,
    "title": "pytest更新删除测试",
    "done": False,
    "priority": "low",
    "tags": ["pytest-before-update"],
}
```

因此可以继续取得字段：

```python
task_id = created_task["id"]
title = created_task["title"]
```

`.json()`的返回类型取决于JSON最外层的数据类型，并不固定为字典：

| JSON响应体 | Python返回值类型 |
| --- | --- |
| `{"id": 1}` | `dict` |
| `[{"id": 1}, {"id": 2}]` | `list` |
| `"hello"` | `str` |
| `123` | `int` |
| `1.5` | `float` |
| `true` / `false` | `bool`，即`True` / `False` |
| `null` | `None` |

当前创建任务响应最外层是JSON object，所以`created_task`是字典，其字段类型分别为：

```text
id       → int
title    → str
done     → bool
priority → str
tags     → list[str]
```

#### 方法对象与方法调用

```python
create_response.json
```

取得的是方法本身，没有解析响应体；可能显示为类似：

```text
<bound method Response.json of <Response [201 Created]>>
```

```python
create_response.json()
```

才表示调用方法，并取得解析后的Python对象。

#### 与请求参数`json=`的方向区别

发送请求时：

```python
client.post(
    "/database/tasks",
    json={"title": "任务"},
)
```

其中`json=`负责把Python对象编码为JSON请求体：

```text
Python对象 → JSON请求体
```

读取响应时：

```python
response.json()
```

负责把JSON响应体解析为Python对象：

```text
JSON响应体 → Python对象
```

两者方向相反，不能把`response.json()`理解成“把Response对象转换成JSON”。

#### 响应体不是合法JSON时

如果服务器返回普通文本或损坏的JSON，调用`response.json()`会抛出JSON解码异常。排错时可以先查看：

```python
print(response.status_code)
print(response.text)
```

确认状态码和原始文本，再决定是否调用`response.json()`。FastAPI正常的JSON接口响应可以直接解析；`204 No Content`等没有响应体的情况则不应调用该方法。

#### `Session.get()`返回ORM对象，为什么`TestClient.get()`返回Response

判断一个方法返回什么，关键不在变量名，也不能只看方法都叫`get()`，而要先看点号左侧是什么对象：

| 调用 | 方法所属对象 | 返回值 |
| --- | --- | --- |
| `session.get(TaskRecord, task_id)` | SQLAlchemy `Session` | `TaskRecord`实例或`None` |
| `client.get("/database/tasks/1")` | FastAPI / Starlette `TestClient` | HTTP `Response`对象 |
| `some_dict.get("id")` | Python字典 | 对应的值或默认值 |

变量名不会改变对象类型：

```python
result = client.get("/tasks/1")
response = client.get("/tasks/1")
```

这两个变量都是`Response`。反过来，即使把数据库查询结果命名为`response`：

```python
response = session.get(TaskRecord, 1)
```

它仍然是`TaskRecord | None`。

`Session.get()`在服务器内部按主键查询数据库。SQLAlchemy把查询到的数据库行构造成ORM对象，因此可以直接访问：

```python
task = session.get(TaskRecord, 1)

if task is not None:
    print(task.id)
    print(task.title)
```

这里没有发生HTTP通信，所以不存在HTTP状态码、响应头和JSON响应体。它的参数、返回值和关系加载选项详见前文“`session.get()`：按照主键查询一个对象”。

`TestClient.get()`模拟的是服务器外部客户端发送HTTP请求。客户端收到完整HTTP响应，其中包含状态码、响应头和响应体，所以需要通过不同属性或方法分别读取：

```python
response = client.get("/database/tasks/1")

response.status_code
response.headers
response.text
task_data = response.json()
```

`response.json()`只负责把JSON响应体解析成Python对象；它不会把服务器内部的ORM对象原样取回。当前项目中一条详情请求的数据转换链是：

```text
PostgreSQL数据库行
    ↓ SQLAlchemy映射
TaskRecord ORM对象
    ↓ Repository和路由函数返回
Pydantic响应模型验证、序列化
    ↓ FastAPI生成HTTP响应
JSON响应体
    ↓ TestClient接收
Response对象
    ↓ response.json()
Python字典
```

因此可以记住三条边界：

```text
Session.get()    → 服务器内部的ORM对象或None
TestClient.get() → 客户端收到的HTTP Response
Response.json()  → 从响应体解析出的Python数据
```

#### 测试中为什么有时通过Session修改任务，而不是调用详情路由

通过详情路由能够读取任务，但取得的是HTTP响应，而不是Session正在管理的ORM对象：

```python
detail_response = task_client.get(f"/tasks/{task_id}")
task_data = detail_response.json()
```

`task_data`是由JSON响应体解析出来的普通字典。修改它只会改变测试进程中的字典，不会更新数据库：

```python
task_data["done"] = True  # 不会产生UPDATE
```

如果测试需要准备“数据库中该任务已经完成”的状态，可以通过与API共享同一测试事务的`database_session`取得ORM对象：

```python
saved_task = database_session.get(TaskRecord, task_id)
assert saved_task is not None

saved_task.done = True
database_session.flush()
```

`saved_task`是当前Session管理的`TaskRecord`。属性变化会被SQLAlchemy跟踪，`flush()`将其转换为测试事务内的`UPDATE`，所以后续统计接口能够查询到新状态。fixture结束后，外层事务仍会统一回滚。

这里的直接Session修改属于**测试数据准备（test setup）**，不代表真实客户端可以绕过API修改数据库。选择方式取决于被测试的目标：

| 当前测试目标 | 合适的准备方式 |
| --- | --- |
| 只测试统计接口，但正式完成接口尚未迁移到数据库 | 使用`database_session.get()`修改状态 |
| 测试任务详情读取 | 使用`task_client.get("/tasks/{task_id}")`并检查响应 |
| 正式完成接口已经迁移，需要验证完整用户工作流 | 使用`task_client.patch("/tasks/{task_id}/complete")` |

当前迁移阶段，旧完成接口仍操作JSON文件，无法改变PostgreSQL中的正式测试任务。因此统计接口测试暂时使用Session准备完成状态。完成接口迁移后，应优先补充或改为通过PATCH接口完成任务，从HTTP边界验证完整工作流。

### FastAPI正式列表请求的完整执行链

首先区分请求的发出者和接收者。测试代码中的：

```python
response = task_client.get(
    "/tasks",
    params={"done": False},
)
```

是`TestClient`模拟客户端发出HTTP GET请求，FastAPI应用负责接收和处理；不是FastAPI主动发出`.get()`请求。`task_client.get()`返回HTTP `Response`，其正文再通过`response.json()`解析为Python数据。

当前正式列表接口的完整调用链是：

```text
pytest测试函数
    ↓ TestClient发送GET /tasks
FastAPI匹配路由
    ↓ 解析查询参数、执行依赖注入
Router：get_tasks()
    ↓ 创建Repository和Service，转换业务异常
Service：规范化并校验业务参数
    ↓ 传递合法参数
Repository：构造并执行SQL
    ↓
PostgreSQL返回数据库行
    ↓ SQLAlchemy映射
list[TaskRecord]
    ↓ Service和Router逐层返回
Pydantic按照list[TaskResponse]验证并序列化
    ↓
FastAPI生成HTTP响应
    ↓
TestClient取得Response，pytest执行断言
```

#### 正常请求如何逐层处理

例如客户端提交：

```python
response = task_client.get(
    "/tasks",
    params={
        "priority": " HIGH ",
        "done": False,
        "keyword": " ALPHA ",
        "tag": " PYTEST-ROUTE-FILTER-X ",
    },
)
```

HTTP查询参数本质上来自文本。FastAPI先根据路由函数的类型标注进行解析：字符串参数保持字符串，`done=false`被转换成Python的`False`。它还会处理：

```python
session: Session = Depends(get_session)
```

正常运行时由`get_session`提供请求专属Session；测试中则由`dependency_overrides`改为提供位于外层测试事务中的`database_session`。完成类型解析和依赖注入后，FastAPI才调用路由函数，其效果近似：

```python
get_tasks(
    priority=" HIGH ",
    done=False,
    keyword=" ALPHA ",
    tag=" PYTEST-ROUTE-FILTER-X ",
    session=database_session,
)
```

Router只组织HTTP请求处理：使用Session创建Repository和Service，调用Service，并将业务异常转换成HTTP错误。Service执行`strip().lower()`和业务校验，得到：

```python
priority == "high"
done is False
keyword == "alpha"
tag == "pytest-route-filter-x"
```

Repository接收这些合法参数，逐项追加SQL条件。连续调用`where()`形成AND关系，查询含义近似：

```sql
WHERE priority = 'high'
  AND done = false
  AND title ILIKE '%alpha%'
  AND EXISTS (符合名称条件的关联标签)
ORDER BY id ASC
```

查询结果是`list[TaskRecord]`。Router可以直接返回ORM对象列表，因为路由声明了：

```python
response_model=list[TaskResponse]
```

Pydantic通过`from_attributes=True`读取ORM属性，并由`tags`字段的前置验证器把`list[TagRecord]`转换成`list[str]`。FastAPI最终返回`200 OK`和JSON数组。

#### 业务规则非法：进入Service后返回400

例如：

```python
task_client.get(
    "/tasks",
    params={"priority": "urgent"},
)
```

`"urgent"`能够正常解析为字符串，因此FastAPI会调用路由。Service发现它不属于`low`、`normal`、`high`，抛出普通Python异常：

```python
raise ValueError(
    "Priority must be low, normal, or high"
)
```

Router捕获该异常并转换为HTTP语义：

```python
raise HTTPException(
    status_code=400,
    detail=str(error),
)
```

此时Repository尚未被调用，也不会执行SQL。空白`keyword`和空白`tag`走相同链路：

```text
FastAPI类型解析成功
→ Router被调用
→ Service业务校验失败
→ ValueError
→ Router转换为HTTPException
→ FastAPI返回400
```

#### 类型无法解析：调用路由前直接返回422

例如路由参数声明为：

```python
done: bool | None = None
```

客户端却提交：

```python
params={"done": "not-a-bool"}
```

FastAPI无法把该文本解析为`bool`，因此在调用`get_tasks()`之前生成`422 Unprocessable Entity`。Router函数体、Service和Repository都不会执行，也不会访问数据库：

```text
TestClient发送请求
→ FastAPI匹配路由
→ done类型解析失败
→ get_tasks()未调用
→ FastAPI默认异常处理器返回422
```

这与业务层的400不同：400表示数据类型已经能被程序接收，但违反当前项目规则；422表示请求在框架边界就无法构造成路由函数需要的参数。更完整的Pydantic错误正文结构见后文“读取Pydantic校验错误的位置”和“为什么代码中找不到显式的422”。

#### 服务器内部异常与响应验证异常

如果参数合法，但数据库连接或SQL执行失败，异常发生在Repository或数据库阶段。当前列表Router只捕获`ValueError`，数据库异常不会被误转换成400；若没有更上层的专门异常处理器，通常表现为服务器内部错误`500`。

如果查询成功，但Router返回的数据不符合`response_model`，Pydantic会在HTTP响应发出前触发响应验证异常。例如模型要求`title: str`，返回对象却缺少title。这也是服务器没有兑现响应结构约定，通常属于500，而不是客户端输入错误。

#### 测试结束后的清理链路

正式接口测试结束后，pytest按依赖关系逆序清理fixture：

```text
测试函数结束
→ task_client清除FastAPI dependency_overrides
→ database_session关闭Session
→ 回滚外层事务
→ 关闭数据库Connection
```

测试Session使用`join_transaction_mode="create_savepoint"`。即使正式创建接口内部执行`session.commit()`，它仍处于测试外层事务的控制范围内；fixture最终回滚外层事务，避免测试数据残留。详细事务原理见前文数据库测试隔离章节。

可以用三个关卡整理整条链路：

| 关卡 | 主要职责 | 典型失败 |
| --- | --- | --- |
| FastAPI请求边界 | 路由匹配、类型解析、请求模型校验、依赖注入 | 404、422、依赖创建失败 |
| 业务与数据访问 | Service业务规则、Repository查询、数据库执行 | 400、数据库异常/通常500 |
| 响应输出 | Pydantic响应验证与序列化、生成HTTP响应 | 响应验证异常/通常500 |

当前列表接口几种结果可对照为：

| 情况 | 是否进入Router | 是否进入Service | 是否执行数据库查询 | 典型状态码 |
| --- | ---: | ---: | ---: | ---: |
| 合法筛选 | 是 | 是 | 是 | 200 |
| 非法priority、空白keyword/tag | 是 | 是 | 否 | 400 |
| `done=not-a-bool` | 否 | 否 | 否 | 422 |
| 数据库执行失败 | 是 | 是 | 尝试执行并失败 | 通常500 |
| 返回值不符合`response_model` | 是 | 是 | 可能已经执行 | 通常500 |

### 读取Pydantic校验错误的位置

非法请求体的响应大致如下：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": "   "
    }
  ]
}
```

表达式：

```python
response.json()["detail"][0]["loc"][-1]
```

可以逐层拆解为：

```python
response_data = response.json()       # 整个响应字典
errors = response_data["detail"]      # 错误列表
first_error = errors[0]               # 第一条错误
location = first_error["loc"]         # 错误位置路径
last_location = location[-1]          # 路径最后一项
```

对于`["body", "title"]`，最后一项是`"title"`。但`[-1]`只表示取列表末项，并不保证永远得到title：

- `['body', 'priority']`末项是`priority`；
- `['body', 'task', 'title']`末项是`title`；
- `['body', 'tags', 1]`末项是列表索引`1`。

`loc`通常从请求来源逐步指向具体错误位置。当前测试只制造title错误，因此可以预期路径为：

```python
assert response.json()["detail"][0]["loc"] == [
    "body",
    "title",
]
```

检查完整路径比只检查`[-1]`表达得更严格。如果可能同时产生多条错误，`[0]`只检查第一条，测试还需要考虑错误顺序或遍历错误列表。

### 为什么代码中找不到显式的`422`

FastAPI接口使用Pydantic请求模型时，请求数据会在接口函数执行前完成解析和校验：

```python
class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)


@task_router.post("", status_code=201)
def create_task(task: TaskCreate):
    ...
```

测试发送空标题时：

```python
response = client.post(
    "/tasks",
    json={"title": ""},
)
```

执行流程是：

```text
FastAPI收到请求
    ↓
Pydantic尝试构造TaskCreate
    ↓
title违反Field(min_length=1)
    ↓
请求体验证失败
    ↓
FastAPI默认异常处理器自动返回422
```

因此，项目中不一定存在：

```python
raise HTTPException(status_code=422)
```

接口函数也不会开始执行，读取存储、创建Service和写入数据等业务代码都不会运行。

当前创建接口相关状态码的来源不同：

| 状态码 | 来源 | 是否进入接口函数 |
| --- | --- | --- |
| `201` | 路由装饰器中的`status_code=201` | 是，创建成功后返回 |
| `400` | 接口函数捕获业务`ValueError`后主动抛出`HTTPException` | 是 |
| `422` | FastAPI和Pydantic在参数或请求模型校验失败时自动返回 | 否 |

例如，标题类型错误、长度不符合约束、路径参数无法转换为整数，或者`Literal`字段收到允许范围之外的值，都可能在进入接口函数前产生`422`。测试中的：

```python
assert response.status_code == 422
```

是在验证框架根据请求模型约束产生的行为，并不意味着业务源码中必须手写一个`422`分支。

### Cookie和重定向的当前学习边界

Cookie是服务器要求客户端保存、并在后续请求中携带的一小段数据，常用于登录会话、用户偏好和安全机制。当前Task Manager没有用户系统，因此暂不展开；后续学习认证与授权、Session或JWT时结合真实业务学习。

重定向表示服务器让客户端改为访问另一个地址。常见状态码包括`301`、`302`、`307`和`308`。测试客户端可能自动跟随重定向；若要检查重定向本身，可以关闭自动跟随：

```python
response = client.get(
    "/old-path",
    follow_redirects=False,
)

assert response.status_code == 307
assert response.headers["location"] == "/new-path"
```

后续会结合路径末尾斜杠、登录跳转、旧API地址迁移或HTTP到HTTPS跳转学习。当前只需重点掌握基本请求方法、`params`、`json`、`status_code`和`response.json()`。

## FastAPI 测试中的依赖覆盖

### 为什么需要覆盖依赖

接口函数经常通过`Depends`取得自己需要的资源：

```python
def read_message(message: str = Depends(get_message)):
    return {"message": message}
```

正常运行时，FastAPI调用`get_message()`并把返回值传入`message`。在数据库接口中，相同位置通常是`Depends(get_session)`，它会提供真实数据库`Session`。

测试如果继续使用真实依赖，可能连接真实服务、修改练习数据或依赖外部环境。依赖覆盖允许测试暂时提供一个可控制的替代实现：

```python
test_app.dependency_overrides[get_message] = override_get_message
```

这表示：当FastAPI准备处理`Depends(get_message)`时，改为调用`override_get_message()`。

### `app.dependency_overrides`是什么

```python
app = FastAPI()
```

这里的`FastAPI`是类，`app`是该类创建的应用实例。`app.dependency_overrides`是这个实例上的一个属性，其值是Python字典`dict`：

```python
app.dependency_overrides == {}
```

因此它不是类，也不是方法，不能写成：

```python
app.dependency_overrides()  # 错误：字典不可这样调用
```

它保存的结构是：

```python
{
    原依赖函数: 替代依赖函数,
}
```

例如：

```python
app.dependency_overrides[get_message] = override_get_message
```

这不会修改`get_message`函数，也不会修改接口定义，只会改变当前`app`实例解析`Depends(get_message)`时选择的函数。

### 常用字典操作

因为`dependency_overrides`是字典，所以使用Python字典的操作：

```python
# 添加或替换覆盖
app.dependency_overrides[get_message] = override_get_message

# 安全读取；不存在时返回None
override = app.dependency_overrides.get(get_message)

# 判断是否已经设置
if get_message in app.dependency_overrides:
    ...

# 删除指定覆盖；不存在时不报错
app.dependency_overrides.pop(get_message, None)

# 清除当前应用的全部覆盖
app.dependency_overrides.clear()

# 遍历当前覆盖关系
for original, replacement in app.dependency_overrides.items():
    ...
```

测试fixture结束时常使用`clear()`，避免当前测试设置的覆盖继续影响后续测试。

### 覆盖关系属于具体应用实例

不同FastAPI实例分别保存自己的覆盖字典：

```python
app_a = FastAPI()
app_b = FastAPI()

app_a.dependency_overrides[get_message] = override_get_message
```

以上设置只影响`app_a`，不会影响`app_b`。测试必须在真正注册了待测试接口的那个`app`上设置覆盖。给另一个新建应用设置相同字典项，不会改变目标应用的请求行为。

### 字典中保存的是函数对象

覆盖关系的键和值都是函数本身：

```python
get_message
override_get_message
```

因此不写调用括号。`get_message()`表示立即调用并取得返回值；`get_message`表示把函数对象交给FastAPI，让框架在处理请求时调用。

覆盖前后的执行链如下：

```text
正常请求：Depends(get_message) → get_message() → "production"
测试请求：Depends(get_message) → 查到覆盖 → override_get_message() → "test"
```

### 两套依赖注入各自负责什么

这个实验同时包含两套依赖注入：

| 框架 | 触发方式 | 注入内容 |
| --- | --- | --- |
| pytest | 测试函数声明`override_client`参数 | 把fixture产生的`TestClient`传给测试函数 |
| FastAPI | 接口参数声明`Depends(get_message)` | 把依赖函数的返回值传给接口函数 |

pytest不负责执行`Depends`，FastAPI也不负责寻找pytest fixture。它们发生在不同层次。

### `yield fixture`的准备与清理

```python
@pytest.fixture
def override_client():
    test_app.dependency_overrides[get_message] = override_get_message

    yield TestClient(test_app)

    test_app.dependency_overrides.clear()
```

执行顺序是：

```text
yield之前：登记依赖覆盖并准备客户端
yield的值：注入测试函数，测试开始执行
yield之后：测试结束后清理覆盖
```

使用`return`会在交出客户端后结束fixture，无法在同一fixture中安排测试后的清理。使用`yield`后，pytest在测试结束时回到fixture继续执行后半段；测试断言失败时也会尽力执行清理。

`dependency_overrides`保存在FastAPI应用对象上。如果不清理，后面的测试可能继续使用上一个测试留下的替代依赖，造成测试污染。

### 从字符串实验迁移到数据库测试

字符串实验验证的是：

```text
正常字符串依赖 → 测试字符串依赖
```

数据库接口测试沿用同一结构：

```text
真实get_session → 可回滚的测试Session
```

依赖覆盖只解决“接口使用哪个Session”；要保证测试写入不永久留在数据库，还需要在外层开启事务，并在测试结束后回滚。两者职责不同，后续组合使用。

职责边界可以总结为：

| 组件 | 负责的事情 |
| --- | --- |
| `dependency_overrides` | 决定接口改用哪个测试依赖 |
| 测试`Session` | 执行测试中的ORM操作 |
| 外层事务 | 包住测试期间的数据库修改 |
| `rollback()` | 撤销外层事务中的测试数据 |
| `dependency_overrides.clear()` | 清除替代关系，避免污染后续测试 |

`dependency_overrides`本身不会创建数据库、开启事务、自动回滚或关闭Session，这些资源仍需由测试fixture明确准备和清理。

## 数据库隔离测试中的 Connection、外层事务与 Session

测试数据库接口时，需要区分三个不同层次的对象：

```text
Connection：决定SQL通过哪条具体连接发送
Transaction：决定一组SQL最终提交还是回滚
Session：管理ORM对象并把对象操作转换成SQL
```

它们在隔离测试中的关系是：

```text
Engine
└── Connection
    └── outer_transaction
        └── Session使用的SAVEPOINT
```

### 当前隔离测试涉及的常用接口

`Engine`是应用级连接入口和连接池管理者，不代表某一条正在使用的连接：

| 方法 | 主要参数 | 返回值 | 当前用途 |
| --- | --- | --- | --- |
| `engine.connect()` | 无 | `Connection` | 从连接池取得一条具体连接 |
| `engine.begin()` | 无 | 事务上下文中的`Connection` | 取得连接并自动提交或回滚，适合普通短事务 |
| `engine.dispose()` | `close=True`等 | `None` | 释放连接池资源，常用于应用关闭或重建环境 |

`Connection`代表当前使用的一条SQLAlchemy数据库连接：

| 方法 | 主要参数 | 返回值 | 当前用途 |
| --- | --- | --- | --- |
| `connection.begin()` | 无 | `Transaction`，当前通常为`RootTransaction` | 开启测试外层事务 |
| `connection.execute(statement, parameters=None)` | SQLAlchemy语句、可选参数 | `CursorResult` | 直接执行Core或文本SQL |
| `connection.commit()` | 无 | `None` | 提交Connection控制的事务；当前隔离fixture不能调用 |
| `connection.rollback()` | 无 | `None` | 回滚Connection当前事务 |
| `connection.in_transaction()` | 无 | `bool` | 判断连接是否处于事务中 |
| `connection.close()` | 无 | `None` | 关闭使用并将连接归还连接池 |

`connection.begin()`返回的`Transaction`用于控制同一层事务：

| 方法或属性 | 返回值 | 当前用途 |
| --- | --- | --- |
| `transaction.commit()` | `None` | 提交该事务；隔离测试不提交外层事务 |
| `transaction.rollback()` | `None` | 撤销该事务中的数据库修改 |
| `transaction.is_active` | `bool` | 判断事务是否仍然有效 |

测试Session的构造：

```python
session = Session(
    bind=connection,
    join_transaction_mode="create_savepoint",
)
```

当前涉及的构造参数：

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `bind` | `None` | 绑定Engine或Connection；测试必须绑定已开启外层事务的Connection |
| `join_transaction_mode` | `"conditional_savepoint"` | Session加入已有Connection事务时如何处理事务；测试显式使用`"create_savepoint"` |
| `autoflush` | `True` | 查询前是否自动flush待处理的ORM变化 |
| `expire_on_commit` | `True` | commit后是否让对象属性过期，之后访问时重新加载 |

构造调用返回一个新的`Session`对象。`add()`、`get()`、`execute()`、`scalars()`、`flush()`、`commit()`、`rollback()`、`refresh()`、`delete()`和`close()`的参数与返回值详见前文“SQLAlchemy ORM：Session常用方法、参数与返回值”，这里不重复维护第二套说明。

这些调用可能抛出SQLAlchemy异常：连接、认证或服务不可用常表现为`OperationalError`；唯一、外键和非空约束冲突常表现为`IntegrityError`；它们都属于更通用的`SQLAlchemyError`体系。发生数据库异常后，Session通常需要先`rollback()`才能继续使用。

### `Connection`负责执行通道

```python
connection = engine.connect()
```

`Engine`保存数据库连接配置并管理连接池；`engine.connect()`从中取得一条具体的`Connection`。后续测试事务和ORM Session必须使用同一条Connection，测试才能统一控制这些SQL。

### `outer_transaction`负责最终控制权

```python
outer_transaction = connection.begin()
```

这会在Connection上开启外层事务，并返回事务控制对象。它不是新的数据库连接，也不负责管理ORM对象，主要提供：

```python
outer_transaction.commit()
outer_transaction.rollback()
```

隔离测试不会提交外层事务，而是在测试结束时执行`rollback()`，撤销测试期间的全部修改。

### `Session`负责ORM工作

```python
session = Session(
    bind=connection,
    join_transaction_mode="create_savepoint",
)
```

Session负责追踪ORM对象、执行查询，以及把`add()`、属性修改和`delete()`转换成SQL。`bind=connection`保证它产生的SQL进入测试已经开启外层事务的同一条Connection。

如果Session直接绑定Engine，它可能从连接池取得另一条Connection：

```text
Connection A：测试的outer_transaction
Connection B：Session执行并提交SQL
```

此时Connection A的回滚无法撤销Connection B已经提交的数据。因此，`bind=connection`是外层事务能够控制测试写入的基础。

## `create_savepoint`如何保护外层事务

### 要解决的冲突

数据库接口内部会正常调用：

```python
session.commit()
```

测试同时希望接口完整执行，又希望测试结束后撤销写入。`join_transaction_mode="create_savepoint"`让Session加入已有外层事务时，在其中创建自己的保存点（SAVEPOINT）：

```text
外层事务：由pytest fixture控制
└── SAVEPOINT：由Session控制
```

### 创建任务的实际过程

Python代码：

```python
connection = engine.connect()
outer_transaction = connection.begin()

session = Session(
    bind=connection,
    join_transaction_mode="create_savepoint",
)

task = TaskRecord(title="pytest临时任务")
session.add(task)
session.commit()

session.close()
outer_transaction.rollback()
connection.close()
```

对应的数据库行为可以近似理解为：

```sql
BEGIN;                              -- 外层测试事务

SAVEPOINT sa_savepoint_1;           -- Session内部保存点

INSERT INTO tasks (...)
VALUES ('pytest临时任务', ...);

RELEASE SAVEPOINT sa_savepoint_1;   -- session.commit()

ROLLBACK;                           -- outer_transaction.rollback()
```

`RELEASE SAVEPOINT`只表示Session本次内部工作已经完成，并把结果保留在外层事务中；它不等于提交最外层事务。因此，当前测试能查询刚创建的任务，接口也能`refresh()`并取得数据库生成的ID，但数据仍未永久保存。

最后执行外层`ROLLBACK`时，临时任务仍会被撤销。

### 为什么不违反“commit后不能rollback”

普通业务代码中的`session.commit()`通常提交最外层事务，提交后不能用后续`rollback()`撤销。

隔离测试中存在两层边界：

```text
outer_transaction：从未提交
└── Session SAVEPOINT：可以被Session释放或回滚
```

这里的`session.commit()`完成的是Session内部保存点；测试最终调用的是尚未提交的外层事务的`rollback()`。它们操作的不是同一层事务。

### 多次`session.commit()`

同一个测试连续调用创建、更新接口时，可以形成多个保存点：

```sql
BEGIN;

SAVEPOINT sa_savepoint_1;
INSERT INTO tasks (...);
RELEASE SAVEPOINT sa_savepoint_1;

SAVEPOINT sa_savepoint_2;
UPDATE tasks SET done = true WHERE id = ...;
RELEASE SAVEPOINT sa_savepoint_2;

ROLLBACK;
```

每次Session提交只完成当前保存点，最终的外层回滚仍能同时撤销创建和更新。

### `session.rollback()`的边界

使用`create_savepoint`时，Session自己的回滚主要作用于当前保存点：

```sql
ROLLBACK TO SAVEPOINT sa_savepoint_1;
```

外层测试事务仍由fixture控制。这样，接口内部的`commit()`和`rollback()`不会轻易夺走测试对外层事务的最终控制权。

如果省略该参数，Session默认使用`conditional_savepoint`。在只有普通外层事务时，它通常采用类似`rollback_only`的行为：Session的`commit()`不会提交外层事务，但Session的`rollback()`可能传播到外层事务。外层回滚并非一定失效，但边界不如显式保存点模式清晰。

因此两项配置的职责是：

```text
bind=connection
    → 保证Session和外层事务使用同一条连接

join_transaction_mode="create_savepoint"
    → 让Session通过内部保存点管理自己的commit和rollback
```

### 测试结束时的清理顺序

```text
1. 清除FastAPI dependency_overrides
2. 关闭测试Session
3. 回滚outer_transaction
4. 关闭Connection
```

- 清除依赖覆盖：防止后续测试继续使用当前测试Session；
- 关闭Session：结束ORM工作并释放其资源；
- 回滚外层事务：撤销测试产生的数据库修改；
- 关闭Connection：将连接归还Engine管理的连接池。

可以用一句话概括三者的协作：

> Session决定执行哪些ORM操作，Connection负责把SQL发送到数据库，outer_transaction决定测试产生的全部操作最终保留还是撤销；SAVEPOINT则让Session在不提交外层事务的前提下正常执行自己的`commit()`和`rollback()`。

### 当前创建接口测试的验收证据

测试通过`TestClient`调用真实`POST /database/tasks`接口，接口内部执行`session.commit()`并返回`201 Created`。fixture结束后，使用独立Session查询临时标题`pytest事务隔离测试`和标签`pytest-isolation`，两者计数均为0。这同时证明：

- 创建接口完整执行并返回预期响应；
- Session的保存点提交没有提交外层事务；
- fixture的外层回滚清除了任务、标签和关联写入；
- 本次测试没有把临时记录留在练习数据库。

## pytest参数化测试：一套逻辑覆盖多组输入

### 为什么使用参数化

当测试步骤和断言相同，只有输入数据不同时，分别复制多个测试函数会产生重复代码。`pytest.mark.parametrize`可以给同一个测试函数登记多组参数，pytest在收集阶段把它展开为多条独立测试案例。

```python
@pytest.mark.parametrize(
    "invalid_priority",
    ["urgent", "", None],
    ids=["unknown", "empty", "null"],
)
def test_create_rejects_invalid_priority(
    database_client,
    invalid_priority,
):
    ...
```

源码中虽然只有一个函数，但pytest会收集成：

```text
test_create_rejects_invalid_priority[unknown]
test_create_rejects_invalid_priority[empty]
test_create_rejects_invalid_priority[null]
```

因此测试统计增加3条，而不是1条；某一组失败时，案例id会直接指出失败输入。

### 常用参数、用途与结果

`pytest.mark.parametrize(...)`返回一个用于标记测试函数的装饰器。当前常用参数如下：

| 参数 | 作用 | 当前示例 |
| --- | --- | --- |
| `argnames` | 声明注入测试函数的参数名；可用字符串或名称序列 | `"invalid_priority"` |
| `argvalues` | 提供每组参数值；多个参数时每组通常使用元组 | `["urgent", "", None]` |
| `ids` | 为各组案例设置易读名称，不改变数据和逻辑 | `["unknown", "empty", "null"]` |
| `indirect` | 让参数先交给fixture处理；属于后续进阶用法 | 当前不使用 |
| `scope` | 控制参数化资源的作用域 | 当前使用默认值 |

装饰器不会在定义函数时立即发出HTTP请求。pytest收集测试时读取标记，为每组数据安排一次函数调用。

### 参数值与fixture来自不同渠道

测试函数可以同时声明参数化数据和fixture：

```python
def test_create_rejects_invalid_priority(
    database_client,
    invalid_priority,
):
    ...
```

```text
database_client  ← pytest fixture创建
invalid_priority ← parametrize当前案例提供
```

当前`database_client`使用默认`function`作用域，所以三组参数案例分别创建Connection、外层事务、Session和TestClient，并分别在结束时回滚。

### 多参数形式

如果每组案例需要多个输入，可以声明多个名称，每组值使用对应元组：

```python
@pytest.mark.parametrize(
    ("priority", "expected_status"),
    [
        ("high", 201),
        ("urgent", 422),
    ],
)
def test_priority(database_client, priority, expected_status):
    ...
```

每个元组的位置必须与`argnames`顺序一致。测试函数参数名也必须与登记名称匹配，否则pytest收集阶段会报错。

### 当前非法优先级测试

`"urgent"`、空字符串和`None`分别对应未知值、空值和JSON `null`。三者都不符合创建模型的`Literal["low", "normal", "high"]`约束，因此由Pydantic在进入接口函数前返回`422`：

```python
assert response.status_code == 422
assert response.json()["detail"][0]["loc"][-1] == "priority"
```

Pydantic错误位置字段名是`loc`。本轮曾把状态码写成`400`并把键写成`local`；第一条断言先失败时，第二个拼写错误不会立即暴露。修正断言时要继续检查后续尚未执行的代码，避免一次只暴露一个错误。

本轮数据库测试文件最终得到`6 passed, 1 warning`：原有3条工作流测试，加上参数化生成的3条非法输入案例。外部查询确认测试标题和标签计数均为0。

## 使用`pytest.raises()`验证预期异常

2026-10-22补充控制流：Service中的raise仍会中断当前方法，异常向外传播，被pytest.raises捕获后，继续的是with代码块外的测试语句，不会回到Service或继续with块内raise之后的语句。预期ValueError被抛出则继续后续断言；没有异常或异常类型不匹配则该用例失败。这类似外层try/except捕获，但额外检查必须发生预期异常。

### 为什么不能只让异常自然抛出

Service对空标题、非法优先级和空标签主动抛出`ValueError`。如果测试直接调用：

```python
service.create_task("   ")
```

异常会被pytest当成测试失败。这里的业务预期恰好是“必须抛出该异常”，所以需要用`pytest.raises()`声明预期结果。

### 基本形式和执行结果

```python
with pytest.raises(ValueError):
    service.create_task("   ")
```

`pytest.raises()`属于pytest，接收预期的异常类型并返回一个上下文管理器。`with`代码块结束时会检查：

| 被测代码结果 | pytest结果 |
| --- | --- |
| 抛出预期的`ValueError`或其子类 | 该异常断言通过 |
| 没有抛出异常 | 测试失败，提示没有抛出预期异常 |
| 抛出不属于预期类型及其子类的异常 | 异常继续传播，测试失败 |

只有可能抛出异常的语句应放入`with`块，后续普通断言放在块外，避免过大的代码范围意外吞掉同类型异常。

### 使用`match`检查异常消息

```python
with pytest.raises(
    ValueError,
    match="Task title cannot be empty",
):
    service.create_task("   ")
```

`match`不是普通字符串全等比较，而是用正则表达式搜索异常消息。当前错误消息不包含特殊正则字符，可以直接使用。若消息含有`(`、`)`、`[`、`]`、`.`、`*`等字符，又希望按字面值匹配，可使用：

```python
import re

with pytest.raises(
    ValueError,
    match=re.escape(expected_message),
):
    ...
```

### 取得实际异常对象

需要对异常对象进行更多检查时，可以使用`as`：

```python
with pytest.raises(ValueError) as exception_info:
    service.create_task("   ")

assert str(exception_info.value) == "Task title cannot be empty"
```

其中：

| 对象 | 含义 |
| --- | --- |
| `exception_info` | pytest提供的异常信息包装对象 |
| `exception_info.value` | 实际捕获的异常对象 |
| `str(exception_info.value)` | 异常消息 |

2026-10-23结合候选生成测试补充异常原因检查：

```python
with pytest.raises(RuntimeError, match="模型服务请求失败") as caught:
    deepseek_demo.generate_candidate("test")

assert caught.value.__cause__ is original
```

`caught`是pytest的ExceptionInfo包装对象，`caught.value`才是捕获到的RuntimeError。业务代码`raise RuntimeError(...) from error`把原异常记录为`__cause__`；`is original`进一步确认保留的是测试预先创建的同一个异常对象。当原异常由真实`json.loads()`或Pydantic内部产生、测试没有预先保存它时，本文件用`isinstance(caught.value.__cause__, json.JSONDecodeError)`或ValidationError检查类型。

**预设Timeout或ConnectionError，为何却断言RuntimeError：**

Timeout和ConnectionError都属于requests.RequestException的子类，不属于RuntimeError。它们不会直接与`pytest.raises(RuntimeError)`匹配。测试包住的是整个generate_candidate调用；该函数内部还有一层异常处理：

```python
try:
    response = requests.post(url, headers=headers, json=payload, timeout=(10, 20))
    response.raise_for_status()
except requests.RequestException as error:
    raise RuntimeError("模型服务请求失败") from error
```

执行链是`模拟post抛Timeout → 业务except捕获Timeout → 新建并抛RuntimeError → 测试捕获RuntimeError`；换成ConnectionError同理。原始异常对象没有被改成新类型，而是作为新异常的__cause__保留。如果业务函数没有这段转换，原始请求异常就会直接传到测试，因与RuntimeError不匹配而失败。测试因此同时验证“对外提供统一错误”与“保留内部故障原因”。

`match`依旧是对异常消息进行正则搜索，不是检查cause；只写`pytest.raises(RuntimeError)`也不会自动检查错误说明。捕获预期异常后执行的是with块外的断言，不会恢复已经被异常中断的业务函数。`is`与`isinstance`的详细区别参见后文既有对象比较内容。

当前Service测试把`pytest.raises()`与参数化组合，一套测试逻辑分别验证三类业务错误。每组参数仍是一条独立测试，并分别获得独立的数据库fixture和回滚过程。

## `is`与`==`：验证ORM对象复用

`==`比较两个值是否相等，`is`比较两个变量是否引用内存中的同一个Python对象：

```python
left == right  # 值相等
left is right  # 对象身份相同
```

对于字符串、数字、列表等业务值，通常使用`==`：

```python
assert task.title == "pytest Service创建测试"
assert tag_names == ["python", "database"]
```

本次测试需要证明Service没有创建第二个同名标签，而是复用了当前Session中已有的`TagRecord`：

```python
saved_existing_tag = repository.get_tag_by_name(
    "pytest-service-existing"
)

assert saved_existing_tag is existing_tag
```

在同一个SQLAlchemy Session中，同一数据库行通常由身份映射（Identity Map）维护为同一个ORM对象，因此`is`可以直接表达“就是原来的对象”。这比只比较名称更强：两个不同的`TagRecord`也可能拥有相同名称，但它们不是同一个实例。

不要把`is`用于普通字符串和数字的值比较：

```python
title is "任务"   # 错误用法
title == "任务"   # 正确
```

Python可能缓存某些不可变对象，使错误的`is`比较偶尔看似成功，但这种行为不能作为业务判断依据。`None`是单例，判断空值应使用：

```python
value is None
value is not None
```
