# 学习进度与阶段路线

> 更新日期：2026-10-13。路线依据本次讨论确认；实现状态依据源码和Git核对。最新pytest验收结果为`49 passed`，项目使用说明见README.md，长期导师规则见AGENTS.md，详细知识笔记见get_knowledge.md。

## 1. 当前继续位置

**阶段四：数据库演示API主要功能已实现并逐项测试；正式任务接口已全部从JSON迁移到PostgreSQL，下一步进行迁移收尾与工程化。**

- 阶段三已完成并发布v3.0.0；保留此前发布证据，本次未重新访问远程。
- 2026-10-07核对：当前分支feature/database，HEAD为5ef3064（文档重组提交）；数据库学习文件存在暂存及未暂存修改，知识笔记等文件未跟踪。不能把工作区实现当作已提交或已发布。
- 已完成SQL、PostgreSQL、Psycopg、SQLAlchemy基础、ORM关系、事务实验及FastAPI数据库依赖接入。
- database_api_demo.py已实现列表、详情、创建、部分更新、删除、完成任务；创建和更新支持标签清理、复用及关联。
- 列表的priority、done、keyword和tag动态过滤已实现并通过隔离测试；数据库统计接口用一条聚合查询返回总数、已完成数和未完成数，混合数据与事务隔离空表场景均已验证。
- database.py提供Engine、SessionFactory和get_session；orm_models.py提供任务、标签和中间表映射。
- 正式Task Manager的创建、详情、列表、统计、部分更新、完成与删除接口均已改用Repository、Service和数据库Session，并有事务隔离的正式路由测试；旧依赖清理、README同步、Alembic、旧JSON数据导入、Docker交付及阶段独立验收待完成。
- 恢复时先让学习者用中文说明列表过滤流程，再根据困难提供适量提示；不重新开始阶段三或重复已完成实验。

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
| Alembic 结构迁移 | 仅介绍用途 | 检查并执行增加字段等迁移 |
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
