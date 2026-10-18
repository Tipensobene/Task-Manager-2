# 学习进度与阶段路线

> 更新日期：2026-10-18。实现状态依据源码与Git核对；助手在专用测试库实际运行完整pytest套件108 passed；无数据库导入测试文件55 passed。项目使用说明见README.md，长期导师规则见AGENTS.md，详细知识笔记见get_knowledge.md。

## 1. 当前继续位置

**阶段四：数据库演示API主要功能已实现并逐项测试；正式任务接口已全部从JSON迁移到PostgreSQL，下一步进行迁移收尾与工程化。**

- 阶段三已完成并发布v3.0.0；保留此前发布证据，本次未重新访问远程。
- 2026-10-13核对：当前分支`feature/database`；数据库教学示例整理、正式API迁移和学习文档已分别提交为`2a2d080`、`a68ace5`和`0b73591`，工作区在提交后无未提交修改。这些提交仍只存在于本地，尚未合并、打标签或推送。
- 已完成SQL、PostgreSQL、Psycopg、SQLAlchemy基础、ORM关系、事务实验及FastAPI数据库依赖接入。
- database_api_demo.py已实现列表、详情、创建、部分更新、删除、完成任务；创建和更新支持标签清理、复用及关联。
- 列表的priority、done、keyword和tag动态过滤已实现并通过隔离测试；数据库统计接口用一条聚合查询返回总数、已完成数和未完成数，混合数据与事务隔离空表场景均已验证。
- database.py提供Engine、SessionFactory和get_session；orm_models.py提供任务、标签和中间表映射。
- 正式七个任务接口均已改用Repository、Service和数据库Session，并有事务隔离测试；Alembic两版迁移、原库接管及测试库往返验证已完成，README已补齐迁移运行说明。旧JSON导入、Docker交付及阶段独立验收待完成。
- Alembic两版迁移及原库接管已验收。旧JSON导入已完成入口、友好异常处理、事务回滚及说明，2026-10-18完整回归108 passed，真实JSON尚未导入。本地功能提交3e45e54已完成，教学文档随独立提交保存，均未推送。当前进入阶段四Docker小节整体导学，环境尚未核验或安装。

## 2. 学习者背景、目标与时间预算

计算机专业研一学生，已有C/C++和历史Java基础；Python/Web后端仍需巩固。Java基础当前保留程度尚未摸底。

2026-10-07确认：目标由2027年暑假前调整为**2027年1月底至2月初具备初步投递条件**。预计学校2027年1月15日开始寒假，考试结束日期尚未确定。

主投AI应用、AI Backend、LLM应用及相关Python后端方向，以可靠后端工程能力支撑AI项目；Java后端作为有时间上限、有独立成果要求的备选。不是承诺同时达到所有方向或大厂岗位的全部标准。

增加Java的动机：担心AI Agent岗位变化，希望扩大选择并补强工程基础。这是学习者的风险顾虑，不是已验证的招聘市场结论；投递前另行核对实际岗位要求。

| 时段 | 时间约束 | 安排原则 |
| --- | --- | --- |
| 现在至11月底 | 每天总学习时间可达7～8小时，导师任务可能占用一天或数天 | 集中建设后端基础和首个AI项目闭环 |
| 12月至考试结束 | 可能仅有每天1～2小时 | 旧题复现、知识回顾、小幅维护，降低新增内容 |
| 考试结束至1月底/2月初 | 可用容量待实际确认 | 项目补齐、Java备选、独立验收与投递准备 |

- 7～8小时是总容量，包含算法、工程和CS基础，不是每项分别投入；原算法约2小时/日作为平时参考，考试期不固定照搬。
- 每周按预计容量的70%～80%安排任务，保留导师工作、调试和复习缓冲；不假设每天都可高强度学习。
- 先保证核心成果与独立能力，再扩展技术。考试结束日期、Java摸底结果与具体岗位要求作为后续细化依据，不阻塞当前推进。
- 当前多项功能是在骨架和多轮提示下完成。学习者已主动发现优先级校验缺失及重复逻辑，但完整独立重建能力仍待验证。
- 已同意渐进减少提示；按AGENTS.md的分级帮助执行，不突然切换成完全独立开发。

## 3. 阶段总览

| 阶段 | 项目或主题 | 实际状态 |
| --- | --- | --- |
| 0 / 1 | Python 基础与早期 Task Manager | 历史记录已完成 |
| 2 | Task Manager 2.0 Rebuilding + Git | 已完成并推送，保留 v2.0.0 |
| 3 | Task Manager 3.0：HTTP + FastAPI | 功能验收、文档、合并与 v3.0.0 推送完成 |
| 4 | Task Manager 4.0：数据库与工程基础 | 数据库演示API已逐项验收，正式迁移与工程化待完成 |
| 5 | AI Task Manager：LLM API | 规划中 |
| 6 | Personal RAG | 规划中 |
| 7 | Research Agent | 规划中 |
| 8 | Production Agent | 后续扩展，不作为本轮投递前置条件 |
| 9 | 开源项目阅读与贡献 | 后续扩展，不作为本轮投递前置条件 |

## 4. 已完成阶段及知识点大纲

### 阶段 0 / 1：Python 基础与早期任务管理

历史记录中已接触和使用：

- 基本数据类型、list / dict、条件、循环、函数。
- 字符串 strip、split，遍历 enumerate，文件读写和 JSON。
- 异常处理、pathlib、typing、类型注解。
- 类、对象、方法、dataclass、装饰器基础。
- Socket 网络实验及 HTTP / JSON 基础。

成果：通过早期任务管理程序练习输入、数据处理和持久化。这些历史练习未在本轮重新运行。

### 阶段 2：Task Manager 2.0 Rebuilding + Git

已完成内容：

- 根据需求、模块划分和函数职责重新构建命令行任务管理器。
- 模型、业务、存储、CLI、工具拆分；认识 UI、业务逻辑和持久化的职责。
- 任务增删改查、优先级、搜索、统计、JSON 兼容与 logging。
- Git 初始化、status、add、commit、log、diff、restore、revert。
- 分支创建和切换、merge、.gitignore、remote、push 与 GitHub 协作基础。

成果：Task Manager 2.0 已推送，v2.0.0 标签保留。Git 后续作为日常开发工具使用，不重新布置整套入门练习。

### 阶段 3：Task Manager 3.0 Web API

阶段变化：CLI 的 input / print 交互扩展为客户端通过 HTTP / JSON 调用服务器；继续复用业务逻辑和 JSON 存储。

#### 入门实验与知识点

已完成实验：

- GET /、GET /hello/{name}、GET /add?a=10&b=20、POST /users。
- 综合练习 GET /courses/{course_name}、GET /study-time、POST /study-plans。
- 输入边界、首尾空白清理、计算字段和基本错误处理。

已学习并在项目中使用：

- 客户端 / 服务器、localhost、IP、端口、URL、HTTP 请求与响应。
- 路径参数、查询参数、请求体、响应体、JSON 与 Python 字典的区别。
- GET / POST / PATCH / DELETE；200、201、400、404、422、500 的实际用途。
- FastAPI 与 Uvicorn 分工、路由装饰器、Swagger /docs、OpenAPI、Query(alias=...)。
- Pydantic BaseModel、Field、ConfigDict、长度和数值约束、字符串清理。
- TaskCreate、TaskUpdate、TaskResponse、TaskStatsResponse 的职责。
- model_dump、exclude_unset 与 exclude_none 的区别；省略字段、null、空列表的不同含义。
- except 捕获、raise 抛出，业务 ValueError 到 HTTPException 的转换。
- 全局 StorageError 处理器与 JSONResponse，HTTP 与业务 / 存储异常的分层。
- APIRouter、prefix、tags、include_router，以及避免循环导入。
- Python requests 客户端、超时与连接异常处理。
- dict.items / values、关键字参数解包、is None 与真假值判断。
- dataclasses.field 与 pydantic.Field，default_factory 与可变默认参数。
- 循环变量覆盖、构造清理后列表、先校验所有字段再修改对象。
- 临时文件写入后 replace 正式文件；ID 与列表位置的区别。
- Git 分支整合、快进合并、暂存区差异、附注标签与推送。

原路线还包含 PUT / PATCH 区别、Header、204、curl 和网络原理等理论目标；它们不都具有逐项独立验收记录，后续遇到相关场景时补充确认，不将整份路线自动标为精通。

#### 项目成果

- 7 个任务接口：创建、列表、统计、详情、部分更新、完成、删除。
- priority、done、keyword、tag 单独或组合过滤。
- Router / Service / Storage 分层；内部 Task 包含 id、title、done、priority、tags。
- Task Tag 功能：创建标签、更新或清空标签、大小写无关过滤、旧 JSON 缺少 tags 时兼容为 []。
- CLI 保留，requests 客户端可查询统计；详细接口、字段和启动方式以 README 为准。
- 理论问答已讨论请求执行链、模型职责、异常转换及替换存储的影响；经纠正后继续推进。

#### 验收与发布记录

| 范围 | 历史结果 | 说明 |
| --- | --- | --- |
| 基础 API 综合验收 | 36/36 | CRUD、过滤、状态码、持久化、损坏 JSON、OpenAPI |
| 标签创建 | 8/8 | 默认、清理、持久化、错误输入、旧数据 |
| 标签更新 | 8/8 | 更新、保留、清空、错误输入、不部分修改 |
| 标签过滤 | 7/7 | 大小写、无结果、空查询、组合过滤 |
| 标签联合验收 | 23/23 | 创建至重载、更新、查询、原接口相关回归 |
| 最终主线检查 | 通过 | 导入、7 个接口、4 个过滤参数 |

以上数字来自此前临时隔离测试，范围有重叠，不能相加当作独立用例总数。本轮文档重构没有重新运行测试，仓库尚未建立持久化 pytest 套件。测试未修改真实任务 JSON。

关键 Git 记录：

- 4625476：创建任务标签。
- a3a71d8：更新标签。
- 94cb9db：标签过滤。
- 2d490e6：标签文档。
- c6c1667：学习进度文档，阶段三发布提交。
- feature/task-tags 已合并到 feature/web-api，再合并到 main。
- 2026-10-03 创建附注标签 v3.0.0，推送 main 与标签并核对远程成功。

#### 带入阶段四的问题

- 当前 ID 为最大现有 ID + 1，删除最大 ID 后仍可能复用；尚非永久不复用的 ID 机制。
- 临时文件替换降低中途写坏正式文件的风险，但未解决并发覆盖或多个请求共用临时文件的竞争。
- Service 当前依赖内存任务列表；数据库替换会涉及持久化以及部分查询和事务组织，不是只换文件名。
- 需要把临时验证逐步变成学习者自己编写的可重复测试。
- 历史测试出现 Starlette / httpx 弃用警告；当测试环境工作开始时核对实际依赖，不把历史警告当成业务错误。
- 代码格式、旧注释和查询实现等打磨曾按学习者偏好推迟，需按需要与学习者决定安排，不能无限扩张收尾工作。

原阶段三“约 5 周，最多 1 周机动”的时间表仅是历史规划，不是当前任务或固定截止时间。原来的 POST 待验收、最小空缺 ID 和尚待实现响应模型等描述已经被上述实际结果替代。

## 5. 当前阶段四：Task Manager 4.0 详细进度

### 目标与本阶段技术角色

目标：把 JSON 持久化迁移为 PostgreSQL，建立数据设计、可靠修改、自动验证和运行交付能力，尽量保持现有 API 的对外行为。

| 内容 | 项目中的作用 |
| --- | --- |
| 关系模型与 SQL | 组织任务和标签，用查询表达业务数据需求 |
| PostgreSQL | 存储数据、执行查询、提供约束与事务能力 |
| Python 数据库连接 | 在 Python 中连接、参数化查询并处理连接问题 |
| SQLAlchemy ORM | 映射 Python 对象和数据库表，组织查询与 Session |
| 事务 | 多步相关操作一起提交或失败回滚 |
| Alembic | 有版本地升级数据库表结构 |
| pytest | 可重复验证 API、Service 和持久化行为 |
| Docker / Compose | 描述并运行 API 与数据库环境，理解网络和持久化 |

### 实际进度

| 小节 | 当前状态 | 后续可验收成果 |
| --- | --- | --- |
| 阶段导学 | 2026-10-03 已讲解；不是独立掌握证明 | 理解总体目标、技术角色和学习顺序 |
| 表、行、列、主键 | 已讲解并在 PostgreSQL 创建真实表 | 已将 Task 映射为 tasks 表并解释字段 |
| 外键、约束、多对多 | 已设计并创建 tasks / tags / task_tags | 已说明关联、联合主键、外键和级联删除 |
| SQL 基础 | 已在 Query Tool 执行增删改查、排序、统计、JOIN 与标签数组聚合 | 后续结合 Python 和 ORM 继续巩固 |
| PostgreSQL 环境 | 已安装 PostgreSQL 18.6，创建 task_manager_learning | 已能通过 psql 和 pgAdmin 连接练习数据库 |
| Python 连接与参数化查询 | Psycopg连接、参数化查询和异常实验已完成 | 安全传递参数，区分连接和查询错误 |
| SQLAlchemy ORM / Session | 映射、查询、CRUD与Session实验已完成 | 独立实现基本数据库 CRUD |
| 事务与 FastAPI 接入 | 提交/回滚实验、依赖注入与演示接口已验证；正式迁移待做 | 多步失败不留下部分修改，原 API 正常 |
| 标签关系与查询 | 多对多、selectinload、标签创建替换清空已实现并测试 | 创建、更新、查询持久化的任务与标签 |
| Alembic 结构迁移 | 1.20.0已安装、环境已初始化；配置与日志已讲解，连接和迁移尚未验收 | 检查并执行增加字段等迁移 |
| 旧 JSON 数据导入 | 仅介绍与结构迁移的区别 | 可验证地导入任务和标签 |
| pytest | 已安装；已学习测试发现、assert、fixture及function作用域、TestClient、yield清理、依赖覆盖、外层事务与SAVEPOINT；数据库创建接口隔离测试已通过 | 隔离测试数据，能自行重跑和解释失败 |
| Docker 运行交付 | 仅介绍镜像、容器、数据卷、Compose | API 与数据库可按配置启动，数据保留 |
| 最终独立验收 | 待开始 | 独立完成新的数据库功能及迁移、测试 |

### 已学知识与代表性验收证据

以下来自此前会话的临时测试，范围有重叠；不是仓库中的完整自动化回归套件，也未证明独立掌握：

- Psycopg：连接、游标、execute、fetchone/fetchall、参数化SQL、连接/语法/唯一约束错误。
- SQLAlchemy：URL、Engine、Connection、text、命名参数、Row/Mapping；DeclarativeBase、Mapped、mapped_column、select、scalars、Session。
- 事务：add、flush、commit、rollback、refresh；autoflush、transient/pending/persistent及Session关闭。flush后的persistent不等于事务已提交；已提交事务不能通过后续rollback撤销。
- 关系：Table/ForeignKey、secondary、back_populates、多对多、延迟加载、selectinload与N+1。列表临时测试确认两条主要业务SELECT。
- API：环境变量、SessionFactory、yield依赖、Depends、请求/响应模型、from_attributes、field_validator、classmethod、Literal与default_factory。
- 创建：默认值、标题校验、标签规范化去重、已有标签复用、新标签及关联持久化；移动add时机后，以SAWarning作为错误重测通过。
- 更新：标题/优先级/标签替换与清空；显式null从500修正为400；Literal使创建和更新的urgent请求返回422，非法写入未发生。
- 删除：返回200及原数据，后续查询和重复删除404，关联行消失、标签保留。该验收验证结果，不单独证明关联清理由ORM还是数据库CASCADE完成。
- 完成任务：首次与重复调用200，done持久化为true，标签保留，不存在返回404。
- 测试临时任务与临时标签已按此前记录清理；identity序列允许空缺。Starlette/httpx弃用提示待正式测试环境阶段核对。

### 剩余交付与边界

1. 补齐必要的列表过滤、统计，并开始少量pytest隔离测试，把手工验收变成学习者能运行的检查。
2. 将数据库演示成果整合到正式项目，按需求整理Router、Service和数据库访问职责，明确事务边界与异常转换。
3. 学习Alembic并完成一次真实结构迁移，验证旧JSON数据导入。
4. 完成配置、日志、Linux运行基础及Docker Compose启动API与PostgreSQL。
5. 用一个小需求进行独立实现、排错和复现验收，再收束阶段四。

数据库知识分深度推进：SQL、约束、事务、基本索引与EXPLAIN要能实践；ACID、隔离、锁和死锁能结合例子解释；MVCC和索引内部实现逐步深入。先用扎实PostgreSQL，再比较MySQL，不同步铺开两套完整实践。Redis不是阶段四结束的必要条件。

未决问题包括：同名标签并发创建竞争、数据库级priority CHECK约束、正式业务规则兼容、响应转换适用范围及持久测试覆盖。按实际整合需要逐项处理，不将全部理论变成进入LLM阶段的门槛。

### 下一次的具体起点

2026-10-18 Git授权执行：用户明确确认已审阅两提交方案并授权执行。本地功能提交3e45e54（feat: add transactional legacy JSON import）包含导入实现、两份测试和README；教学规范、知识笔记及进度作为独立docs提交保存，提交后核对git log和工作区。未合并、打标签或推送，本轮未重复运行最近108 passed测试。接下来回到Docker导学，等待学习者解释两个容器中的localhost含义；尚未检查Docker环境。

2026-10-18继续位置：用户澄清并理解真实JSON尚未导入，当前继续学习。开始Docker小节整体导学（仍属阶段四）：问题是可复现运行环境，目标为API/独立PostgreSQL容器、Compose协作、迁移及持久卷验证；先解释镜像/容器/Dockerfile/Compose及端口、网络、卷，不先安装或改配置。环境尚未核验，导学后确认理解再安排第一步。导入Git两提交方案已展示但未获明确提交授权，保留待办，不自动提交；不阻塞概念导学。

2026-10-18导入收尾：SQLAlchemyError已正确导入并加入main捕获范围；导师补模拟数据库错误入口用例，沿用退出1、实际错误提示与无成功输出断言。无数据库文件55 passed，随后专用测试库完整套件108 passed，测试写入回滚。README已补导入路径、字段规则、整批事务、退出码和限制；业务代码本轮仅同步注释，未代写功能。下一步先讲本轮新增用例，再做Git变更摘要/复盘；不自动提交、推送或真实导入。原库已有任务，按当前规则拒绝合并导入；并发导入防重未实现且不宣称支持。

2026-10-18友好错误验收：main在parse_args之后捕获导入调用的OSError/ValueError，消息包含实际error，以SystemExit(1)结束，不打印成功结果。导师更新入口失败测试为数据错误和文件缺失两组，检查退出1、标准错误及空标准输出；无数据库文件54 passed，未重跑数据库或全套（上次全套106 passed）。同步旁注，不改业务行为。下一步介绍SQLAlchemyError处理数据库失败，随后README/最终回归收尾；真实JSON仍未导入。

2026-10-18路径传递旁注：按用户授权把tmp_path→file_path→sys.argv字符串→args.file_path→fake形参path→received_paths的完整具体例子合并进入口测试旁注；说明局部变量不共享、比较相同路径不用对象身份。本轮仅注释/进度更新，未运行测试。下一步讲解parser.exit(status=0,message=None)并安排学习者在main中捕获导入调用的OSError/ValueError，以1退出并输出简洁错误；解析器自身缺参/帮助仍维持2/0。数据库错误处理随后按需求补充，暂不真实导入。

2026-10-18入口连接验收：main正确调用import_legacy_file并在成功后打印len(mapping)与映射。导师更新成功入口测试，用替代函数记录Path参数、返回预设映射，检查两行输出；新增失败不打印成功测试，更新代码旁注以消除旧“只打印路径”描述。无数据库文件53 passed，随后专用测试库完整pytest 106 passed，数据库写入由测试事务回滚；真实JSON未导入。本轮仅改测试和注释，未代写业务功能。下一步先讲清替代入口测试，之后安排友好错误提示及README收尾，暂不对已有任务原库运行导入。

2026-10-18教学要求补充：用户已理解add_argument登记与parse_args执行的区别，要求把表格类比与具体输入流旁注代码，并将“整体通俗目标→样例贯穿跨文件执行→逐步值变化→正常/异常分支”作为逐行解释规范。已合并到AGENTS现有条款及main注释，本轮仅规则/注释/进度更新，未运行测试或改变功能。下一步仍由学习者把main的路径打印替换为import_legacy_file调用及成功数量/ID映射输出，导师随后更新入口测试；暂不运行真实导入。

2026-10-18入口注释教学：按用户明确授权在main及三个入口测试加入详细中文注释和具体执行例子，解释sys/argv属性替换、add_argument登记与parse_args实际转换、Namespace、输出比较、文件不创建，以及缺参/帮助在库内部产生SystemExit的分支。只改注释并清除文件末尾多余空行，未改变业务逻辑，本轮未运行测试；先让学习者结合源码理解，不提前连接真实导入。

2026-10-18入口验收：main正确登记file_path/type=Path并打印，主入口guard正确。已将argparse三个接口、参数名与输入值区别合并笔记。导师新增三项入口测试，模拟argv并捕获输出/退出状态；本轮无数据库文件52 passed，数据库测试未重跑（此前4项通过）。下一步讲清sys.argv/capsys/SystemExit后，由学习者将main的打印替换为调用import_legacy_file并输出数量和映射；不执行真实导入，后续调整入口测试。本轮未代写业务代码。

2026-10-18事务测试知识整理：用户已理解monkeypatch从setattr到fixture清理期间持续生效，作用于类方法且不限一次调用。已合并文件事务入口、失败模拟逐段解释、原方法引用与闭包、Python列表不随回滚清空、get可能命中身份映射，以及undo撤销全部替换的边界。本轮仅文档维护，未重跑测试；最近专项结果仍53 passed。下一任务仍为导入使用入口及完整回归，不自动执行真实文件导入。

2026-10-18事务入口验收：import_legacy_file先load、函数内导入SessionFactory、begin块内整批导入、块外return均正确。导师新增两测试及局部fixture，monkeypatch将工厂绑定测试连接并create_savepoint，外层夹具回滚保护数据。成功后重新查到两条记录并拒绝重复调用；第二条模拟RuntimeError，第一条已flush的任务及新标签均回滚。两导入文件53 passed，专用测试库，无持久业务写入。本轮未代写业务功能，下一步先讲解monkeypatch与异常放在with外的意义，再安排入口/完整回归，不直接真实导入。

2026-10-18知识整理：expire_all例子合并到原Session章节，集合/字典ID映射、scalars整模型查询和enumerate合并到导入章节。本轮核对源码并修改文档，未运行测试。下一步由学习者新增import_legacy_file(file_path: Path)->dict[int,int]调用者函数：先load完整校验，再用SessionFactory.begin开启会话及事务，调用import_legacy_tasks，退出成功后返回映射；数据库工厂可在函数内延迟导入，避免纯模型导入就要求密码。需讲明异常向with外传播才能自动回滚。尚不执行真实导入，导师后续补事务测试。

2026-10-17导入循环验收：非空目标检查已恢复。导师新增成功导入测试，夹具事务内delete任务构造空目标，结束回滚恢复；测试覆盖两条任务完成状态/优先级/时间、ID映射和共享标签复用。执行两导入测试文件51 passed（非完整套件），专用测试库，无提交。expire_all后重读以验证实际flush的数据。本轮未修改业务代码。下一步先讲解成功测试的新方法及事务内清空边界，再实现调用者事务组织，补失败整批回滚和重复执行拒绝测试。

2026-10-17导入循环静态验收：Service创建、done复制、id_mapping累积、循环外flush与return位置正确，但此前非空目标统计检查被删除，尚不满足导入边界。下一步由学习者在循环之前恢复repository.get_stats及total非零raise，保留新循环；之后导师复验已有拒绝测试并补成功导入测试。本轮未连接数据库或执行导入，也未代写业务代码；不以局部正确认定整函数通过。

2026-10-17目标非空检查复核：学习者已补raise，助手在专用测试库运行两个导入测试文件，共50 passed（49模型/读取用例+1非空拒绝数据库用例），数据库测试由外层事务回滚。下一步学习者实现导入循环：复用TaskService.create_task，设置返回ORM对象的done，记录旧新ID字典，结束flush后返回，不commit。需说明create_task内部add_task已flush生成ID，但不等于提交；最终flush确保最后一条done更新发往数据库。空目标成功及回滚测试由导师后续编写。本轮未代写业务代码。

2026-10-17目标非空检查验收：import_legacy_tasks正确使用Repository统计，但if中仅构造ValueError，遗漏raise。导师新增tests/test_legacy_import_database.py，在测试库通过database_session准备已有任务并调用导入，实际1 failed（DID NOT RAISE ValueError），外层事务回滚测试写入。下一步由学习者补raise后复验；空输入占位返回不单独写镜像实现测试。尚未实现数据库导入循环或提交，业务代码未代写。

2026-10-17重复源ID验收：学习者正确先校验再查seen_ids，首次出现加入集合与结果列表，重复抛含ID的ValueError。导师补相邻[3,3]和非相邻[3,8,3]用例，独立导入测试49 passed，无数据库连接；测试用不同标题避免将标题相同误判为拒绝原因。下一步讲解本组测试后进入导入数据库函数的事务边界设计（Session由调用者提供、函数不commit、拒绝任务非空目标、保留done和标签并返回ID映射）。本轮未代写业务代码。

2026-10-17非法元素测试：导师新增3个用例，文件第一条合法，第二条分别为123、None或done为字符串的字典，预期ValidationError，独立测试47 passed。覆盖错误元素不被跳过且不会返回前半段结果；只涉及内存结果，不等于数据库事务回滚已验证。下一轮讲解后安排学习者实现重复旧ID检测；本轮未修改业务代码、未连接数据库。

2026-10-17教学分工更新：用户明确要求保留当前测试轮次，改由导师编写每轮测试后讲解，业务功能仍由学习者实现，规则已加入AGENTS。本轮已代写非列表根结构四用例，使用合法JSON的dict/str/int/None，断言ValueError及Not a list消息；独立测试44 passed，无数据库连接。下一轮仍须讲清本组代码，不直接跳到新业务；之后由导师补非法元素测试并讲解，再安排学习者实现重复源ID检查。未提交Git。

2026-10-17当前验收：非法JSON测试已先关闭写文件再读取，助手复验独立测试40 passed，无数据库连接。本轮未代写代码。下一步参数化写入合法JSON但非列表顶层（dict、str、int、None），预期ValueError且match="Not a list"，区分根结构错误与JSON解析异常；之后补非法元素和重复ID。

2026-10-17非法JSON测试检查：实际40 passed，但pytest.raises与读取调用嵌套在写文件with内，读取可能看见尚未刷新的空文件，仍抛相同异常而假通过，不能确认测试覆盖预期的"["内容。下一步学习者将raises移到写文件with外（与with open对齐），关闭写文件后再读取；无需额外flush。本轮未代写代码，暂不推进结构错误测试。

2026-10-17缺失文件测试验收：仅构造不存在路径，使用raises(FileNotFoundError)包住读取调用，正确；助手运行独立测试39 passed，无数据库连接。本轮未代写代码。下一步讲解file.write直接写入非法JSON文本，用JSONDecodeError验证解析失败；随后补顶层/元素结构错误及重复旧ID。

2026-10-17当前验收：正常两记录读取测试的fixture已改为tmp_path，助手复验38 passed；覆盖记录数量、顺序、规范化和默认值，无数据库连接。本轮未修改业务代码或测试。下一步补不存在文件的FileNotFoundError及错误JSON的JSONDecodeError传播测试，再补顶层/元素结构错误与重复旧ID。

2026-10-17正常记录读取测试核对：文件准备和两条记录断言正确，但误将内置fixture参数tmp_path写成temp_path，pytest无法找到fixture。实际运行37 passed, 1 error（测试准备阶段错误，函数体未运行）。下一步由学习者将函数参数及路径拼接中的temp_path都改为tmp_path，再复验；本轮未修改代码或访问数据库。

2026-10-17当前验收：空列表读取测试正确使用tmp_path、UTF-8写入、关闭文件后调用load_legacy_tasks，助手运行独立测试37 passed，未连接数据库。本轮知识已合并tmp_path作用域与磁盘保留差异、Path/文件对象、读取调用链；未代写代码。下一步由学习者写两条任务JSON的读取测试，断言数量、顺序、规范化及默认值，之后补文件和结构错误。

2026-10-17读取函数修正通过静态核对：逐项调用LegacyTaskInput.model_validate(item)，其余流程符合当前要求。本轮未运行新增读取测试或重跑模型测试。下一步先讲tmp_path内置fixture、Path拼接及文件生命周期，再由学习者用open/json.dump写临时[]，调用load_legacy_tasks断言返回[]；随后补正常记录、格式/类型异常和重复旧ID检查。

2026-10-17读取函数复核：循环现为LegacyTaskInput(item)，仍未调用model_validate。该写法将字典作为位置参数传给BaseModel构造器，正常记录也会TypeError；应改为LegacyTaskInput.model_validate(item)。本轮仅静态检查，暂不推进tmp_path实现或重跑不覆盖读取函数的36项模型测试；修正后再验收读取路径。未代写代码。

2026-10-17读取函数静态核对：只读UTF-8、顶层列表检查、返回列表及异常传播符合要求；循环使用LegacyTaskInput(**item)，对正常字典可用，但非映射元素会先在Python参数展开阶段抛TypeError，绕过Pydantic输入检查。本小步要求改为LegacyTaskInput.model_validate(item)，统一由模型校验每项并使错误元素产生ValidationError。尚未完成读取函数运行测试；本轮未改代码或重跑无关模型测试。修正后再学习tmp_path临时文件测试。

2026-10-17当前验收：必填缺失测试已正确命名，显式空tags合法用例已补齐；独立模型测试36 passed，未加载conftest或访问数据库。本轮未代写代码。下一步由学习者在legacy_import.py类外实现load_legacy_tasks(file_path: Path)->list[LegacyTaskInput]：UTF-8只读json.load、顶层列表检查、逐项model_validate、完整返回。文件及校验异常暂原样传播；重复旧ID检查、错误定位和临时文件测试后续补充，不导入真实数据。

2026-10-17本轮验收：新增两个必填字段缺失用例正确，但误用函数名test_legacy_task_accepts_empty_tags；显式空tags合法测试仍未实现。独立模型测试35 passed，未连接数据库。下一步由学习者将该函数更名为test_legacy_task_rejects_missing_required_fields，再单独新增空列表合法测试；预计36项。本轮未代写代码，不能因现有测试通过就认定缺失场景已覆盖。

2026-10-17标签验收：六个非法tags参数均正确，助手运行独立模型测试33 passed，未连接数据库。文件中尚无test_legacy_task_accepts_empty_tags，因此此前计划34项未全部完成。下一步由学习者补显式空列表合法用例，再补缺失id/title的参数化用例；本轮未代写测试。

2026-10-17优先级验收：六种非法值及三种合法值的参数化测试实现正确；助手运行独立模型测试27 passed，未加载conftest或连接数据库。下一步补标签容器/元素/空白边界、显式空列表及必填缺失；本轮未代写测试。

2026-10-17标题边界验收：五种非法标题及恰好100字符合法标题用例实现正确。助手运行python -m pytest --noconftest tests/test_legacy_import.py -q，18 passed；未加载数据库夹具或连接数据库，本轮未修改测试代码。下一步补priority/tag及必填缺失，之后才进入读取JSON。

2026-10-17知识整理：已检索并合并自上次整理后的导入模型职责、after执行顺序、StrictStr与容器严格模式、默认值测试预期错误、12项参数化案例和--noconftest使用边界；model_validate调用与返回对象说明补入原有方法章节。仅维护文档，未重跑测试。当前继续位置仍为补标题、优先级、标签及必填缺失测试，不推进数据库写入。

2026-10-17非法id验收通过：六种参数均正确注入id、title合法、raises包住model_validate。助手运行独立模型测试12 passed，未加载conftest或连接数据库。本轮未修改测试实现；下一步仍是补其余模型边界，随后进入JSON读取与整批校验。

2026-10-17当前验收：非法done参数化输入及raises范围正确，助手执行python -m pytest --noconftest tests/test_legacy_import.py -q，6 passed；未加载数据库夹具或连接数据库。下一步由学习者复用相同模式补非法id（0、-1、"3"、3.0、True、None），保持title合法，其他字段用默认值。缺失必填字段及其余字段边界后续补充；本轮未代写代码。

2026-10-16当前验收：默认值测试已修正为done is False。助手运行python -m pytest --noconftest tests/test_legacy_import.py -q，2 passed；只运行模型测试，未加载数据库夹具或连接数据库。下一步导入pytest和ValidationError，用parametrize覆盖"false"、0、1、None，with pytest.raises(ValidationError)验证严格done拒绝非法输入；本轮未代写代码。

2026-10-16最新验收：默认值测试已添加，但误断言done is True；模型默认False符合需求，需学习者把断言改为is False。助手运行隔离模型测试文件，结果1 failed, 1 passed；本轮未修改测试代码。先修正测试预期并复验，再编写非法done参数化测试。未加载conftest或访问数据库。

2026-10-16当前验收：第一项正常数据测试正确使用model_validate返回实例，五字段断言覆盖清理标题、保留True、优先级小写及标签顺序去重。助手运行python -m pytest --noconftest tests/test_legacy_import.py -q，结果1 passed；未加载数据库夹具或连接数据库。这不是完整套件回归。下一步由学习者添加仅id/title输入的默认值测试，随后补非法done参数化；本轮未修改业务代码或测试实现。

2026-10-15 tags静态验收通过：Field(default_factory=list, strict=True)、list[StrictStr]及after小写/空白拒绝/顺序去重符合要求；strip由模型配置作用于字符串元素，因此无需要求重复添加strip。验证器以list[str]标注也可，当前list[StrictStr]不影响正确性。本轮未运行测试或代写代码。下一步由学习者新建tests/test_legacy_import.py，先写完整合法数据规范化、缺失字段默认值、非法done参数化三组测试，后续再补其他字段边界和读取流程。

2026-10-15 priority静态验收通过：strict=True、默认normal、after验证器strip/lower、非法值ValueError、成功返回字符串均正确；额外strip与全局配置重复但不影响正确性。本轮未运行测试或代写代码。下一步解释容器strict不自动递归到元素，使用list[StrictStr]与Field(default_factory=list, strict=True)，由学习者编写after标签清理/空白拒绝/顺序去重验证器；尚未实现读取JSON或数据库写入。

2026-10-15当前核对：id已移除min_length，仅保留strict=True和gt=0，静态验收通过。已将长度/数值约束、严格整数拒绝bool及源ID用途合并进知识章节；本轮未运行测试或修改业务代码。下一步priority使用严格str和normal默认值，after字段验证器清理并转小写后校验low/normal/high；先解释执行顺序再由学习者实现。

2026-10-15导入模型静态验收：title为必填严格字符串、strip后长度1～100；done为严格bool且默认False，均符合要求。本轮未运行测试或代写代码。下一步讲解Field(gt=0)并由学习者添加必填id，严格整数、正数、无默认值；旧id用于源记录识别和后续映射，不传入数据库identity。随后补其余字段并安排模型测试。

2026-10-15导入导学：已读取旧模型/storage与Service/Repository。初步范围为单次导入、任务空目标库、数据库新ID、保留done与标签、整批失败回滚、不改源文件。学习者已理解转换与严格校验的区别，缺失done由校验模型补False，字符串/数字/null拒绝。已将内容整理进笔记。下一步讲解Field(strict=True)，由学习者新建legacy_import.py，仅编写LegacyTaskInput的title和done两字段；其他字段、读文件及数据库写入逐步补充。本轮仅文档更新，未运行测试或写业务代码。

2026-10-15 Git收尾：用户明确授权按两个提交方案执行。本地功能提交138df49（feat: add Alembic migrations and task timestamps）已完成，包含迁移、模型、依赖、数据库选择及README；同时清除初始迁移文档字符串的一处尾随空格。教学规则、笔记及本进度随独立文档提交保存，完成后以git log和工作区状态核验。未合并、打标签或推送。下一学习项为旧JSON数据导入，先检查现有数据格式、导入范围和重复执行规则，再小步设计；本次不重复运行已由用户确认49 passed的测试。

2026-10-15收尾：用户报告在测试库运行pytest为49 passed，作为本次回归证据记录，不是助手重跑。已补README数据库选择、新库迁移、已有库接管、版本链、时间语义和测试说明。本轮仅修改文档，未运行测试或提交Git。下一步审阅本轮变更并讨论合理提交；旧JSON导入为后续新学习小节。created_at当前仅在存储层，不宣称已加入API响应。

2026-10-15最新验收：用户确认原库第二版升级及current/check、原任务保留、created_at非空均符合预期，依据用户报告。助手本轮读取tests/conftest.py，确认数据库夹具绑定database.engine，以外层事务和create_savepoint隔离并回滚测试写入。下一步终端指定task_manager_migration_test运行python -m pytest -q，验收已有功能回归；此前49 passed仍为历史结果。尚未更新README迁移使用说明或执行Git提交。

2026-10-15当前起点：第二版测试库往返及再次升级后的时间补值和check均由用户确认通过。已合并自上次整理后的原库stamp验收、datetime/DateTime、CURRENT_TIMESTAMP、自动生成迁移、add/drop_column、指定版本回退及时间丢失边界。本轮只核对文件和更新文档，未执行数据库命令或测试。下一步明确切换原库、确认current为042f491f9a4a后执行第二版upgrade，再current/check及GUI核对任务保留和时间补值；原库不做回退实验。

2026-10-15第二迁移测试进展：用户确认测试库upgrade head及旧任务id=1补值、新任务自动记录时间均符合预期，依据文字报告，助手未重跑。下一步由用户在同一测试库终端执行current（预期f959d63045e7 head）和check（预期无新增操作）；之后安排仅回退第二个迁移的验证。原库仍停留初始基线，尚未执行第二迁移。本轮仅源码检查和进度更新，未运行测试或迁移。

2026-10-15第二迁移审查：用户截图显示Detected added column tasks.created_at，文件f959d63045e7_add_task_created_at.py与预期一致，无额外结构变更。已读取源码，未运行迁移或测试。下一步解释add_column/drop_column参数及副作用，并在指定测试库使用原始SQL插入迁移前任务；暂不通过含新字段的ORM访问未升级库。之后才执行测试库升级并验证旧记录保留、时间补值和新任务默认时间，原库暂不升级。

2026-10-15当前静态验收：created_at声明和datetime/DateTime导入符合要求，历史任务时间只能补迁移事务时间的边界已讲解。版本目录仅有初始迁移；本轮未运行测试或连接数据库。下一步讲解revision --autogenerate调用链，由用户指定测试库运行revision --autogenerate -m "add task created_at"，只生成文件不升级；审查后再验证，原库暂不执行新迁移。

2026-10-15最新结果：用户确认原库stamp 042f491f9a4a、current显示head、check无待迁移操作，基线接管完成。下一步导入datetime/DateTime并解释时区时间列及CURRENT_TIMESTAMP，先确认历史任务时间不可还原的边界，再安排模型修改、自动生成迁移、审查及测试库验证。初始迁移保留为历史版本，不回写新增列。本轮未运行数据库命令或测试。

2026-10-15当前任务：已讲解stamp只登记版本、不核对或修复结构；学习者理解compare_metadata空列表的含义。已将MigrationContext与env.py代理context的区别、比较参数职责及只读检查流程合并进知识文档。下一步由学习者运行此前临时检查代码，局部变量统一用migration_context，目标原库task_manager_learning；期待Database正确且Differences: []。原库比较尚未执行确认，禁止提前stamp。本轮仅文档更新，未连接数据库或运行测试。

2026-10-15最新结果：用户报告测试库alembic check输出No new upgrade operations detected；这是用户执行的结构比较，不是助手重跑或完整pytest结果。测试库流程完成到自动差异检查；原库task_manager_learning的结构比较及stamp尚未进行。下一步先解释已有库为何使用stamp而非重复upgrade，确认理解后安排原库只读结构核对；不得先登记版本再以check代替登记前核对。

2026-10-15当前静态验收：priority已改为server_default=text("'normal'")，本轮模型修正通过。尚未运行测试或连接数据库。下一步由学习者在run_migrations_online的context.configure中添加compare_server_default=True，再在指定测试库的终端运行alembic check。需先解释check比较实际结构与metadata、不生成文件或修改表、存在自动比较局限；结果待用户执行后核对。

2026-10-15本次静态验收：两处Identity(always=True)、done的server_default及保留Python侧default均正确；priority的server_default=text("normal")缺少SQL字符串单引号，应为text("'normal'")。已将本次错误合并进默认值知识章节，未代写源码、未运行测试或连接数据库。下一步由学习者修正这一处，随后启用数据库默认值比较并学习结构差异检查。

2026-10-15最新进度：测试库回退截图显示downgrade成功、current无版本号；用户随后确认再次升级/current及三张业务表恢复均符合预期。此为用户手动验证，不是新增自动化测试，助手本轮未连接数据库。源码核对发现TaskRecord/TagRecord的id仍未声明Identity，done/priority仍仅有Python侧default。下一步先讲解模型与真实结构对齐的原因，用小问题确认后再安排局部修改；不得把迁移往返成功等同于原库基线已登记。

2026-10-15当前起点：已将数据库选择、终端环境变量作用范围、真实连接目标查询、scalar_one、资源清理及在线迁移验收合并到学习文档。证据为用户连接/升级/current截图及GUI结构符合预期的文字确认，助手本轮仅核对源码和更新文档，未运行测试或迁移。下一步在明确指定的测试库执行downgrade base，检查版本清空和业务表移除，再upgrade head确认重建；原库数据不参与此实验。

以下为历史过程记录，当时的“下一步”和状态由上方当前起点取代。

2026-10-14当前起点：两次用户截图分别确认upgrade head --sql及downgrade 042f491f9a4a:base --sql正常输出。回退输出删除三表及版本记录，未删除版本表；离线验收通过不代表真实数据库变化。本轮核对database.py仍固定连接task_manager_learning，env.py从它导入database_url并覆盖ini连接地址。下一步先讲解os.getenv读取数据库名的方案，检查理解后由学习者修改；尚未创建测试库、修改连接代码或运行在线迁移。

2026-10-14最新静态核对：downgrade按task_tags、tasks、tags顺序调用drop_table，符合外键依赖关系。回退原理已合并到学习文档，未代写源码、未运行测试或实际回退。下一步先讲解`alembic upgrade head --sql`的调用链与只生成SQL的边界，再由学习者执行离线预览；当前env.py导入database.py，离线也需要已有密码环境变量。完整在线隔离验证、模型元数据对齐和基线登记仍待完成。

2026-10-14最新检查：task_tags的两列、外键目标、ON DELETE CASCADE、联合主键及创建顺序均正确；省略nullable=False不影响主键非空规则。本轮仅静态检查和知识整理，未运行测试、未修改迁移源码。下一步讲解op.drop_table后由学习者编写downgrade，先task_tags，再tasks和tags；只编写，不对当前数据库执行回退。之后仍需完整基线验证及ORM元数据对齐。

2026-10-14当前验收：学习者已将tasks的两个默认值修正为server_default。临时离线PostgreSQL SQL生成断言通过，覆盖两张表、两列Identity、title非空、done DEFAULT false、priority DEFAULT 'normal'及标签唯一约束。未连接数据库、未运行pytest或真实迁移，未修改学习者代码。下一步在两张父表之后编写task_tags，使用联合主键及两个ON DELETE CASCADE外键；downgrade留待下一小步。

2026-10-14增量：tags建表部分已由学习者实现，代码核对及临时离线SQL断言通过，覆盖Identity ALWAYS、主键、name非空与唯一约束。知识合并到现有Identity章节，未代写迁移代码、未连接数据库、未运行pytest、未执行upgrade或stamp。此前只读核对已确认三表真实结构。下一步先讲解server_default与Python侧default的区别，再由学习者填写tasks；仍需完成task_tags、downgrade、ORM元数据对齐及完整基线验证。

2026-10-14 首个迁移骨架核对：文件042f491f9a4a_create_initial_task_tables.py已生成，revision正确、down_revision/branch_labels/depends_on为None，upgrade/downgrade均为pass。已把revision/upgrade/stamp区别、版本标识、op与context区别和create_table局部示例整理进知识文档。本轮仅文件核对与文档更新，未运行迁移。继续讲解骨架与建表API，随后读取真实数据库结构，核对identity、默认值和约束，再让学习者小步填写；不对现有业务表直接执行空骨架或重复建表。

2026-10-14 context知识整理与连接验收：将代理模块、EnvironmentContext/MigrationContext职责、常用方法，以及set_main_option修改配置和configure配置迁移环境的区别合并进知识文档。首次current因缺少TASK_MANAGER_DB_PASSWORD而在导入database.py时抛KeyError；学习者在同一PowerShell设置变量后，截图显示PostgresqlImpl与事务DDL日志并正常返回提示符，没有版本号。证据来自用户截图，助手本轮未重跑。versions目录仍为空；下一步通过普通revision创建空白基线骨架，先讲解再填写并审查，禁止把空骨架直接当作完成的基线登记。

2026-10-14 事务与配置补充：学习者能解释异常时先回滚内层事务、再关闭外层连接。已将异常继续传播、回滚范围、str.replace参数与返回值、URL编码和ConfigParser百分号转义合并进已有知识章节。只读核对env.py确认百分号转义已补齐，本轮仅修改文档；下一步由学习者在已设置数据库密码环境变量的终端运行alembic current，并提交输出供验收，暂不创建或执行基线迁移。

2026-10-14 Alembic执行流程增量整理：将在线/离线分支、get_section、engine_from_config、NullPool、Engine.connect、连接清理与事务提交的区别，以及configure参数合并到已有知识章节，并补充本轮事务块与run_migrations讲解。学习者能够解释metadata赋值不会改表、Engine创建成功不证明数据库可达。源码已接入URL和metadata但尚未验证；下一步检查对事务和命令分派的理解，再补足URL百分号转义、验收alembic current。此次仅更新文档，无数据库操作或测试。

2026-10-14 Alembic文档整理：保留已有Base.metadata笔记，将入门、INI语法、路径基准、Config对象与方法、current的含义、日志配置和target_metadata逐段说明合并到get_knowledge.md。纠正“所有命令都会运行env.py”、current查看结构及URL百分号转义的表述；长期教学规范补充以实际执行链展开讲解。已安装和初始化的依据为此前工具结果及本轮源码核对；env.py仍为模板，未执行数据库连接验收或迁移。侧边栏临时对话原文不可访问，仅整理了本对话和现有笔记可见内容，未纳入文档的临时对话需用户补充。下一步讲解target_metadata，随后继续连接创建与事务，理解后再由学习者配置env.py。

2026-10-13 Git阶段检查点：在进入Alembic前清理了长期混杂的暂存状态，并按职责形成三个本地提交：`2a2d080 chore: organize database learning examples`、`a68ace5 feat: migrate task API to PostgreSQL`、`0b73591 docs: update database learning progress`。提交前完整套件实际结果为`49 passed in 0.84s`，代码空白检查和文档敏感信息检查通过；未执行push。下一步开始Alembic数据库结构迁移导学与实操。

2026-10-13 正式部分更新接口迁移验收：`PATCH /tasks/{task_id}`已通过数据库Session构造Repository与Service，使用`model_dump(exclude_unset=True)`保留部分更新语义，由Router把Service的`ValueError`转换为400、缺失任务转换为404，并在成功路径提交和刷新ORM对象。隔离测试覆盖只修改标题时保留其他字段、同时更新并规范化标题/优先级/标签、标签去重、再次GET确认持久化、缺失ID，以及显式null、非法优先级和空白标签三类400响应。首次验收发现测试模块导入另一个`test_`函数导致pytest重复收集、缺失请求体先触发422，以及主流程误用非法优先级而未覆盖合法完整更新；修正后完整套件实际结果为`49 passed in 1.47s`。至此正式七个任务接口已全部迁移到PostgreSQL。下一步清理`task_routes.py`残留的旧JSON依赖导入，核对正式运行路径不再访问JSON，并同步README。

2026-10-13 Service部分更新验收：`TaskService.update_task()`接收由`exclude_unset`产生的更新字典，区分未提供字段与显式`None`，规范化标题、优先级和标签，去重并复用标签，允许`tags=[]`清空关联；缺失任务返回`None`，不在Service提交事务。直接测试覆盖只改标题时保留其他字段、同时更新全部字段、缺失ID、显式null、非法优先级、空白标签和清空标签。首次测试把`list[TagRecord]`与`list[str]`比较，又直接调用预期抛错的方法导致后续代码不可达；改用标签名称列表和独立`pytest.raises()`后，完整套件实际结果为`45 passed in 0.71s`。下一步用该Service替换正式`PATCH /tasks/{task_id}`的JSON/TaskManager逻辑，并覆盖成功、404与400响应。

2026-10-13 正式删除接口迁移验收：`TaskService.delete_task()`通过Repository查询任务并调用不提交事务的删除方法；正式DELETE路由负责404转换和`commit()`，不对已删除对象调用`refresh()`。隔离测试验证删除响应保留原任务ID、标题和标签，后续详情返回404，缺失ID删除也返回准确404。完整套件实际结果为`44 passed in 0.90s`。当前仅正式部分更新接口仍依赖JSON；下一步先在Service实现基于`exclude_unset`字典的部分更新规则与直接测试，再迁移Router。路由局部变量`delete_task`与函数同名，后续编辑时建议改为`deleted_task`以提高可读性。

2026-10-12 Repository删除方法验收：`TaskRepository.delete_task()`接收当前Session管理的`TaskRecord`，调用`Session.delete()`和`flush()`但不提交事务。直接测试验证删除后按ID无法查询任务，同时原标签仍存在。首次测试先单独插入标签，又为任务创建第二个同名`TagRecord`而触发唯一约束；改为任务复用同一个标签对象后，完整套件实际结果为`43 passed in 0.81s`。下一步增加`TaskService.delete_task()`，让正式DELETE路由负责404转换和提交，并验证删除响应、后续详情404及缺失ID。

2026-10-12 正式完成任务接口迁移验收：`TaskService.complete_task()`通过Repository读取任务，缺失时返回`None`，存在时依靠Session脏对象跟踪把`done`设为`True`；正式Router负责404转换、`commit()`、`refresh()`及响应。隔离测试覆盖创建时未完成、PATCH后完成、再次GET仍为完成以及缺失ID返回404。首次实现虽然行为测试通过，却在Router直接调用`get_task()`并修改`done`，导致新增Service方法未使用；修正职责后完整套件实际结果为`42 passed in 0.93s`。下一步迁移删除接口，先为Repository增加使用`Session.delete()`且不提交事务的删除方法与直接测试。

2026-10-12 正式统计接口迁移验收：`TaskService.get_stats()`委托Repository执行单条聚合查询；正式`GET /tasks/stats`改用数据库Session、Repository和Service，且静态`/stats`保持在动态`/{task_id}`之前。路由测试以三次快照验证创建前基线、创建未完成任务后的总数与未完成数变化、转为已完成后的已完成数与未完成数迁移。首次测试误用不存在的`test_client` fixture、误断言创建状态码为200，并在取得中间统计前完成任务；第二版又从创建响应读取不存在的统计键并写反最终增量；修正后完整套件实际结果为`41 passed in 0.64s`。下一步迁移正式`PATCH /tasks/{task_id}/complete`，由Service修改ORM状态、Router提交事务并覆盖成功及404测试。

2026-10-12 Repository统计查询验收：`TaskRepository.get_stats()`使用一条聚合查询返回`total`、`completed_num`和`uncompleted_num`，其中已完成与未完成数量分别通过聚合函数的`filter(...is_(True/False))`计算。直接测试先记录基线，再插入一条已完成和一条未完成任务，以差值断言三个计数。首次测试误写不存在的`Session.add_()`，并使用了与返回字典不一致的键名；修正后完整套件实际结果为`40 passed in 0.56s`。下一步增加`TaskService.get_stats()`委托方法，迁移正式`GET /tasks/stats`并增加路由级隔离测试。

2026-10-12 正式列表错误响应验收：正式路由参数化测试覆盖非法priority、空白keyword和空白tag，确认Service的`ValueError`经Router统一转换为HTTP 400及准确detail；另验证无法解析的`done`由FastAPI在进入Service前返回422。完整套件实际结果为`39 passed in 0.54s`。下一步迁移正式统计接口：先把单条聚合统计查询提取到Repository，并通过测试前后差值直接验收，不依赖练习数据库原有任务总量。

2026-10-12 正式列表接口迁移验收：正式`GET /tasks`已删除基于JSON、`TaskManager`和Python循环的筛选逻辑，改为通过数据库Session构造Repository与Service，返回ORM列表，并把Service的`ValueError`转换为HTTP 400。正式路由隔离测试通过POST准备三条数据，使用同一`database_session`把B改成已完成，再验证大小写与空白规范化后的四条件AND只返回A。首次测试误把`TestClient`当作Session调用ORM版`get()`和`flush()`，且准备的数据不满足查询关键词和标签；区分两个fixture并修正数据后，完整套件实际结果为`35 passed in 0.52s`。下一步补充正式列表路由的非法priority、空白keyword、空白tag及无法解析的done响应测试。

2026-10-12 Service列表筛选验收：`TaskService.list_tasks()`负责规范化`priority`、`keyword`和`tag`，校验允许的优先级及空白关键词/标签，并将`done`原样传给Repository。直接测试覆盖大小写与空白清理、四条件AND及三类非法输入。首次Review发现合法筛选测试与参数化非法测试同名，导致前者被Python后定义覆盖，同时把`done=false`的包含/排除断言写反；修正后完整套件实际结果为`34 passed in 0.46s`。下一步用该Service替换正式`GET /tasks`中基于JSON和`TaskManager`的列表筛选逻辑，并增加正式路由隔离测试。

2026-10-11 Repository完整列表筛选验收：`TaskRepository.list_tasks()`现支持`priority`、`done`、`keyword`和`tag`四个可选条件；关键词通过`ilike`进行不区分大小写的包含匹配，标签通过关系属性的`any()`生成存在性条件，多项条件连续追加形成AND。直接测试覆盖关键词、标签以及关键词与标签组合。首次测试为B、C各构造一个同名`TagRecord`而触发`tags.name`唯一约束，改为共享同一个标签对象，正确表达多对多关联后，完整套件实际结果为`30 passed in 0.48s`。下一步在`TaskService`中增加列表方法，负责优先级、关键词和标签的规范化及非法输入校验，再把已清理参数传给Repository。

2026-10-11 Repository列表基础筛选验收：`TaskRepository.list_tasks()`新增可选`priority`与`done`参数，按已提供条件逐项追加`WHERE`并保留标签预加载和ID升序；`done`使用`is not None`判断，能够正确处理显式`False`。新增直接测试覆盖`priority="high" AND done=false`以及单独`done=false`。首次Review发现测试函数误写为`teest_`而未被pytest收集，并在`flush()`前保存尚为`None`的ID；修正后完整套件实际结果为`30 passed in 0.46s`。下一步为Repository加入已规范化的`keyword`与`tag`筛选及直接测试，输入清理和非法值仍留给Service。

2026-10-11 正式详情接口迁移验收：`TaskService.get_task()`委托Repository按主键读取；正式`GET /tasks/{task_id}`通过数据库Session构造Repository和Service，返回ORM对象并由`TaskResponse`序列化，缺失任务转换为404。正式路由测试在隔离事务内先创建任务，再用返回ID读取详情，并独立验证不存在ID；Review中先后发现误断言POST响应和误对JSON字典读取`status_code`，修正为检查`detail_response.status_code`。完整套件实际结果为`29 passed in 0.55s`，测试标题残留计数为0。下一步迁移正式列表查询，先扩展Repository的可选筛选能力并进行直接测试，再改Service和Router。

2026-10-11 正式创建接口pytest验收：`tests/conftest.py`使用`task_app`与`database_app`区分正式应用和演示应用，新增`task_client`复用`database_session`并覆盖正式应用的`get_session`。`tests/test_task_routes.py`验证正式`POST /tasks`的201状态、标题与优先级规范化、默认未完成状态及标签规范化去重；标签关系未定义返回顺序，因此测试使用`sorted()`比较内容而不虚构顺序契约。完整套件实际结果为`28 passed in 0.48s`，测试标题残留计数为0。下一步迁移正式`GET /tasks/{task_id}`，让Router经Service和Repository读取数据库，并覆盖存在与不存在任务两种情况。

2026-10-11 正式创建接口迁移验收：`task_routes.py`中的`POST /tasks`已通过`Depends(get_session)`取得数据库Session，调用`TaskService`创建任务，并在请求边界执行`commit()`与`refresh()`；`TaskResponse`启用`from_attributes`，标签预处理器同时兼容旧JSON的`list[str]`与ORM的`list[TagRecord]`。静态编译通过，完整套件实际结果为`27 passed in 0.52s`。另用外层事务隔离调用正式接口，确认返回201，标题和优先级完成规范化、重复标签去重并转换为字符串列表；回滚后对应任务残留为0。当前属于渐进迁移状态：创建写入PostgreSQL，其余正式接口仍主要读取JSON。下一步先把这次临时正式接口验收固化为pytest隔离测试，再迁移正式任务详情查询。

2026-10-11 TaskService自动化测试验收：新增`tests/test_task_service.py`，直接使用`database_session`覆盖合法创建、标题/优先级规范化、标签去重、已有标签对象复用、默认值，以及通过`pytest.raises()`参数化验证空标题、非法优先级和空标签。首次运行因把`list[TagRecord]`与`list[str]`比较而失败，改为提取标签名称，并用`is`验证复用同一ORM对象后，完整套件实际结果为`27 passed in 0.59s`；任务和标签残留计数均为0。`get_knowledge.md`已详细补充`pytest.raises()`的参数、上下文行为、`match`正则、异常信息对象，以及`is`与`==`在ORM身份验证中的区别。下一步迁移正式`POST /tasks`：先整理可复用的请求/响应模型，再让路由调用`TaskService`并在请求边界提交事务。

2026-10-11 TaskService创建流程验收：新增`task_service.py`，由Service负责标题、优先级和标签规范化、去重、已有标签复用及新标签构造，并通过Repository执行`add + flush`，不在Service或Repository内部提交。首次验收先发现误用`TaskRecord(tag)`及缺少去重；修正后又复现“持久TagRecord关联transient TaskRecord，后续查询触发autoflush”的`SAWarning`。最终改为先收集`list[TagRecord]`、结束全部查询后一次性赋给`task.tags`。临时验收将`SAWarning`提升为异常，覆盖默认创建、大小写与空白清理、重复标签、已有标签复用及三类非法输入，全部通过；完整套件为`23 passed in 0.39s`，任务和标签残留计数均为0。警告原因和解决方式已合并到`get_knowledge.md`。下一步把临时Service验收转为`tests/test_task_service.py`中的可重复隔离测试。

2026-10-11 Repository标签查询验收：`TaskRepository.get_tag_by_name()`使用`select(TagRecord)`与精确名称条件，通过`Session.scalar()`返回`TagRecord | None`；新增直接Repository测试覆盖已存在与不存在标签。完整套件实际结果为`23 passed in 0.43s`，测试标签计数为0，确认事务回滚正常。下一步建立正式迁移使用的`TaskService`，先组织创建任务时的标题、优先级和标签业务规则，再调用Repository完成数据库写入；最终提交仍留在请求事务边界。

2026-10-11 Repository创建方法验收：`TaskRepository.add_task()`接收`TaskRecord`，执行`Session.add()`与`flush()`并返回同一ORM对象，不在Repository内部提交事务。新增直接Repository测试，验证返回对象身份、数据库生成ID、默认`done=false`及重新按ID查询；完整套件实际结果为`22 passed in 0.51s`，测试标题对应记录数量为0。`get_knowledge.md`已补充Repository写入、`flush()`与上层`commit()/rollback()`的事务职责边界。下一步实现按规范化名称查询标签的`get_tag_by_name()`，为后续Service复用已有标签做准备。

2026-10-10 Repository直接测试验收：新增`tests/test_task_repository.py`，直接注入`database_session`，构造带标签的`TaskRecord`并以`flush()`取得ID，验证`list_tasks()`按ID升序且包含新任务、`get_by_id()`返回任务属性与标签、缺失ID返回`None`。首次运行因把`list[TagRecord]`误当作`list[str]`导致1项失败，改为提取`tag.name`后完整套件实际结果为`21 passed in 0.50s`；测试任务和标签计数均为0，确认断言失败与成功场景都被回滚。下一步为Repository增加不提交事务的`add_task()`，明确Repository写入和上层事务提交的职责边界。

2026-10-10数据库fixture拆分验收：`tests/conftest.py`已将Connection、外层事务、Session与最终回滚提取到`database_session`，`database_client`通过fixture依赖复用同一个Session并只负责FastAPI依赖覆盖和TestClient。语法修正后完整套件实际结果为`20 passed in 0.36s`；四类代表性pytest任务标题在测试后计数均为0，确认拆分未破坏事务隔离。已讲解原始单fixture结构、三个`yield`分别所属的pytest/FastAPI生命周期、依赖解析及逆序清理。下一步新增`tests/test_task_repository.py`，直接注入`database_session`测试Repository的列表与主键查询。

2026-10-10 Repository只读查询验收：新增`task_repository.py`中的`TaskRepository`，实现按ID升序并预加载标签的`list_tasks()`，以及使用`Session.get()`和`selectinload()`的`get_by_id()`。首次Review发现误导入标准库`select.select`、排序调用位置错误、`Session.get()`参数错误及尝试对ORM对象调用`.json()`；学习者修正后，真实只读检查返回2条任务，存在ID返回含`python`、`database`标签的ORM对象，不存在的`-1`返回`None`，关闭Session后仍能读取预加载标签。完整套件实际结果为`20 passed in 0.28s`。`get_knowledge.md`已补充`Session.get()`、`TestClient.get()`和`Response.json()`在对象类型及HTTP边界上的区别。下一步将数据库Session提取为可复用fixture，直接为Repository编写隔离测试。

2026-10-10统计接口测试验收：新增`tests/test_database_stats.py`，以接口调用前的统计结果为基线，验证创建未完成任务后`total`与`uncompleted_num`各增加1，以及完成该任务后`completed_num`增加1、`uncompleted_num`回到基线。首次运行因错误读取创建响应而出现`KeyError: 'total'`，修正响应变量及完成接口路径后，完整套件实际结果为`20 passed in 0.46s`、无warning；测试标题对应的数据库记录数量为0，确认失败和成功场景均由fixture回滚。下一步恢复正式项目数据库迁移，先建立数据库访问层并迁移只读查询。

2026-10-09学习决策更新：学习者决定恢复并完成统计接口的pytest隔离回归测试，暂缓开始Repository迁移。当前任务是在`tests/test_database_stats.py`中通过测试前后差值验证创建未完成任务、完成任务所引起的`total`、`completed_num`和`uncompleted_num`变化；验收后再建立数据库访问层并迁移正式项目的只读查询。

2026-10-09最新验收：完整pytest结果为`19 passed`、无warning。标签测试验证查询参数大小写和首尾空白规范化、任务不重复、响应保留全部标签；keyword/tag空白参数化案例分别验证400及准确detail。此前priority/done组合过滤也继续通过。下一步补充统计接口的隔离回归测试，通过测试前后统计差值验证创建和完成操作，避免依赖练习数据库已有数据总量。

2026-10-09过滤测试验收：新增priority与done组合过滤测试，完整套件实际结果为`16 passed`、无warning；验证返回任务均满足条件，A被返回、B和C被排除。随后完成接口路径去除末尾斜杠，代码核对正确，本次未重跑。下一步在同一测试模块增加标签规范化过滤测试，验证大小写及首尾空白清理、返回完整标签列表和任务不重复。

2026-10-09共享fixture迁移验收：`database_client`已移入`tests/conftest.py`，数据库测试文件通过同名参数自动获取fixture，完整套件实际结果为`15 passed`、无warning。已讲解fixture可见范围与生命周期的区别、顶层导入对环境变量的影响。下一步新建`tests/test_database_filters.py`，复用fixture测试priority与done组合过滤，并用本次创建的任务id验证结果，避免依赖练习数据库原有总量。此前目录整理与依赖处理记录作为历史证据保留。

2026-10-09目录整理完成：13个独立数据库实验已移入`examples/database/psycopg/`（3个）与`examples/database/sqlalchemy/`（10个），保留原文件名和内容。公共数据库实现与演示API仍位于根目录，自动化测试保留在`tests/`。新增包标记及运行指南，统一从项目根目录按模块运行；旧PyCharm脚本路径配置需要更新。13个脚本的语法和模块定位检查通过，完整pytest实际结果为`15 passed`、无warning；未批量执行会写入数据的教学实验。文件移动未暂存或提交。下一步继续学习`conftest.py`。

继续完善pytest测试基础。2026-10-09验收：`tests/test_database_api.py`的3条数据库工作流测试与3组非法priority参数化案例全部通过；已安装并记录`httpx2==2.13.1`，消除Starlette/TestClient的httpx弃用warning。完整套件随后发现模块级`test_app`被pytest误收集，将辅助FastAPI实例改名为`demo_app`后，最终结果为`15 passed`且无warning。下一步学习`conftest.py`的自动fixture发现规则，并判断哪些fixture应跨测试模块复用。

### 阶段四最终验收标准

- 能解释任务、标签与关联表的设计，并独立写基本 SQL。
- 能用 SQLAlchemy 支撑既有 API，解释 Session、提交和回滚。
- 能演示多步数据库操作失败时不会留下部分结果。
- 能通过迁移增加字段，并验证旧 JSON 数据导入。
- 能独立编写和重跑隔离测试，定位失败原因。
- 能启动容器化项目，解释数据库连接与数据保存位置。
- 能独立完成一个新字段或新关系需求的设计、实现、迁移、测试与 Git 流程。

## 6. 调整后的路线与投递准备（2026-10-07确认）

原外部路线只掌握阶段三结束时的上下文；本路线从当前阶段四成果继续，不照搬全部技术清单。

### 优先级

| 优先级 | 范围 | 交付要求 |
| --- | --- | --- |
| P0共同基础 | Python、HTTP、SQL、PostgreSQL、事务、pytest、Linux、Docker | 能开发、测试、排错并运行后端 |
| P0主投项目 | LLM API、结构化输出、基础RAG、工具调用Agent | 可演示、可解释，有测试或评估依据 |
| P1 Java备选 | Java核心、Spring Boot、数据库访问、测试 | 固定但有限投入，完成独立小项目；冲突时保证主线 |
| P1按需求扩展 | Redis、混合检索、Rerank、LangGraph、MCP基础 | 明确需求或失败案例后引入 |
| 延后 | Go、MQ/RPC实验、复杂微服务、Kubernetes深入、分布式系统、大型可观测性及复杂CI/CD | 不作为本轮投递前置条件 |

P0表示优先保障，不表示已经学会，也不保证按日期全部达成；时间不足先缩减扩展范围。MQ/RPC不再以“至少一个实验”形式隐性强制。AI/ML系统课程及阶段8、9保留长期方向，原70/20/10比例不再作为当前执行安排。

### 主线顺序和阶段成果

1. **阶段四收束**：利用已有演示API完成正式数据库后端、隔离测试、迁移和运行交付，避免重学已有内容。
2. **阶段五AI Task Manager**：自然语言→LLM→结构化任务→验证→数据库。学习Prompt、Context、Token、JSON Schema、流式响应及async/await，结合调用解释阻塞、协程、线程、并发与并行。先形成能用的最小闭环。
3. **阶段六Personal RAG**：文档解析、分块、Embedding、检索、生成带来源的回答；建立固定评估问题集并记录失败案例。理解分块大小、重叠、Top-K、元数据过滤；混合检索和重排序根据检索问题增加，不阻塞第一版。
4. **阶段七工具调用Agent**：从少量工具起步，理解工具定义、参数验证、调用循环、状态及上下文管理。验收工具失败处理、调用次数限制、修改任务操作的控制和完成判断；先能解释循环，再考虑LangGraph与MCP。
5. **投递准备**：独立实现与复现、项目说明、失败案例、设计取舍、简历和模拟面试并行收束，不等技术清单全部学完才开始准备。

争取11月底前有完整可运行的AI版本，便于考试期维护；这是目标而非对RAG/Agent全部完成的保证。

### Java备选路线

- 先短时摸底，再按缺口恢复类/对象、接口、集合、异常、泛型、Lambda/Stream；后续结合项目学习Maven、线程/线程池和JVM基础认知。
- 阶段四基本闭环后安排缩小的Spring Boot项目，复用任务管理领域知识；覆盖Controller、请求验证、异常、Service、数据库访问及基础测试。
- 数据访问工具在MyBatis/MyBatis-Plus中按实际选择，不同时学习两套；MySQL结合该备选项目学习，并比较与PostgreSQL的差异。
- 验收不仅是四个CRUD端点可运行，还要能独立解释请求到数据库的过程、事务和错误处理。
- Pydantic是库，DTO是对象角色；Repository与Mapper职责可以类比，不能视为严格等价。
- 当前Java摸底和项目均未开始。是否深入Java面试专题由剩余容量和实际目标岗位决定，小项目通过不等于已具备Java岗位全部能力。

### Redis、算法与CS基础

- Redis围绕具体缓存或临时状态需求引入，先学习实际用到的数据结构、TTL和缓存读写/失效；其他数据结构与穿透、击穿、雪崩按触发条件解释，不强行塞入Task Manager。
- 算法在另一个对话长期并行；100～150题仅为外部路线参考，不是硬性门槛。重点是间隔复现、复杂度解释和同类变形，结合实际遗忘情况安排复习。
- CS基础结合项目穿插：操作系统的进程/线程、网络的TCP/UDP、握手/连接关闭、TIME_WAIT、HTTP连接、TLS/DNS、数据库与Linux。要求用自己的话和实例解释，避免脱离项目同时铺开大量专题。
- 考试期降低新增量，在旧题复现、口述知识、阅读自己的代码、补小测试之间交替，不保持算法固定2小时再额外叠加工程学习。

### 投递前能力检查

- 能自行完成一个小需求的接口、数据库修改和测试。
- 能结合日志和调用链定位错误，说明事务边界及输入规则。
- 能解释项目设计取舍，区分实验、真实需求和暂未解决的限制。
- AI项目有可重复评估或测试、真实失败案例与改进依据。
- 在少量提示或查阅文档的情况下，能重新实现相似功能。
- 简历技术项有代码或实验支撑；按岗位分别标明准备程度，不把会话中跟写过等同于独立掌握。

### 教学过渡的当前安排

采用AGENTS.md中的渐进提示规则。先用列表过滤作为小范围过渡：口述流程，再判断需要的骨架。记录每次是否有提示、是否通过测试及后续复现结果，不因一次通过立即升级难度；遇到新技术仍先讲解。

### 寒假后的扩展方向

根据实际投递反馈再选择：偏Agent/AI基础设施时探索Go、Linux、容器、Kubernetes和分布式系统；偏传统后端时深入Java/JVM、MySQL、Redis、MQ。开源贡献及更复杂的部署、可观测性和CI/CD保留后续路线，不作为本轮延期理由。
