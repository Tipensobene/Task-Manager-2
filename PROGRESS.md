# 学习进度与阶段路线

> 更新日期：2026-10-05。学习经历依据本对话及原 AGENTS.md 整理；版本状态依据本次 Git 核对。此文档记录学习进度，项目使用说明见 [README.md](README.md)，导师协作规则见 [AGENTS.md](AGENTS.md)。

## 1. 当前继续位置

**阶段四 Task Manager 4.0：已完成关系模型与 SQL 入门，正在从 PostgreSQL 实操过渡到 Python 连接。**

- 阶段三 API、标签功能、文档与版本发布已完成；v3.0.0 指向 c6c1667。
- 本次核对时位于 main，HEAD 与本地 origin/main 均为 c6c1667；此前已执行并核对远程主线及 v3.0.0 标签推送。本次没有重新访问远程。
- 2026-10-03 已讲解阶段四大纲与各项技术在业务系统中的作用。
- 已将 Task 映射为 tasks 表，并设计 tags 与 task_tags；理解主键、外键、联合主键、唯一约束和 ON DELETE CASCADE。
- 已学习并实际执行 SELECT、WHERE、AND / OR、ORDER BY、LIMIT、COUNT、GROUP BY、INSERT、UPDATE、DELETE、RETURNING、JOIN、LEFT JOIN、ARRAY_AGG、FILTER 和 COALESCE。
- 已安装 PostgreSQL 18.6，服务 postgresql-x64-18 正在运行；已创建独立练习数据库 task_manager_learning。
- 已在练习数据库创建 tasks、tags、task_tags 三张表，插入任务、标签和关联，并查询出带文本数组标签以及空标签数组的任务结果。
- pgAdmin 4 已切换为简体中文；psql 可通过安装目录运行，但其 bin 目录尚未加入 PATH。
- 下一步先提交此前文档重构，再创建阶段四开发分支，学习 Python 数据库连接与参数化查询。
- Docker 尚未安装，按阶段顺序留到后续运行交付小节。

## 2. 学习者背景与长期目标

计算机专业研一学生，已有 C/C++ 基础，以 Python 为 AI Agent / LLM 应用开发主语言；Python 基础仍需在项目中巩固。

目标是在 2027 年暑假前达到可投递 AI Agent、LLM 应用开发、AI 后端开发相关实习岗位的能力水平。关注独立编码、设计、调试、Git / Linux / 后端工程，以及后续模型应用能力。

功能验收通过说明相应行为在测试范围内符合需求，不等于全部知识都能独立运用。标签功能由学习者编写，经过多轮导师提示和修正；后续仍需用新需求检查迁移应用能力。

## 3. 阶段总览

| 阶段 | 项目或主题 | 实际状态 |
| --- | --- | --- |
| 0 / 1 | Python 基础与早期 Task Manager | 历史记录已完成 |
| 2 | Task Manager 2.0 Rebuilding + Git | 已完成并推送，保留 v2.0.0 |
| 3 | Task Manager 3.0：HTTP + FastAPI | 功能验收、文档、合并与 v3.0.0 推送完成 |
| 4 | Task Manager 4.0：数据库与工程基础 | 导学已讲解，实操待开始 |
| 5 | AI Task Manager：LLM API | 规划中 |
| 6 | Personal RAG | 规划中 |
| 7 | Research Agent | 规划中 |
| 8 | Production Agent | 规划中 |
| 9 | 开源项目阅读与贡献 | 规划中 |

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
| Python 连接与参数化查询 | 仅介绍用途 | 安全传递参数，区分连接和查询错误 |
| SQLAlchemy ORM / Session | 仅介绍用途 | 独立实现基本数据库 CRUD |
| 事务与 FastAPI 接入 | 仅介绍用途 | 多步失败不留下部分修改，原 API 正常 |
| 标签关系与查询 | 设计练习待开始 | 创建、更新、查询持久化的任务与标签 |
| Alembic 结构迁移 | 仅介绍用途 | 检查并执行增加字段等迁移 |
| 旧 JSON 数据导入 | 仅介绍与结构迁移的区别 | 可验证地导入任务和标签 |
| pytest | 仅介绍 assert、fixture、回归测试 | 隔离测试数据，能自行重跑和解释失败 |
| Docker 运行交付 | 仅介绍镜像、容器、数据卷、Compose | API 与数据库可按配置启动，数据保留 |
| 最终独立验收 | 待开始 | 独立完成新的数据库功能及迁移、测试 |

### 推进顺序与边界

1. 表和关系模型 → SQL → PostgreSQL 基础与 Python 连接。
2. SQLAlchemy ORM 与事务 → 替换 API 的持久化和标签关系实现。
3. Alembic 结构迁移与旧 JSON 数据导入 → Docker 运行交付。
4. pytest 在替换存储之前开始，以少量场景入门，贯穿后续改动。
5. 最终以一个新的数据库字段或关联需求进行独立验收。

上述是教学顺序，不是一次安装所有依赖的指令。环境准备前核对本机状态；如实际依赖关系要求调整实验顺序，先解释原因。

本阶段先学满足当前业务所需的同步数据库操作、基本事务、查询与索引认识、结构迁移和本地容器运行。高级异步、大规模性能优化、分布式数据库、微服务、生产集群运维以及 LLM / RAG / Agent 实现暂不展开。

### 下一次的具体起点

1. 提交 AGENTS.md、README.md 与本文件的职责重构和进度整理。
2. 创建阶段四开发分支，避免数据库接入代码直接堆在 main。
3. 选择并安装 PostgreSQL Python 驱动，编写最小连接实验。
4. 学习参数化查询，区分连接错误、SQL 错误与约束错误。

阶段四尚未创建开发分支、接入 Python 数据库驱动、实施数据库迁移或修改现有 API 持久化。文档改动的 Git 提交由用户决定。

### 阶段四最终验收标准

- 能解释任务、标签与关联表的设计，并独立写基本 SQL。
- 能用 SQLAlchemy 支撑既有 API，解释 Session、提交和回滚。
- 能演示多步数据库操作失败时不会留下部分结果。
- 能通过迁移增加字段，并验证旧 JSON 数据导入。
- 能独立编写和重跑隔离测试，定位失败原因。
- 能启动容器化项目，解释数据库连接与数据保存位置。
- 能独立完成一个新字段或新关系需求的设计、实现、迁移、测试与 Git 流程。

## 6. 后续路线与并行副线（规划，尚未开始）

| 阶段 | 项目 | 知识方向 |
| --- | --- | --- |
| 5 | AI Task Manager | LLM API、Prompt、Context、Token、结构化输出、Streaming、async/await；先理解基本调用再选择框架 |
| 6 | Personal RAG | 文档解析、Chunking、Embedding、向量数据库、检索、混合检索、Rerank、RAG 评估 |
| 7 | Research Agent | Function / Tool Calling、Agent Loop、State、Planning、Memory、上下文管理与错误处理 |
| 8 | Production Agent | LangChain / LangGraph、MCP、Redis、Tracing、Evaluation、Retry、Timeout、部署 |
| 9 | 开源项目贡献 | 部署、读目录与入口、跟踪调用链、二次开发、测试、尝试 PR |

阶段九候选项目包括 Dify、LangGraph、LlamaIndex、AutoGen、CrewAI、Open WebUI；届时按兴趣和项目状态选择，不表示已经研究或使用。

原规划中的并行投入比例为后端 / Agent 项目 70%、AI / ML 基础 20%、算法与 CS 基础 10%，作为可调整参考。AI / ML 副线包含 NumPy、PyTorch、神经网络、Attention、Transformer、LoRA、SFT；数据结构、算法、Linux 和 CS 基础随主线持续补充。这些比例和主题不代表已执行或已掌握。
