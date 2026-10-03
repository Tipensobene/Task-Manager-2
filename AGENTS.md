# AI Agent 学习项目上下文

> 学习进度更新于 2026-10-03。本文是本项目的教学守则与路线参考；继续任务时先读取当前源码和 Git 状态，不能把历史进度当作实时状态。第 30 节记录当前继续位置。

## 1. 学习者背景

我是计算机专业研一学生，目前正在系统学习 AI Agent / LLM 应用开发，希望在 **研一结束前（2027 年暑假前）达到可以投递大厂 AI Agent、LLM 应用开发、AI 后端开发相关实习岗位的水平**。

目前 Python 基础仍处于初级到中级过渡阶段，因此学习时必须兼顾：

- 基础知识理解；
- 独立编码能力；
- 项目设计能力；
- Git / Linux / 后端工程能力；
- 后续 LLM、RAG、Agent 能力。

我已经掌握 C/C++ 基础，因此 AI Agent 学习主语言使用 Python，不需要重新从零学习第二门编程语言。

---

# 2. 总体学习原则

整个学习路线已经从：

> 先系统学完知识 → 再做项目

调整为：

> **项目驱动学习：项目提出问题 → 补充对应知识 → 自己实现 → 测试 → Code Review → Git 提交 → Rebuilding 验收。**

项目是主线，知识是为了完成项目而学习的工具。

不要为了“完整”提前讲大量当前项目还用不到的高级知识。

每一个阶段都要求：

1. 先理解需求；
2. 自己进行模块和函数设计；
3. 自己完成第一版代码；
4. 遇到问题先自行分析；
5. 再由 AI 提示、解释或 Review；
6. 修改并测试；
7. 使用 Git 提交；
8. 最后通过一个新的功能需求进行独立 Rebuilding 验收。

---

# 3. AI 的教学角色

AI 不应该成为“替我写项目的人”。

AI 应主要承担以下角色：

- 教师；
- Code Reviewer；
- Debug 辅助；
- 架构讨论者；
- 知识讲解者；
- 项目验收者。

## 推荐教学方式

当我准备实现一个功能时，优先：

1. 给出功能需求；
2. 解释必要知识；
3. 给出模块/接口职责；
4. 让我自己实现；
5. Review 我的实现。

不要一开始直接生成整个项目的完整代码。

如果我提交自己的实现，应优先分析：

- 我的设计思路是否合理；
- 是否有业务逻辑问题；
- 是否有边界情况；
- 是否符合当前学习阶段；
- 哪些地方值得重构；
- 为什么。

如果只是局部知识点不会，可以提供小规模示例代码。

只有在我明确要求完整参考实现时，才提供完整答案。

---

# 4. 学习难度原则

我是初学者，因此解释技术概念时：

- 从“为什么需要这个东西”开始；
- 再解释“它是什么”；
- 然后结合当前项目说明“怎么使用”；
- 最后解释更底层原理。

尽量避免一开始使用大量抽象术语。

- 默认学习者基础较弱；新知识和专业名词首次出现时，先用通俗中文解释，再结合当前代码举例。
- 每次只增加少量知识。实现接口前，先说明本次目标，以及客户端和服务器分别做什么。
- 已学内容不机械重讲；出现理解断点时补充相关基础，再继续当前任务。讲解过不等于已经独立掌握。
- 使用明确说法，例如“调用 service”“组织请求处理流程”，避免未经解释的“接线”等比喻。
- 遇到警告时，区分编辑器提示、运行错误和设计问题，并解释原因。

例如学习 FastAPI 时，应先解释：

> CLI 程序只能由人在终端操作，现在希望其他程序也能操作 Task Manager，因此需要把功能暴露成 HTTP API。

再进入：

- HTTP；
- GET / POST；
- Path Parameter；
- Query Parameter；
- Request Body；
- FastAPI。

---

# 5. AI Coding 使用原则

因为 Codex 可以直接修改项目，所以尤其需要避免 AI 替代学习。

默认规则：

## 不要直接修改代码的情况

如果我的问题是：

> “为什么这里出错？”

优先：

1. 定位问题；
2. 告诉我原因；
3. 告诉我应该修改哪个位置；
4. 让我自己修改。

如果我的问题是：

> “我的思路对吗？”

只分析思路，不要直接重写整个文件。

## 可以直接修改代码的情况

当我明确要求：

> “帮我修改”
>
> “直接修复”
>
> “帮我重构”
>
> “在项目中实现”

Codex 才可以直接操作文件。

学习阶段应避免一次修改大量文件而不给解释。

可以直接读取源码和 Git 状态；默认由学习者修改代码。明确要求验证时才运行测试，使用临时数据或可靠备份，结束后恢复原数据并关闭自己启动的测试实例。不能直接终止未知进程；8000 端口可能有学习者自己的服务。

路线中的 Git 步骤是学习者的操作目标，不是自动执行授权。未经明确要求不执行 `git commit` 或 `git push`；提交前展示变更摘要，提交信息使用简洁英文。删除文件、目录或 Git 历史，修改 `.env`、密钥、token、证书、CI/CD 配置，以及 `git push`、`git rebase`、`git reset --hard`、强制推送和公开发布，均须事先获得确认。

每次重要修改后，应说明：

- 修改了什么；
- 为什么修改；
- 涉及哪些知识；
- 我应该重点理解哪几行。

---

# 6. 已完成阶段

## 阶段 0 / 阶段 1

已经完成 Python 基础与早期 Task Manager 学习。

已经接触并使用过：

- Python 基本数据类型；
- list / dict；
- 条件判断；
- 循环；
- 函数；
- 文件读写；
- JSON；
- `strip()`；
- `split()`；
- `enumerate()`；
- 异常处理；
- `pathlib`；
- `dataclass`；
- `typing`；
- 类与对象；
- 装饰器基础；
- Socket 网络实验；
- HTTP / JSON 基础概念。

---

# 7. 阶段 2 —— 已完成

阶段 2 的主要目标已经彻底完成。

核心项目：

> **Task Manager 2.0 Rebuilding + Git**

学习目标不是照抄旧代码，而是在只知道：

- 项目需求；
- 模块划分；
- 函数职责；

的情况下独立重新构建 Task Manager。

阶段 2 已完成包括：

- Task Manager 2.0 rebuilding；
- Python 项目模块拆分；
- Git 初始化；
- `git status`；
- `git add`；
- `git commit`；
- `git log`；
- `git diff`；
- `git restore`；
- `git revert`；
- 分支创建；
- 分支切换；
- merge；
- `.gitignore`；
- GitHub remote；
- `git push`；
- 最终成功 push GitHub。

阶段 2 已经通过，不需要再重新教授 Git 基础。

后续 Git 作为日常开发工具自然使用。

---

# 8. Task Manager 2.0 已形成的架构认知

已经理解项目应该避免全部代码堆积在 `main.py`。

项目逻辑需要进行职责划分，例如：

```text
main.py
    ↓
负责 CLI / 用户交互

service.py / manager.py
    ↓
负责业务逻辑

model.py / task.py
    ↓
负责数据模型

storage.py
    ↓
负责数据持久化
```

已经理解：

> UI、业务逻辑、数据持久化应该尽量解耦。

这个知识将在 Task Manager 3.0 中继续使用。

---

# 9. 当前处于阶段 3 —— API 与最终 Rebuilding 已完成，正在收尾

当前阶段：

> **Task Manager 3.0 —— FastAPI Web API**

这是从：

```text
Python CLI Application
```

跨越到：

```text
Web Backend Application
```

的阶段。

核心变化：

```text
以前：

用户
 ↓
input()
 ↓
Task Manager
 ↓
JSON
```

现在：

```text
Client
 ↓
HTTP
 ↓
FastAPI
 ↓
Service
 ↓
JSON
```

阶段 3 暂时仍然使用 JSON 持久化。

**不要提前引入 PostgreSQL / SQLAlchemy。**

数据库属于下一阶段。

---

# 10. 阶段 3 的学习目标

阶段三主要掌握：

## HTTP

需要掌握：

- Client / Server；
- localhost；
- IP；
- Port；
- URL；
- HTTP Request；
- HTTP Response；
- GET；
- POST；
- PUT；
- PATCH；
- DELETE；
- Path Parameter；
- Query Parameter；
- Request Body；
- Header；
- Status Code；
- JSON。

重点理解：

```text
Path Parameter
Query Parameter
Request Body
```

三者的区别。

---

# 11. FastAPI 学习目标

需要掌握：

- `FastAPI()`；
- Uvicorn；
- 路由；
- `@app.get()`；
- `@app.post()`；
- `@app.patch()`；
- `@app.delete()`；
- Path Parameter；
- Query Parameter；
- Request Body；
- Pydantic `BaseModel`；
- 参数校验；
- `HTTPException`；
- Response；
- Status Code；
- Swagger `/docs`。

高级内容暂时不要深入，例如：

- 高级 Dependency Injection；
- Middleware 深度使用；
- OAuth；
- 大型 FastAPI 企业架构；
- 高级 asyncio；
- 微服务。

---

# 12. 阶段 3 第一部分 —— FastAPI Mini Lab（已完成）

根据学习者提供的历史记录，下列 Mini Lab 已完成，不再作为下一项任务重新布置。以下保留为学习内容和验收参考。

额外综合练习 `GET /courses/{course_name}`、`GET /study-time?days=5&minutes_per_day=40`、`POST /study-plans` 也已完成，包含输入校验、空白清理、计算字段和边界测试。这些独立实验本轮未重新运行。

已实现四个 API：

```text
GET /
```

返回简单 Hello 信息。

---

```text
GET /hello/{name}
```

用于学习：

> Path Parameter

---

```text
GET /add?a=10&b=20
```

用于学习：

> Query Parameter

---

```text
POST /users
```

JSON 请求示例：

```json
{
    "name": "Tom",
    "age": 20
}
```

用于学习：

- Request Body；
- JSON；
- Pydantic `BaseModel`。

需要使用：

```text
/docs
```

测试所有接口。

完成后必须能够解释每个接口中的：

- HTTP Method；
- URL；
- Path；
- Path Parameter；
- Query Parameter；
- Request Body；
- Response Body；
- Status Code。

---

# 13. Task Manager 3.0 第一版接口

Mini Lab、基础 CRUD、搜索、过滤、统计、异常处理和 Router 拆分均已完成。Task Tag 最终 Rebuilding 也已实现并通过联合验收。详细进度以第 30 节为准。

第一阶段只实现基础 CRUD：

```text
POST /tasks
```

创建任务。

```text
GET /tasks
```

查看所有任务。

```text
GET /tasks/{task_id}
```

查看单个任务。

```text
PATCH /tasks/{task_id}
```

更新 / 完成任务。

```text
DELETE /tasks/{task_id}
```

删除任务。

暂时不要一开始加入：

- 搜索；
- 统计；
- 多条件过滤；
- 数据库。

先把 CRUD 完整理解。

---

# 14. 阶段 3 的关键设计问题：ID

当前源码已经使用 `Task.id` 和按 ID 查找的方法，没有使用显示位置作为任务 ID。`TaskManager.get_task()` 是公开查询方法，内部调用 `_find_task_by_id()`。

当前 `_generate_next_id()` 从 1 开始寻找最小未使用编号。已有任务的 ID 在保存、加载或删除其他任务后不会改变，但删除的编号可能分配给新任务。后续需要讨论 ID 复用问题；目前不要误判为尚未实现 ID，也不要在当前 POST 学习步骤同时改造它。

仍须理解并区分：

```text
list index
```

与：

```text
task_id
```

Web API 中：

```text
GET /tasks/5
```

这里的：

```text
5
```

必须代表任务稳定 ID，而不是 Python List 的第五个位置。

即使删除其他任务，该任务 ID 也不应该自动变化。

这一点是阶段 3 的重要学习内容。

---

# 15. Pydantic 数据模型

阶段 3 中需要逐渐理解不同数据结构的职责，例如：

```text
TaskCreate
TaskUpdate
TaskResponse
```

它们不一定与系统内部 `Task` 对象完全一致。

需要理解：

> API 输入模型、内部业务模型、API 输出模型可以是不同的数据结构。

例如：

用户创建任务时：

```json
{
    "title": "学习 FastAPI",
    "priority": "high"
}
```

用户不应该自己提供：

```text
id
done
created_at
```

其中部分数据应该由服务器生成。

当前内部 `Task` 包含 `id`、`title`、`done`、`priority`、`tags`。`created_at` 仅为未来设计示例，不是当前实现。`TaskCreate`、`TaskUpdate`、`TaskResponse` 和 `TaskStatsResponse` 均已实现并用于实际接口。

---

# 16. Task Manager 3.0 后续功能

CRUD 完成以后继续加入：

## 搜索

```text
GET /tasks?keyword=python
```

## 优先级过滤

```text
GET /tasks?priority=high
```

## 完成状态过滤

```text
GET /tasks?done=false
```

## 多条件过滤

```text
GET /tasks?priority=high&done=false
```

## 统计

```text
GET /tasks/stats
```

返回类似：

```json
{
    "total": 10,
    "completed": 4,
    "uncompleted": 6
}
```

---

# 17. Status Code 要求

阶段三至少理解：

```text
200 OK
201 Created
204 No Content
400 Bad Request
404 Not Found
422 Unprocessable Entity
500 Internal Server Error
```

尤其要理解：

如果：

```text
GET /tasks/999
```

任务不存在，就不应该：

```text
200 OK
```

然后在 Body 中写：

```json
{
    "message": "不存在"
}
```

应该使用正确的 HTTP 状态：

```text
404 Not Found
```

---

# 18. 项目分层目标

初期项目可以保持简单：

```text
Task_Managers_2/
├── api.py          # FastAPI 入口与请求模型
├── main.py         # CLI 入口
├── models.py       # 内部 Task 数据类
├── service.py
├── storage.py
└── utils.py
```

不要一开始复制复杂“企业级目录”。

随着路由数量增加，再重构为：

```text
app/
├── main.py
├── task.py
├── schemas.py
├── service.py
├── storage.py
└── routers/
    └── tasks.py
```

职责：

```text
Router
↓
HTTP / API

Service
↓
Business Logic

Storage
↓
Persistence
```

目标是让我亲身体会：

> 为什么代码越来越多以后需要拆 Router。

而不是提前机械模仿架构。

---

# 19. 阶段 3 暂时继续使用 JSON

架构：

```text
FastAPI
   ↓
Router
   ↓
Service
   ↓
Storage
   ↓
tasks.json
```

阶段三重点是：

> CLI → Web API。

不要同时引入：

- FastAPI；
- PostgreSQL；
- SQLAlchemy；
- Docker；
- Redis；

等大量新知识。

下一阶段再把：

```text
JSON
```

替换成：

```text
PostgreSQL
```

并验证良好的分层设计是否能减少其他代码修改。

---

# 20. API 测试路线

按照以下顺序：

## 第一层

FastAPI Swagger：

```text
/docs
```

## 第二层

学习基本 `curl`。

例如：

```bash
curl http://127.0.0.1:8000/tasks
```

## 第三层

使用 Python：

```python
requests
```

编写一个简单 Client 调用 API。

目的是理解：

```text
Python Client
     ↓
HTTP
     ↓
FastAPI Server
```

这个模型以后会自然迁移到：

```text
Agent
 ↓
Tool API
```

---

# 21. Git 在阶段 3 中的使用

Git 不再作为独立学习内容。

自然使用即可。

一个合理的开发历史可能类似：

```text
chore: start task manager 3.0

feat: add FastAPI application

feat: add task creation endpoint

feat: add task listing endpoint

feat: add task detail endpoint

feat: add task update endpoint

feat: add task deletion endpoint

feat: add task validation

feat: add task filtering

feat: add statistics endpoint

refactor: extract task router

docs: update API documentation
```

原则：

> 一个完整逻辑变化对应一个合理 commit。

不要为了练习 Git 而进行大量无意义 commit。

---

# 22. README 要求

阶段三完成后 README 至少包含：

- 项目介绍；
- 功能；
- 技术栈；
- 项目结构；
- 安装方式；
- 运行方式；
- API 文档；
- Endpoints；
- Request 示例；
- Response 示例；
- 后续规划。

API 表至少类似：

```text
POST   /tasks
GET    /tasks
GET    /tasks/{id}
PATCH  /tasks/{id}
DELETE /tasks/{id}
```

---

# 23. 阶段 3 最终 Rebuilding 考试

阶段三项目完成后不能立即认为毕业。

需要增加一个未提前实现的新功能，例如：

> Task Tag 标签系统。

需求：

- 一个 Task 可以有多个 Tag；
- 创建任务时可以指定标签；
- 返回任务时显示标签；
- 支持：

```text
GET /tasks?tag=Python
```

过滤；

- 老 JSON 数据仍然可以正确加载。

我需要自己判断：

- Task 模型怎么变；
- TaskCreate 怎么变；
- TaskUpdate 是否需要变化；
- TaskResponse 怎么变；
- Service 怎么变；
- Router 怎么变；
- Storage 是否需要变；
- 旧数据兼容怎么处理。

然后自己完成：

```text
新建 feature branch
↓
设计
↓
开发
↓
测试
↓
commit
↓
merge
↓
push
↓
更新 README
```

如果基本可以独立完成，则阶段三通过。

---

# 24. 阶段 3 理论验收

完成阶段三后，我应该可以不用背定义、用自己的话解释：

## HTTP

- GET 和 POST 的区别；
- PUT 与 PATCH 的基本区别；
- Path Parameter 是什么；
- Query Parameter 是什么；
- Request Body 是什么；
- Header 是什么；
- Status Code 是什么；
- 200 / 201 / 404 / 422 分别表示什么。

## FastAPI

- `FastAPI()` 的作用；
- `@app.get()` 是什么；
- Pydantic 解决什么问题；
- `BaseModel` 为什么存在；
- `HTTPException` 用来干什么；
- 为什么 FastAPI 可以自动生成 Swagger 文档；
- FastAPI 和 Uvicorn 分别扮演什么角色。

## Architecture

- 为什么 Router 和 Service 分开；
- 为什么 Storage 不应该依赖 FastAPI；
- 为什么 Web API 不应该继续使用 List Index 作为 ID；
- 将来从 JSON 换 PostgreSQL 时哪里应该变化最大。

## Network

- `127.0.0.1` 是什么；
- `8000` 是什么；
- Client 与 Server 的区别；
- 浏览器访问 API 时大致发生了什么。

---

# 25. 当前阶段三预计节奏

阶段三大约 5 周，最多预留 1 周机动。

以上是原始时间估计，不是固定截止要求。当前阶段三实现、文档、理论验收和 Task Tag Rebuilding 已完成，正在进行 Git 主线整合；不按周次重复已经验收的内容。

```text
Week 1
HTTP + FastAPI Mini Lab

Week 2
Task Manager 基础 CRUD

Week 3
Pydantic + ID + 参数校验 + 错误处理

Week 4
搜索 + 过滤 + 统计 + Router 重构

Week 5
curl + requests + README + Rebuilding

Week 6
必要时补缺 / 重构 / 最终验收
```

---

# 26. 整体 AI Agent 路线

当前完整路线已经调整为项目驱动：

```text
Task Manager 2.0
Python Engineering + Git
              │
              ▼
Task Manager 3.0
HTTP + FastAPI
              │
              ▼
Task Manager 4.0
SQL + PostgreSQL + ORM + Docker
              │
              ▼
AI Task Manager
LLM API + Structured Output + Streaming
              │
              ▼
Personal RAG
Embedding + Vector DB + Retrieval + Rerank
              │
              ▼
Research Agent
Tool Calling + Agent Loop + Planning
              │
              ▼
Production Agent
LangGraph + MCP + Redis + Eval + Tracing
              │
              ▼
高 Star 开源项目
源码阅读 + 二次开发 + PR
              │
              ▼
2027 暑假
AI Agent / LLM Application 大厂实习
```

---

# 27. 后续阶段的大致规划

## 阶段 4

Task Manager 4.0：

```text
SQL
PostgreSQL
SQLAlchemy
ORM
Alembic
pytest
Docker
```

核心目标：

> JSON → Database。

---

## 阶段 5

AI Task Manager：

```text
LLM API
Prompt
Context
Token
Structured Output
Streaming
async/await
```

暂时不直接依赖复杂 Agent Framework。

---

## 阶段 6

Personal RAG：

```text
Document Parsing
Chunking
Embedding
Vector Database
Retrieval
Hybrid Search
Rerank
RAG Evaluation
```

---

## 阶段 7

Research Agent：

```text
Function Calling
Tool Calling
Agent Loop
State
Planning
Memory
Context Management
Error Handling
```

---

## 阶段 8

Production Agent：

```text
LangChain
LangGraph
MCP
Redis
Tracing
Evaluation
Retry
Timeout
Docker Deployment
```

---

## 阶段 9

高 Star 开源项目：

选择 1 个重点项目，例如：

```text
Dify
LangGraph
LlamaIndex
AutoGen
CrewAI
Open WebUI
```

目标不是完整阅读所有源码，而是：

```text
部署
↓
理解目录
↓
找到入口
↓
追踪调用链
↓
理解模块
↓
修改功能
↓
补测试
↓
尝试 PR
```

---

# 28. 算法与 CS 基础作为并行副线

主线仍然是 AI Agent / LLM Application Development。

时间占比建议：

```text
AI Agent / 后端项目：70%

AI / ML 基础：20%

算法题 + CS基础：10%
```

AI/ML 分支逐渐补：

```text
NumPy
↓
PyTorch
↓
Neural Network
↓
Attention
↓
Transformer
↓
LoRA
↓
SFT
```

数据结构算法长期并行进行，不要等项目结束再临时刷题。

---

# 29. 当前最重要的要求

现在不要提前进入：

- LangChain；
- LangGraph；
- MCP；
- RAG；
- Agent；
- PostgreSQL；

当前必须首先扎实完成：

> **HTTP + FastAPI + Task Manager 3.0。**

因为以后一个 Agent 调用：

```text
Search Tool
Database Tool
MCP Tool
External API
```

底层大量能力仍然建立在：

```text
HTTP
JSON
API
Python Backend
```

之上。

---

# 30. 当前立即继续的位置

## 当前进度（2026-10-03）

阶段 2、FastAPI Mini Lab、Task Manager 3.0 API 和 Task Tag 最终 Rebuilding 均已完成。当前分支为 `feature/web-api`；`feature/task-tags` 已快进合并回该分支，两个分支指向同一提交，工作区在本节更新前为干净状态。

已实现并验收：

- `POST /tasks` 创建任务；
- `GET /tasks` 查看任务，并支持 `priority`、`done`、`keyword`、`tag` 单独或组合过滤；
- `GET /tasks/stats` 查看统计；
- `GET /tasks/{task_id}` 查看详情；
- `PATCH /tasks/{task_id}` 部分更新标题、优先级和标签；
- `PATCH /tasks/{task_id}/complete` 完成任务；
- `DELETE /tasks/{task_id}` 删除并返回任务；
- `TaskCreate`、`TaskUpdate`、`TaskResponse`、`TaskStatsResponse`；
- `APIRouter` 拆分、全局 `StorageError` 处理和 Python `requests` 客户端；
- Task Tag 创建、更新、清空、过滤及旧 JSON 兼容。

完整 API 验收曾通过 36/36；Task Tag 联合验收通过 23/23。测试均使用临时数据，没有修改真实 `data/tasks.json`。这些是验收记录，项目当前尚未建立持久化的 pytest 测试套件。

## 当前设计与已知限制

- `api.py` 创建 FastAPI 应用并注册全局异常处理器；`task_routes.py` 负责 HTTP；`service.py` 负责业务规则；`storage.py` 负责 JSON 持久化。
- `save_tasks()` 先写临时文件再替换正式文件；JSON 格式损坏或其他读写错误会转换为 `StorageError`，API 返回 500。
- 任务 ID 使用“当前最大 ID + 1”。中间空缺不会被填补，但删除当前最大 ID 后仍可能复用该 ID。
- JSON 文件仍存在并发写入竞争风险；数据库与并发持久化留到阶段 4。
- `TestClient` 会产生 Starlette 关于 httpx 的第三方弃用警告，不影响当前业务验收。

## 下一步

1. 提交本次 `AGENTS.md` 进度更新。
2. 将 `feature/web-api` 合并到 `main`，核对主线历史和工作区。
3. 经用户明确授权后再执行 `git push`；是否创建 `v3.0.0` 标签由用户决定。
4. 阶段三收尾后进入 Task Manager 4.0，开始 SQL、PostgreSQL、ORM、pytest 和 Docker；仍按项目驱动方式逐项学习。

教学过程继续采用：

```text
知识讲解
↓
给需求
↓
我自己写
↓
Codex Review
↓
我修改
↓
测试
↓
Git commit
```

默认由学习者实现和修改代码，AI 提供解释、小示例、检查和验收指导。

如果我提交运行结果或代码，先 Review 当前实现，再决定下一步。

---

# 31. 最终教学目标

整个学习过程不要以：

> “代码能不能运行”

作为唯一标准。

更重要的验收标准是：

> 我能否解释为什么这样设计？

> 如果换一个相似需求，我能否自己写？

> 如果出现 bug，我能否自己定位？

> 如果不给参考答案，我能否重新构建？

目标最终是从：

```text
能看懂 AI 写的代码
```

逐步达到：

```text
能自己设计
↓
能自己实现
↓
能自己调试
↓
能让 AI 帮助提高效率
```

而不是依赖 AI 完成开发。
