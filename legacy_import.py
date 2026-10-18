import json
import argparse

from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel,ConfigDict,Field,field_validator,StrictStr

from task_repository import TaskRepository
from task_service import TaskService


class LegacyTaskInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,

    )

    title: str = Field(min_length=1,
                       max_length=100,
                       strict=True,
                       )

    done: bool = Field(default=False,
                       strict=True,
                       )

    id:int = Field(
        strict=True,
        gt=0,
    )

    tags:list[StrictStr] = Field(
        default_factory=list,
        strict=True,

    )

    priority:str = Field(
        default="normal",
        strict=True,
    )

    @field_validator("tags",mode="after")
    @classmethod
    def validate_tags(
        cls,
        values: list[StrictStr],
    )->list[StrictStr]:

        cleaned_values: list[StrictStr] = []
        for value in values:
            cleaned_value=value.lower()

            if not cleaned_value:
                raise ValueError(
                    "Tag must not be empty"
                )

            if cleaned_value not in cleaned_values:
                cleaned_values.append(cleaned_value)

        return cleaned_values

    @field_validator("priority",mode="after")
    @classmethod
    def validate_priority(
        cls,
        value:str,
    )->str:
        value = value.lower()

        if value not in ["normal","high","low"]:
            raise ValueError(
                "Priority must be one of 'normal','high','low'"
            )

        return value

def load_legacy_tasks(
        file_path: Path,
) -> list[LegacyTaskInput]:

    with open(file_path,"r",encoding="utf-8") as f:
        data = json.load(f)

        if not isinstance(data,list):
            raise ValueError(
                "Not a list"
            )

        res_list=[]
        seen_ids=set()


        for item in data:

            task_temp=LegacyTaskInput.model_validate(item)
            if task_temp.id not in seen_ids:
                seen_ids.add(task_temp.id)

                res_list.append(task_temp)

            else:
                raise ValueError(
                    f"Duplicate legacy task id: {task_temp.id}"
                )


    return res_list

def import_legacy_tasks(
        session: Session,
        tasks:list[LegacyTaskInput],
)->dict[int,int]:

    repository = TaskRepository(session)

    stats=repository.get_stats()

    if stats["total"]!=0:
        raise ValueError(
            "Target database already contains tasks"
        )

    service=TaskService(repository)

    id_mapping={}
    for task in tasks:
        new_task=service.create_task(
            title=task.title,
            priority=task.priority,
            tags=task.tags,
        )
        new_task.done=task.done
        id_mapping[task.id]=new_task.id

    session.flush()
    return id_mapping

def import_legacy_file(
        file_path:Path
)->dict[int,int]:

    list_tasks=load_legacy_tasks(file_path)

    from database import SessionFactory
    with SessionFactory.begin() as session:

        id_mapping=import_legacy_tasks(session,list_tasks)

    return id_mapping

def main():
    # 【当前整体功能】
    # main是命令行入口：接收JSON路径，交给import_legacy_file完成读取、校验及事务导入，
    # 成功提交并返回ID映射后，打印导入数量与旧新ID对照。
    # 真实执行会读取文件并写入环境配置指定的数据库，不再只是预览路径。
    #
    # 【一条具体命令的完整执行路线】
    # 用户在项目目录运行：python legacy_import.py data/tasks.json
    # Python准备启动参数：sys.argv通常为["legacy_import.py", "data/tasks.json"]。
    # 本函数创建解析器 → 登记file_path的规则 → 读取启动参数并转换
    # → 得到类似Namespace(file_path=Path("data/tasks.json"))的结果
    # → 调用import_legacy_file → 成功提交 → 打印数量和映射。
    # sys.argv是sys模块保存的字符串列表。这里没有显式写sys.argv，
    # 因为parse_args()在未传args参数时，会在库内部读取sys.argv[1:]。

    # ① 创建“参数解析器”对象，用parser变量保存；不是在这里执行文件导入。
    # argparse是标准库模块，ArgumentParser是其中的类；调用后返回解析器实例。
    # description是帮助页中的功能说明，不是用户输入，也不是参数名称。
    # 默认add_help=True，解析器因此还会自动支持-h和--help。
    parser = argparse.ArgumentParser(description="导入旧任务JSON")

    # ② 向解析器登记一条参数规则。登记规则不等于已经读取运行参数。
    # add_argument返回参数配置对象，这里不接收，因为后续由parser自己管理规则。
    # "file_path"不带短横线，所以它是必填的位置参数：命令中直接写一个路径即可。
    # 此字符串只决定解析结果的属性名：后面通过args.file_path取得用户输入。
    # 它不是要转换的文件名；真正被转换的是用户提供的data/tasks.json。
    # 【通俗理解：先设计表格，再填写内容】
    # 解析器不会凭空知道命令后的文字表示什么，我们先告诉它：程序需要一个路径。
    # add_argument像“设计一个待填写的表格”：
    #   字段名=file_path；必填=是；接收内容后用Path转换。
    # 现在还没有填写内容，"file_path"也不是用户必须输入的路径文字。
    # 用户将来执行python legacy_import.py data/tasks.json，提供的是data/tasks.json；
    # 下面parse_args才像“把用户提供的内容填进表格”，按上述规则保存和转换。
    # 若登记名改为source，实际命令的位置输入仍可一样，只是结果改用args.source访问。
    parser.add_argument(
        "file_path",
        # Path是已经导入的pathlib.Path类。这里不加括号，是把转换工具交给解析器。
        # parse_args读取到实际字符串后，再调用类似Path("data/tasks.json")的转换。
        # Path只表示一个位置，不自动创建文件，不验证文件存在，也不读取文件内容。
        # 相对路径后续按进程的当前工作目录解释，不自动以本py文件的目录为基准。
        type=Path,
        # help只用于帮助页中解释这个参数，既不是默认路径，也不是实际输入值。
        help="旧JSON文件路径",
    )

    # ③ 真正开始读取并解析参数。这是整个入口的数据获取和分支处理点。
    # parser是解析器实例；调用的是实例方法parser.parse_args()，
    # 不是直接调用模块上的argparse.parse_args()。
    # 本次没有向parse_args传参数，所以它读取当前进程的sys.argv[1:]。
    # [1:]跳过第一项程序名，例如只取出["data/tasks.json"]。
    # 随后按登记的规则，把输入字符串转成Path，放到Namespace对象的file_path属性。
    # args保存这个Namespace对象；args不是列表，不是路径，也不是文件内容。
    # 例如：args.file_path的值是Path("data/tasks.json")。
    # 对应前面的表格类比：这里才真正“填表”。
    # 具体值路线：用户的"data/tasks.json" → Path("data/tasks.json")
    # → 放入返回对象的file_path属性 → args引用这个返回对象 → args.file_path取得路径。
    # 可以近似想成args.file_path = Path("data/tasks.json")，
    # 但真正工作是parse_args依据已登记规则完成的，不是将名字"file_path"转换成路径。
    #
    # 这里有三个分支：
    # A. 提供路径：正常返回Namespace，完成args赋值，继续调用导入函数。
    # B. 没有路径：argparse内部向标准错误输出缺参说明，抛SystemExit(2)。
    #    此时args赋值未完成，main被中断，不执行导入和成功输出。
    # C. 输入--help：argparse打印帮助，抛SystemExit(0)，不导入或打印成功结果。
    # SystemExit是Python内置退出异常；0表示正常结束，2表示这里的参数用法错误。
    # 这些异常由库内部产生，不需要我们在main中自己写raise才能发生。
    args = parser.parse_args()

    # ④ 将解析后的Path传给导入入口，不再只打印路径。
    # 例如读取旧ID为3、8的两条任务，提交成功后返回{3: 101, 8: 102}。
    # 如果读取、校验、数据库写入或提交失败，异常从此处传出，下面成功输出不执行。

    try:
        mapping=import_legacy_file(args.file_path)



    # 文件、数据校验或SQLAlchemy数据库错误到达这里时，内部事务块已先回滚（如已开启）。
    # error是实际异常对象；f-string会把它转成说明文字，而不是固定输出“具体原因”。
    except (OSError,ValueError,SQLAlchemyError) as error:

        # exit将message写入标准错误并抛SystemExit(1)，因此后面成功print不会执行。
        # 与parse_args缺参时的退出2不同，1表示本程序导入操作失败。
        parser.exit(
            status=1,
            message=f"导入失败，{error}\n",
        )

    # ⑤ 返回映射的条目数就是导入任务数量；示例先输出2，再换行。
    print(len(mapping))

    # 输出旧ID→新ID对照；示例为{3: 101, 8: 102}。
    # 这些输出发生在事务成功之后；main本身无显式return，正常返回None。
    print(mapping)


# 直接运行本文件时__name__为"__main__"，才进入main解析命令行参数。
# 被测试文件通过import导入时__name__为"legacy_import"，这里只定义main，不执行它。
# 测试随后显式调用main()才会进入上面的函数体。
if __name__ == "__main__":
    main()
