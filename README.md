# Task Manager 2.0

## 项目简介

Task Manager 2.0 是一个使用 Python 开发的命令行（CLI）任务管理系统，支持任务的增删改查、优先级管理、搜索、统计，并通过 JSON 文件实现数据持久化、通过 logging 记录关键操作日志。

本项目是对之前完成的 Task Manager 的**重新构建（Rebuilding）**：在功能不变的前提下，把原来集中的代码拆分为**模块化、分层**的结构（数据模型 / 业务逻辑 / 存储 / 工具），以提高代码的可维护性与可扩展性。

本次重构主要训练以下能力：

- Python 模块化开发与分层设计（models / service / storage / utils）
- 面向对象编程（dataclass 数据类）
- JSON 数据持久化（对象与 JSON 之间的相互转换）
- 异常处理与输入校验
- logging 日志记录与装饰器（Decorator）的使用
- 类型注解（Type Hints）
- 旧数据兼容（字段缺失时用默认值兜底，不破坏已有数据）
- Git 分支开发流程（feature branch → commit → merge）

## 功能

目前已实现：

| 功能 | 说明 |
| ---- | ---- |
| 添加任务 | 输入任务名称与优先级，自动分配 ID；空名称会被拒绝 |
| 任务优先级 | 支持 low / normal / high 三级；回车默认 normal，输入不区分大小写（如 HIGH → high），非法值会提示并重新输入 |
| 查看任务 | 按 ID、状态、优先级、名称的表格形式列出所有任务 |
| 按优先级查看任务 | 输入优先级，只列出该优先级的任务 |
| 完成任务 | 按 ID 将任务标记为完成；已完成的会提示错误 |
| 删除任务 | 按 ID 删除任务；不存在的 ID 会提示错误 |
| 搜索任务 | 按关键词模糊匹配任务名称（不区分大小写） |
| 查看未完成任务 | 只列出尚未完成的任务 |
| 统计信息 | 显示总任务数、已完成数、未完成数 |
| JSON 持久化 | 任务数据自动保存到 `data/tasks.json`，重启后不丢失 |
| 输入校验 | ID 必须为合法整数，非法输入会提示并允许重新输入 |
| Logging | 添加、完成、删除操作自动写入日志文件 |

## 项目结构

```
Task_Managers_2/
├── main.py           # 程序入口：CLI 菜单循环，负责与用户交互并展示结果
├── models.py         # 数据模型：Task 数据类及其与字典互转的方法
├── service.py        # 业务逻辑：TaskManager 类，实现任务的增删改查、优先级筛选、搜索、统计
├── storage.py        # 持久化：任务的保存（save）与加载（load），路径管理
├── utils.py          # 工具：logging 配置、整数输入校验、日志装饰器
├── data/             # 数据目录：存放 tasks.json（首次运行自动创建，已加入 .gitignore）
├── logs/             # 日志目录：存放 tasks_manager.log（自动创建，已加入 .gitignore）
├── .gitignore        # 忽略缓存、虚拟环境、IDE 配置、日志与数据文件
└── README.md
```

各模块职责：

- **main.py**：唯一与用户交互的地方。显示菜单、读取用户输入、调用 service 层、打印结果与错误信息。
- **models.py**：定义 `Task` 数据类（`id`、`title`、`done`、`priority`），并提供 `complete()`、`to_dict()`、`from_dict()` 等方法；`from_dict()` 对缺失字段用 `.get()` 提供默认值（`done=False`、`priority="normal"`），保证旧版本数据可以直接加载。
- **service.py**：核心业务逻辑。`TaskManager` 类负责所有任务操作，并在增删改后自动调用 storage 保存；`add_task()` 校验并规范化优先级（去空格、转小写、空值默认为 normal），`search_by_priority()` 按优先级筛选任务。
- **storage.py**：负责把 `Task` 对象列表写入 `data/tasks.json` 或从中读回，处理文件不存在、格式错误等异常。
- **utils.py**：集中配置 logging；提供 `get_valid_int()` 做输入校验、`log_operation()` 装饰器统一记录日志。

## 如何运行

需要 Python 3.10+（代码使用了 `match-case` 与 `list[Task]`、`Task | None` 等新语法）。

```bash
python main.py
```

启动后按菜单输入数字序号即可操作：

```
============================
      Task Manager 2.0
============================

1. 添加任务
2. 查看任务
3. 完成任务
4. 删除任务
5. 搜索任务
6. 查看未完成任务
7. 查看统计信息
8. 按优先级查看任务
0. 退出
```

添加任务时，会依次提示输入任务名称与优先级：

```
请输入名称：
请输入任务优先级[low/normal/high]（回车默认 normal）：
```

优先级输入规则：

- 直接回车 → 默认为 `normal`
- `low` / `normal` / `high`（不区分大小写，如 `HIGH` 会保存为 `high`）
- 其他输入 → 提示 `优先级不合法，请输入 low / normal / high`，任务不会被添加

## 数据存储

任务数据保存在 `data/tasks.json`，该文件（及目录）在首次写入时自动创建。

- **写入（Task → dict → JSON）**：保存时先通过 `Task.to_dict()`（基于 `dataclasses.asdict`）把每个 `Task` 对象转换为字典，再用 `json.dump` 写入文件（`ensure_ascii=False` 保证中文可读，`indent=4` 便于阅读）：

```json
[
    {
        "id": 1,
        "title": "学习 Git",
        "done": false,
        "priority": "normal"
    },
    {
        "id": 2,
        "title": "学习 Python",
        "done": true,
        "priority": "high"
    }
]
```

- **读取（JSON → dict → Task）**：加载时先用 `json.load` 把文件解析为字典列表，再通过 `Task.from_dict()` 将每个字典还原为 `Task` 对象。

读取过程中对 `FileNotFoundError`、`json.JSONDecodeError`、`OSError` 分别做了处理，文件缺失或损坏时程序不会崩溃，而是以空列表启动。

**旧数据兼容**：早期版本保存的 `tasks.json` 中没有 `priority`（甚至 `done`）字段，`Task.from_dict()` 使用 `data.get("priority", "normal")` 等默认值兜底，旧文件可以正常加载，缺失优先级的任务会显示为 `normal`。

## 日志

运行日志记录在 `logs/tasks_manager.log`，格式为 `时间 级别 消息`，由 `utils.py` 统一配置。

通过 `@log_operation(...)` 装饰器自动记录以下操作：

- 添加任务
- 完成任务
- 删除任务

示例：

```
2026-09-29 14:44:40 INFO Added task: 马上结束了！
2026-09-29 14:46:15 INFO Completed tasks: 学无止境啊
2026-09-29 14:46:23 INFO Deleted tasks: 马上结束了！
```

## 技术点

| 技术 | 应用位置 |
| ---- | ---- |
| Python | 整体实现，使用 `match-case` 等新语法（3.10+） |
| dataclass | `Task`、`TaskManager` 数据类；`Task` 含 `priority` 字段（默认 `normal`） |
| JSON | 任务数据的持久化与恢复 |
| pathlib | 用 `Path` 管理数据与日志文件的路径 |
| 异常处理 | 空标题 / 非法 ID / 非法优先级 / 文件缺失与损坏等场景 |
| 旧数据兼容 | `Task.from_dict()` 用 `.get()` 为缺失字段提供默认值，旧 JSON 直接可加载 |
| 类型注解 | 函数参数与返回值标注（如 `list[Task]`、`Task \| None`） |
| logging | 关键操作日志记录 |
| 装饰器 | `log_operation` 装饰器为增删改操作统一附加日志 |
| Git | 分支开发流程与提交历史管理 |

## Git 开发方式

本项目采用分支开发流程（feature branch → commit → merge）：

- **main**：稳定主线，只保留可运行、已验证的版本。
- **feature/task-service**：业务逻辑开发分支（数据模型、JSON 存储、任务服务）。
- **feature/cli**：命令行界面开发分支（菜单、交互与展示）。
- **feature/task-priority**：任务优先级功能开发分支（`priority` 字段、优先级输入校验、按优先级筛选、旧数据兼容），当前开发所在分支。

流程说明：

1. 从 `main` 创建 `feature/*` 分支；
2. 在分支上按模块小步提交（如 `feat: add task model` → `feat: add json task storage` → `feat: add task management service`）；
3. 功能完成并验证后合并回 `main`。

## 后续计划

**Task Manager 3.0**：将现有命令行程序升级为 FastAPI REST API，把 `TaskManager` 业务逻辑暴露为 HTTP 接口（如 `POST /tasks`、`GET /tasks`、`PUT /tasks/{id}`、`DELETE /tasks/{id}`），供前端或其他客户端调用。
