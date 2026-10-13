# 数据库教学实验

本目录保留阶段四的13个教学脚本，文件名和实验逻辑保持原样。

- `psycopg/`：连接查询、约束异常、事务回滚，共3个脚本。
- `sqlalchemy/`：Core连接与参数化、公共数据库模块、ORM查询、关系加载和提交/回滚，共10个脚本。
- 项目根目录的 `database.py`、`orm_models.py` 为公共实现，`database_api_demo.py` 是当前数据库接口入口。
- `tests/` 是可重复运行的自动化测试，不属于本目录。

## 运行方式

工作目录设为项目根目录 `D:\Python\Project\Task_Managers_2`，用模块名运行，省略 `.py`：

```powershell
& "D:\Python\Project\.venv\Scripts\python.exe" -m examples.database.psycopg.db_connection_demo
& "D:\Python\Project\.venv\Scripts\python.exe" -m examples.database.sqlalchemy.orm_query_demo
```

其他脚本同理替换最后的模块名。模块方式使根目录中的 `orm_models` 和 `database` 可被正确导入，无需修改 `sys.path`。

PyCharm 使用“运行 → 编辑配置”，选择 Python 配置，把运行目标设为“模块名称”，填写例如 `examples.database.sqlalchemy.orm_query_demo`；工作目录设为项目根目录，解释器选择上述虚拟环境。原来指向根目录脚本的旧配置需要更新。

多数脚本会交互式读取密码；使用 `getpass` 的脚本建议在终端运行。`database_module_demo` 读取进程环境变量 `TASK_MANAGER_DB_PASSWORD`，需要在运行配置中提供。

## 实验数据影响

教学脚本不是自动隔离测试。尤其 `orm_insert_commit_demo` 会提交真实数据；约束实验是否写入取决于实际分支。复习时先查看脚本内容，再决定运行哪个实验。目录整理验证只检查语法、模块定位和导入来源，不批量执行这些脚本。
