# Task Manager 3.0

## 项目简介

Task Manager 3.0 是一个使用 Python 和 FastAPI 开发的任务管理 Web API。项目从 Task Manager 2.0 命令行程序升级而来，在保留 CLI 的同时，通过 HTTP 和 JSON 向浏览器、Swagger UI、Python 程序等客户端提供任务管理能力。

项目继续复用原有的 `TaskManager` 业务逻辑，并使用 JSON 文件保存任务。当前阶段的重点是学习 HTTP、FastAPI、Pydantic、API 分层、异常处理和客户端调用。

```text
浏览器 / Swagger UI / Python requests
                  ↓ HTTP
              FastAPI
                  ↓
             TaskManager
                  ↓
          data/tasks.json
```

## 主要功能

- 创建、查看、更新、完成和删除任务；
- 按优先级、完成状态和标题关键词过滤任务；
- 查看任务统计信息；
- 使用 Pydantic 校验请求数据和响应数据；
- 使用正确的 HTTP 状态码返回成功或错误结果；
- 统一处理 JSON 文件读写异常；
- 使用临时文件降低覆盖写入过程中损坏原数据的风险；
- 保留 Task Manager 2.0 命令行入口；
- 提供基于 `requests` 的 Python 客户端示例。

## 技术栈

| 技术 | 用途 |
| --- | --- |
| Python 3.10+ | 项目开发语言 |
| FastAPI | 定义 Web API、路由和异常处理器 |
| Uvicorn | 运行 ASGI Web 服务器 |
| Pydantic | 请求和响应数据校验 |
| requests | Python HTTP 客户端示例 |
| dataclass | 定义内部 `Task` 和 `TaskManager` 模型 |
| JSON | 任务数据持久化 |
| pathlib | 管理数据文件与日志路径 |
| logging | 记录任务操作日志 |

## 项目结构

```text
Task_Managers_2/
├── api.py            # FastAPI 应用入口，注册 Router 和全局异常处理器
├── task_routes.py    # 任务路由、请求模型和响应模型
├── client_demo.py    # 使用 requests 调用 API 的客户端示例
├── main.py           # Task Manager 2.0 命令行入口
├── models.py         # 内部 Task 数据模型
├── service.py        # TaskManager 业务逻辑
├── storage.py        # JSON 加载、保存和存储异常
├── utils.py          # 日志配置、输入工具和日志装饰器
├── data/             # 任务数据目录
├── logs/             # 日志目录
├── AGENTS.md         # 项目学习路线和协作规则
├── .gitignore
└── README.md
```

主要调用方向：

```text
api.py
  ↓
task_routes.py
  ↓
service.py
  ↓
storage.py
```

- `api.py` 创建 FastAPI 应用，注册任务 Router 和全局存储异常处理器。
- `task_routes.py` 负责 HTTP 请求与响应，并把业务操作交给 `TaskManager`。
- `service.py` 负责创建、查询、更新、删除、搜索和统计等业务逻辑。
- `storage.py` 负责在 `Task` 对象与 JSON 文件之间转换数据。
- `models.py` 定义内部任务对象，不依赖 FastAPI。

## 安装依赖

建议先创建并激活虚拟环境，然后安装当前版本需要的依赖：

```powershell
python -m pip install fastapi uvicorn requests
```

## 运行 Web API

在项目根目录执行：

```powershell
python -m uvicorn api:app --reload
```

命令含义：

- `api` 对应 `api.py`；
- `app` 对应文件中的 `app = FastAPI(...)`；
- `--reload` 在开发期间检测代码变化并自动重启服务。

启动后可以访问：

- API 基础地址：`http://127.0.0.1:8000`
- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI 文档：`http://127.0.0.1:8000/openapi.json`

## API 接口

| HTTP Method | 路径 | 作用 | 成功状态码 |
| --- | --- | --- | --- |
| `GET` | `/tasks` | 查看、搜索或过滤任务 | `200` |
| `GET` | `/tasks/stats` | 查看任务统计 | `200` |
| `GET` | `/tasks/{task_id}` | 查看单个任务 | `200` |
| `POST` | `/tasks` | 创建任务 | `201` |
| `PATCH` | `/tasks/{task_id}` | 部分更新任务 | `200` |
| `PATCH` | `/tasks/{task_id}/complete` | 将任务标记为完成 | `200` |
| `DELETE` | `/tasks/{task_id}` | 删除并返回任务 | `200` |

### 查看和过滤任务

```http
GET /tasks
```

支持以下可选查询参数：

| 参数 | 类型 | 示例 | 作用 |
| --- | --- | --- | --- |
| `priority` | string | `high` | 按 `low`、`normal` 或 `high` 过滤 |
| `done` | boolean | `false` | 按完成状态过滤 |
| `keyword` | string | `python` | 按标题关键词搜索 |

多个条件可以组合使用：

```http
GET /tasks?priority=high&done=false&keyword=python
```

响应示例：

```json
[
    {
        "id": 1,
        "title": "学习 FastAPI",
        "done": false,
        "priority": "high"
    }
]
```

### 查看任务统计

```http
GET /tasks/stats
```

响应示例：

```json
{
    "total": 3,
    "completed_num": 1,
    "uncompleted_num": 2
}
```

### 查看单个任务

```http
GET /tasks/1
```

任务不存在时返回 `404 Not Found`。

### 创建任务

```http
POST /tasks
Content-Type: application/json
```

请求体：

```json
{
    "title": "学习创建任务接口",
    "priority": "high"
}
```

- `title` 必填，清理首尾空白后长度必须为 1～100；
- `priority` 可省略，默认值为 `normal`；
- `id` 由服务器生成；
- `done` 由服务器设置为 `false`。

成功时返回 `201 Created` 和新任务：

```json
{
    "id": 2,
    "title": "学习创建任务接口",
    "done": false,
    "priority": "high"
}
```

### 部分更新任务

```http
PATCH /tasks/2
Content-Type: application/json
```

请求体可以只包含需要修改的字段：

```json
{
    "title": "复习 FastAPI",
    "priority": "normal"
}
```

当前支持更新 `title` 和 `priority`。显式传入 `null` 会返回 `400 Bad Request`。

### 完成任务

```http
PATCH /tasks/2/complete
```

成功后任务的 `done` 为 `true`。重复完成已经完成的任务会返回 `400 Bad Request`。

### 删除任务

```http
DELETE /tasks/2
```

成功时返回被删除的任务；任务不存在时返回 `404 Not Found`。

## 状态码与错误响应

| 状态码 | 含义 | 当前项目中的示例 |
| --- | --- | --- |
| `200 OK` | 请求成功 | 查询、更新或删除成功 |
| `201 Created` | 资源创建成功 | 创建任务成功 |
| `400 Bad Request` | 业务输入不合法 | 非法优先级、重复完成任务、更新字段为 `null` |
| `404 Not Found` | 资源不存在 | 查询、更新或删除不存在的任务 |
| `422 Unprocessable Entity` | 请求没有通过模型校验 | 缺少标题、标题过长、路径 ID 不是整数 |
| `500 Internal Server Error` | 服务器内部处理失败 | JSON 文件读取、解析或保存失败 |

错误响应示例：

```json
{
    "detail": "Task not found"
}
```

## Python 客户端示例

确保 API 服务器已经运行，然后执行：

```powershell
python client_demo.py
```

`client_demo.py` 使用 `requests` 发送 HTTP 请求，演示 Python 客户端如何获取任务统计数据并处理连接错误。

## 运行命令行版本

原有的 Task Manager 2.0 CLI 仍然可以运行：

```powershell
python main.py
```

CLI 与 Web API 复用相同的业务模型和 JSON 数据文件。

## 数据存储

任务保存在 `data/tasks.json`，每个任务包含：

```json
{
    "id": 1,
    "title": "学习 FastAPI",
    "done": false,
    "priority": "high"
}
```

保存时会先把完整数据写入临时文件，写入成功后再替换正式的 `tasks.json`。这样可以降低直接使用 `w` 模式覆盖正式文件时，写入中途失败造成原数据损坏的风险。

当前存储行为：

- 数据文件不存在时返回空任务列表；
- JSON 格式损坏时抛出 `StorageError`；
- 读取或保存发生其他 `OSError` 时抛出 `StorageError`；
- FastAPI 全局异常处理器把未处理的 `StorageError` 转换为 `500` JSON 响应。

当前仍使用 JSON 文件，不处理多个请求同时写入造成的竞争问题。数据库和并发持久化将在后续阶段学习。

## 任务 ID

任务 ID 由服务器生成：

- 没有任务时从 `1` 开始；
- 有任务时使用当前最大 ID 加 `1`；
- 删除中间位置的任务后不会填补该空缺；如果删除的是当前最大 ID，下一次创建任务仍可能复用这个 ID。

ID 表示任务身份，不是任务在 Python 列表中的位置。

## 当前学习阶段

Task Manager 3.0 用于学习从命令行程序迁移到 Web API 的过程，目前已经完成：

- FastAPI 和 Uvicorn 基础；
- HTTP 路由与状态码；
- Pydantic 请求和响应模型；
- 任务 CRUD；
- 搜索、过滤和统计；
- HTTP 异常与存储异常处理；
- `APIRouter` 路由拆分；
- Python HTTP 客户端示例。

后续将进行完整接口验收和 Task Tag 独立 Rebuilding。数据库、SQLAlchemy、Docker、LLM、RAG 和 Agent 等内容不属于当前版本范围。
