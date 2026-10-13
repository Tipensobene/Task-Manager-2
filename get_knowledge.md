# 学习问题与知识沉淀

> 2026-10-09路径调整：文中早期数据库实验文件名保留不变，Psycopg脚本现位于`examples/database/psycopg/`，SQLAlchemy和ORM脚本位于`examples/database/sqlalchemy/`。旧示例中的直接脚本运行命令请改用[数据库实验运行说明](examples/database/README.md)中的模块方式；公共`database.py`、`orm_models.py`和`database_api_demo.py`仍在根目录。

## pytest共享fixture：`conftest.py`

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
| 抛出预期的`ValueError` | 该异常断言通过 |
| 没有抛出异常 | 测试失败，提示没有抛出预期异常 |
| 抛出其他异常类型 | 其他异常继续传播，测试失败 |

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
