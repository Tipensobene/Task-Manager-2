# Task Manager 4.0

## 项目简介

Task Manager 4.0 是一个使用 Python、FastAPI、SQLAlchemy 和 PostgreSQL 开发的任务管理 Web API。项目从 Task Manager 2.0 命令行程序升级而来，在保留旧 CLI 的同时，通过 HTTP 和 JSON 向浏览器、Swagger UI、Python 程序等客户端提供任务管理能力。

正式 Web API 已采用 Router、Service 和 Repository 分层，并使用 PostgreSQL 持久化任务、标签及其多对多关系。旧 CLI 仍保留原有 `TaskManager` 和 JSON 存储，作为历史版本入口。

```text
浏览器 / Swagger UI / Python requests
                  ↓ HTTP
              FastAPI
                  ↓
          TaskService
                  ↓
        TaskRepository
                  ↓
       SQLAlchemy / PostgreSQL
```

## 主要功能

- 创建、查看、更新、完成和删除任务；
- 为任务添加、更新或清空多个标签；
- 按优先级、完成状态、标题关键词和标签过滤任务；
- 查看任务统计信息；
- 使用 Pydantic 校验请求数据和响应数据；
- 使用正确的 HTTP 状态码返回成功或错误结果；
- 使用 PostgreSQL 持久化任务和标签；
- 使用 SQLAlchemy ORM、Session 和事务管理数据库操作；
- 使用 pytest 与事务回滚隔离自动化测试；
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
| SQLAlchemy | ORM 映射、数据库查询与事务操作 |
| PostgreSQL | 正式 Web API 的数据持久化 |
| Alembic | 数据库结构迁移与版本管理 |
| Psycopg | SQLAlchemy 使用的 PostgreSQL 驱动 |
| pytest | 自动化测试与数据库测试隔离 |
| dataclass / JSON | 保留的旧 CLI 模型与存储方式 |

## 项目结构

```text
Task_Managers_2/
├── api.py            # FastAPI 应用入口，注册任务 Router
├── task_routes.py    # 任务路由、请求模型和响应模型
├── task_service.py   # 正式 Web API 的业务规则
├── task_repository.py # SQLAlchemy 数据访问层
├── database.py       # Engine、Session 工厂与 FastAPI 数据库依赖
├── orm_models.py     # tasks、tags 与关联表的 ORM 映射
├── legacy_import.py  # 旧JSON校验与一次性事务导入入口
├── alembic.ini       # Alembic 配置
├── alembic/          # 迁移环境及版本脚本
├── Dockerfile        # API 镜像构建步骤
├── .dockerignore     # 构建上下文排除规则
├── compose.yaml      # API、独立 PostgreSQL、健康检查与持久卷
├── client_demo.py    # 使用 requests 调用 API 的客户端示例
├── main.py           # Task Manager 2.0 命令行入口
├── models.py         # 内部 Task 数据模型
├── service.py        # TaskManager 业务逻辑
├── storage.py        # JSON 加载、保存和存储异常
├── utils.py          # 日志配置、输入工具和日志装饰器
├── database_api_demo.py # 数据库 API 教学演示入口
├── examples/database/ # 数据库教学脚本：psycopg/与sqlalchemy/
├── examples/docker/  # Nginx 页面与镜像构建教学示例
├── tests/            # pytest自动化测试
├── data/             # 任务数据目录
├── logs/             # 日志目录
├── AGENTS.md         # 学习导师与项目协作规则
├── PROGRESS.md       # 阶段路线、知识点、验收记录与当前学习进度
├── .gitignore
└── README.md
```

主要调用方向：

```text
api.py
  ↓
task_routes.py
  ↓
task_service.py
  ↓
task_repository.py
  ↓
database.py / PostgreSQL
```

- `api.py` 创建 FastAPI 应用并注册任务 Router。
- `task_routes.py` 负责接收和校验 HTTP 数据、调用 Service、转换异常并控制提交事务。
- `task_service.py` 负责输入规范化及创建、查询、更新、删除和统计等业务规则。
- `task_repository.py` 负责通过 SQLAlchemy 查询和修改 PostgreSQL 数据。
- `database.py` 创建 Engine 和 Session，并通过依赖注入为请求提供 Session。
- `orm_models.py` 定义任务、标签和中间表的 ORM 映射。
- `main.py → service.py → storage.py` 是保留的旧 CLI/JSON 运行链。

## 安装依赖

阶段四教学脚本已经集中到 [examples/database](examples/database/README.md)，该说明包含模块运行命令和 PyCharm 配置方式。正式 Web API 已完成 PostgreSQL 迁移，`database_api_demo.py` 仅保留为学习过程中的演示入口。

建议先创建并激活虚拟环境，然后安装当前版本需要的依赖：

```powershell
python -m pip install -r requirements.txt
```

## 运行 Web API

以下是本机 Python 开发运行方式；使用容器请见后面的“使用 Docker Compose 运行”。正式 API 默认连接本机 PostgreSQL 的 `task_manager_learning` 数据库，用户为postgres、端口5432。启动前先在当前 PowerShell 会话设置数据库密码和目标数据库名：

```powershell
$env:TASK_MANAGER_DB_PASSWORD = "你的数据库密码"
$env:TASK_MANAGER_DB_NAME = "task_manager_learning"
```

该变量只对当前 PowerShell 会话及其启动的子进程有效。不要把真实密码写入源码或提交到 Git。

数据库名变量未设置时默认为task_manager_learning；主机由TASK_MANAGER_DB_HOST指定，未设置时默认localhost。本机开发请确认该变量没有残留为容器服务名db。API、测试与Alembic均使用此配置。目标数据库需要预先创建，首次运行请先按下节完成结构初始化。确认目标库后，在项目根目录执行：

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

## 数据库结构迁移

先在pgAdmin创建目标空数据库，名称与TASK_MANAGER_DB_NAME一致；Alembic不创建数据库本身。全新空库在设置连接环境变量后执行：

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

当前最新版本为f959d63045e7，前驱042f491f9a4a创建三张业务表，第二版增加tasks.created_at。current应显示最新版本及head，check应输出No new upgrade operations detected。check只检查自动比较支持范围内的差异；env.py已启用数据库默认值比较。

已有手动建表数据库不能直接套用全新空库流程。先只读核对其真实结构与对应基线一致，再使用`python -m alembic stamp 042f491f9a4a`登记初始版本，之后upgrade head。stamp只写版本记录，不核对、修复结构或执行建表；已经登记过版本的数据库无需重复stamp。

后续修改模型后，可运行`python -m alembic revision --autogenerate -m "变更说明"`生成迁移，人工审查后先在专用测试库验证，再应用到实际使用库。生成文件不等于已经升级，历史已应用迁移不回写。`upgrade head --sql`只生成SQL文本。

回退命令会执行对应downgrade，可能删除列、表及其数据；日常运行不需要回退。本项目的回退验证在task_manager_migration_test中进行，原库仅升级。created_at使用带时区时间戳和CURRENT_TIMESTAMP默认值；旧记录补迁移事务时间，不能据此恢复真实历史创建时间。当前API响应尚未增加该字段。

## 使用 Docker Compose 运行

需要已启动的 Docker Engine（Linux 容器）和 Docker Compose，下载镜像及安装依赖需要网络。本节命令在项目根目录的同一 PowerShell 终端执行；容器方式不要求先安装本机 Python 依赖或本机 PostgreSQL。Windows 上安装 Docker 后，如果旧 IDE 终端无法找到 docker，请重开终端；本机安装在 D:\Docker 时也可临时将 D:\Docker\resources\bin 加入当前终端 PATH，凭据助手同样需要此路径。

配置提供两个独立服务：api根据根目录Dockerfile构建，db使用postgres:18。API连接db:5432/task_manager_container，不使用本机task_manager_learning。数据库端口未发布至Windows；API只发布127.0.0.1:8000，启动前确认没有本机开发服务器占用该端口。本节不会自动导入旧JSON。

### 首次启动空数据库

先交互输入独立容器数据库密码，不在配置文件中填写实际密码：

```powershell
$containerPassword = Read-Host "请输入独立容器数据库密码" -AsSecureString
$env:TASK_MANAGER_CONTAINER_DB_PASSWORD = [System.Net.NetworkCredential]::new("", $containerPassword).Password
docker compose config --quiet
```

变量仅在当前终端及子进程中有效，新终端需要重新提供；容器环境变量最终是普通字符串，不是秘密管理系统。不要打印完整环境或把实际密码放入截图。普通docker compose config可能展开密码，因此此处使用--quiet。PostgreSQL初始化完成后须继续提供同一个密码；修改外部变量不会自动修改已有数据库密码。请自行妥善保存密码。

依次执行，每一步成功后再继续：

```powershell
docker compose up -d --wait --wait-timeout 120 db
docker compose build api
docker compose run --no-deps api python -m alembic upgrade head
docker compose up -d --wait --wait-timeout 120 api
docker compose ps
```

第一个命令创建或复用项目网络、命名卷并等待数据库健康；官方镜像只在空数据目录初始化用户postgres和库task_manager_container。Alembic任务使用api的网络和环境变量，以迁移命令覆盖默认Uvicorn CMD，真实创建/升级业务表。这里不指定固定任务容器名，便于以后再次执行迁移；退出的任务容器会保留，可用ps -a查看，清理另行确认。构建不执行迁移，API启动也不自动迁移；先迁移成功再启动API。

访问以下地址验证：

- http://127.0.0.1:8000/docs：接口文档，标题Task Manager 4.0。
- http://127.0.0.1:8000/tasks：真实数据库查询；新空库返回[]，已有数据时返回任务列表。

db的healthy仅表示pg_isready成功，不证明API密码正确或业务表存在；API当前无健康检查，up --wait等待运行状态，仍需实际HTTP查询。120秒是等待超时，不是服务寿命；超时不保证自动停止已经启动的资源。

### 后续停止、恢复和查看日志

```powershell
docker compose ps
docker compose ps -a
docker compose logs --tail 30 api
docker compose logs --tail 30 db
```

ps查看当前项目运行服务，ps -a包含停止及一次性任务容器。停止整套服务并保留容器、网络及卷：

```powershell
docker compose stop
```

在提供相同容器数据库密码后恢复默认服务：

```powershell
docker compose up -d --wait --wait-timeout 120
```

数据未清空且迁移脚本未更新时，不需为了普通停启重复初始化或创建验收任务。源码更新需要重新构建镜像，并由Compose更新API容器；已有容器不会自动读取本机源码。生产发布、容器替换和删除等操作应按实际授权及备份流程另行执行。

### 数据保存与已验证范围

命名卷postgres_data挂载到PostgreSQL 18容器的/var/lib/postgresql，实际卷名默认带Compose项目名前缀。复用同一实际卷并使用兼容数据库版本可保留数据；换项目名可能使用另一卷，仅复用相同容器内路径不够。删除卷会删除这份数据库存储，不要未经确认执行带卷删除的清理；卷也不代替备份。跨PostgreSQL大版本升级需要独立升级流程。

已验证镜像构建、空库迁移、API查询和创建、服务停启，以及替换数据库容器后复用原卷读回任务。未验证Windows重启后的完整恢复、数据库备份恢复演练、生产部署或全套测试在容器中运行。源码构建时顶层依赖固定版本，但传递依赖尚未完整锁定。

构建拉取失败应先区分Docker Hub与PyPI连接；曾出现间歇性TLS中断并在原样重试后成功。索引获取失败后的No matching distribution不独自证明包版本不存在，不据此直接关闭证书校验或改版本。需要时先保留失败步骤和前面的网络错误。

## 旧JSON一次性导入

导入前需要安装依赖、预先创建并迁移目标数据库，在同一终端设置密码与TASK_MANAGER_DB_NAME。第一版只接受任务表为空的目标库；标签可以已有。原库已有练习任务时会拒绝导入，不会清空、覆盖或合并任务。

先查看帮助（不需要连接数据库）：

```powershell
python legacy_import.py --help
```

以下命令会真实写入所选数据库，执行前确认目标和源文件；先在独立空任务测试库验证，不对已有任务的原库直接运行：

```powershell
$env:TASK_MANAGER_DB_PASSWORD = "你的数据库密码"
$env:TASK_MANAGER_DB_NAME = "预先创建并完成迁移的目标数据库名"
python legacy_import.py "data/tasks.json"
```

路径可为绝对路径；相对路径以终端当前目录为基准，含空格时使用引号。输入顶层必须是任务列表，例如：

```json
[
    {"id": 3, "title": "旧任务", "done": true, "priority": "high", "tags": ["Python"]}
]
```

id为必填严格正整数且文件内不能重复；title为必填严格字符串，清理首尾空白后长度1～100。缺失done、priority、tags时分别补false、normal、[]；显式null不接受。done只接受布尔值，字符串"false"和数字0均拒绝。priority清理并转小写后须为low/normal/high；tags须为字符串列表，清理、转小写、拒绝空白并保留首次出现顺序去重。额外字段当前按Pydantic默认行为忽略。

全部记录先校验，再开启同一个事务写入。复用规范化标签，保留完成状态及优先级，由数据库生成新ID及导入时间created_at；旧文件没有真实创建时间。成功提交后先打印任务数量，再打印Python字典形式的旧ID→新ID对照。失败则回滚本批写入，源文件不修改；文件、数据及SQLAlchemy异常显示失败原因并以1退出，参数用法错误退出2，帮助和成功退出0。缺失密码环境变量属于配置错误，当前会直接报KeyError，应先配置。

首次成功导入非空数据后，再次运行因目标已有任务而拒绝；空文件列表只返回空映射，不产生导入标记。此版本定位本地单次导入，不支持并发导入防重、断点续传或持续同步，也不恢复旧ID。旧CLI此后产生的新数据不会自动同步至数据库。

## 自动化测试

先创建并迁移独立测试库，在设置密码的同一终端执行：

```powershell
$env:TASK_MANAGER_DB_NAME = "task_manager_migration_test"
python -m alembic upgrade head
python -m pytest -q
```

数据库测试使用外层事务和保存点隔离，结束后回滚测试写入；PostgreSQL序列编号仍可能前进。运行API前请显式把数据库名切换回预期目标，环境变量的值会被同一终端启动的新进程继承。

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
| `tag` | string | `python` | 按标签过滤，不区分大小写 |

多个条件可以组合使用：

```http
GET /tasks?priority=high&done=false&keyword=python&tag=backend
```

响应示例：

```json
[
    {
        "id": 1,
        "title": "学习 FastAPI",
        "done": false,
        "priority": "high",
        "tags": ["python", "backend"],
        "description": ""
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
    "priority": "high",
    "tags": ["Python", "FastAPI"],
    "description": "练习请求校验和数据库保存"
}
```

- `title` 必填，清理首尾空白后长度必须为 1～100；
- `priority` 可省略，默认值为 `normal`；
- `description` 可省略，默认空字符串；清理首尾空白后最多500字符，允许空串或纯空白，显式 `null`、非字符串或超长输入返回422；
- `tags` 可省略，默认值为空列表；每个标签会清理首尾空白并转成小写；
- `id` 由服务器生成；
- `done` 由服务器设置为 `false`。

成功时返回 `201 Created` 和新任务：

```json
{
    "id": 2,
    "title": "学习创建任务接口",
    "done": false,
    "priority": "high",
    "tags": ["python", "fastapi"],
    "description": "练习请求校验和数据库保存"
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
    "priority": "normal",
    "tags": ["Python", "Web"]
}
```

当前支持更新 `title`、`priority`、`tags` 和 `description`。省略字段时保留原值，`tags: []` 会清空标签，显式传入 `null` 会返回 `400 Bad Request`。标签中的空白字符串不合法。备注清理首尾空白后最多500字符；空串或纯空白会清空备注，非字符串或超长备注返回422。所有使用TaskResponse的任务响应均包含字符串description。

已有数据库需先执行 `python -m alembic upgrade head`，通过备注迁移 `7fd5a8884f29` 新增非空description列，旧任务备注补为空字符串。仅更新Python代码或重新构建镜像不会自动升级数据库。旧JSON导入格式本轮不扩展备注，导入任务使用默认空字符串。

### 完成任务

```http
PATCH /tasks/2/complete
```

成功后任务的 `done` 为 `true`。重复请求会继续保持 `done=true`。

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
| `400 Bad Request` | 业务输入不合法 | 非法优先级、空白筛选条件、更新字段为 `null` |
| `404 Not Found` | 资源不存在 | 查询、更新或删除不存在的任务 |
| `422 Unprocessable Entity` | 请求没有通过模型校验 | 缺少标题、标题过长、路径 ID 不是整数 |
| `500 Internal Server Error` | 服务器内部处理失败 | 未处理的数据库连接错误等服务器异常 |

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

CLI 仍使用旧的 `TaskManager`、数据模型和 JSON 文件；它与正式 Web API 的 PostgreSQL 数据互不同步。

## 数据存储

正式 Web API 使用 PostgreSQL 的三张表：

| 表 | 作用 |
| --- | --- |
| `tasks` | 保存任务的标题、完成状态、优先级和创建时间 |
| `tags` | 保存唯一的规范化标签名称 |
| `task_tags` | 通过 `task_id` 和 `tag_id` 表示任务与标签的多对多关系 |

SQLAlchemy Session 跟踪 ORM 对象变化；Repository 执行查询、`add()`、`delete()` 和 `flush()`，Router 在成功的写请求边界执行 `commit()`。任务删除后，中间表中的对应关系通过外键级联删除，标签记录可以继续被其他任务复用。

`data/tasks.json` 只供保留的旧 CLI 使用，不再是正式 Web API 的数据源。

## 任务 ID

任务 ID 由 PostgreSQL identity 列生成。应用不根据列表位置或当前最大值自行计算 ID；删除任务后也不应依赖后续 ID 是否连续。

ID 表示任务身份，不是任务在 Python 列表中的位置。

## 后续规划与学习记录

PostgreSQL、SQLAlchemy ORM、Alembic结构迁移、旧JSON一次性导入及事务隔离自动化测试已经接入。Docker Compose已验证独立数据库初始化、迁移、API读写及同卷重建持久化；阶段四仍需独立复现与交付收束。真实历史文件导入需另行确认执行目标。

已完成阶段、知识点大纲、验收记录及当前学习进度统一记录在 [PROGRESS.md](PROGRESS.md)。导师教学方式与操作约束见 [AGENTS.md](AGENTS.md)。本文件继续作为项目功能、接口与运行方式的说明。
