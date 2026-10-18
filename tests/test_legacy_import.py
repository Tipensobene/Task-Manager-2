import pytest
import json
import sys
import legacy_import
from pathlib import Path
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from legacy_import import LegacyTaskInput,load_legacy_tasks,main


def test_main_imports_supplied_path_and_prints_result(
        tmp_path,
        monkeypatch,
        capsys
):
    # 【各种path名字的关系：用一个具体值贯穿】
    # 假设pytest提供tmp_path=Path("C:/temp/case1")，按下面顺序执行：
    # 1. 测试变量file_path = tmp_path / "source tasks.json"，得到预期Path对象。
    # 2. str(file_path)转成文字，放到sys.argv[1]，模拟用户的启动输入。
    # 3. 这里只登记fake_import_file函数，不执行；它的形参path此时还没绑定实参。
    # 4. monkeypatch将模块内import_legacy_file名称临时指向fake_import_file。
    # 5. 测试调用main；main的parse_args读取sys.argv[1]，按type=Path转回路径对象，
    #    放入Namespace的file_path属性，即main内部的args.file_path。
    # 6. main执行import_legacy_file(args.file_path)，实际调用替代函数，
    #    等价于fake_import_file(args.file_path)。此时实参才绑定到形参path。
    # 7. 替代函数把收到的Path加入received_paths，再返回预设ID映射给main。
    # 8. main打印结果并返回后，测试比较“实际收到的路径”和“最初预期路径”。
    #
    # 因此整条链是：
    # 测试的file_path → str后放sys.argv[1] → main的args.file_path
    # → 替代函数的path → received_paths[0]。
    # file_path和args.file_path来自不同函数的局部作用域，不自动共享变量；
    # 两个Path表示同一位置即可，不要求它们是内存中同一个对象（不用is比较）。
    # 【目标】模拟“用户提供路径”，检查main传递Path并打印导入数量和ID映射。
    # main已接入导入函数；本测试临时替换该函数，不执行真实文件读取或数据库操作。
    # tmp_path：pytest内置fixture，提供本用例独立的临时目录Path对象。
    # monkeypatch：临时修改属性，测试及fixture清理时恢复，不会永久修改启动参数。
    # capsys：捕获当前测试中的标准输出和标准错误，用来检查print或错误说明。

    # 构造路径，不创建文件。假设tmp_path是C:/temp/test_case，
    # 则file_path表示C:/temp/test_case/source tasks.json。
    file_path = tmp_path / "source tasks.json"
    # sys.argv是“程序名+用户参数”的字符串列表。本行分开写模块sys和属性名"argv"，
    # 所以虽然没出现字面量sys.argv，实际修改的正是这个属性。
    # 相当于临时设置sys.argv=["legacy_import.py", "C:/temp/test_case/source tasks.json"]。
    # str(file_path)将Path转回命令行通常提供的字符串；setattr返回None，这里无需接收。
    # 整条路径放在列表的第二个元素中，文件名中的空格不会把它拆成多个参数。
    # 这只测试“已收到的单个参数包含空格”，不测试PowerShell的引号解析；
    # 手动运行对应命令时需类似：python legacy_import.py "C:/temp/test_case/source tasks.json"。
    monkeypatch.setattr(sys, "argv", ["legacy_import.py", str(file_path)])

    # 保存实际收到的参数，以便验证main不是漏调函数或传错值。
    received_paths = []

    def fake_import_file(path):
        # path是普通形参，不是tmp_path fixture，也不是根据名字自动生成的路径。
        # 它接收的是调用时的args.file_path；换名为received_file并同步函数体也一样。
        # 例如此时path=Path("C:/temp/case1/source tasks.json")。
        # 模拟成功导入两条记录；这里只返回预设结果，没有真正导入。
        received_paths.append(path)
        return {3: 101, 8: 102}

    # main在legacy_import模块中查找这个名称，故替换模块上的同名函数。
    # 与替换sys.argv一样，测试结束自动恢复真实函数。
    monkeypatch.setattr(legacy_import, "import_legacy_file", fake_import_file)

    # 进入legacy_import.py中的main，不是运行另一个Python进程。
    # main创建parser并登记规则，再执行parser.parse_args()。
    # parse_args默认读刚替换的sys.argv[1:]，按type=Path转换路径，
    # main把转换后的路径交给fake_import_file，得到映射后打印2和映射。
    main()

    # received_paths记录实际传入值，右侧[file_path]是测试准备的预期值。
    # 列表相等同时要求只有一次调用、路径相等；第二个断言另查实际参数类型为Path。
    # 这里检查的是跨函数参数传递，既不是读取路径内容，也不是比较文件中的任务。
    assert received_paths == [file_path]
    assert isinstance(received_paths[0], Path)
    # .out为标准输出；splitlines()按换行切成列表，不保留末尾换行。
    # 实际输出"2\n{3: 101, 8: 102}\n"应得到下面的两项列表。
    assert capsys.readouterr().out.splitlines() == ["2", "{3: 101, 8: 102}"]
    # Path.exists()无参数，检查路径是否存在并返回bool，不创建或删除文件。
    # not取反：不存在时False变True，assert通过。
    # 此处使用替代导入函数，没人创建文件，所以应仍不存在；不是说真实导入不读文件。
    # 这个断言仅证明指定文件未产生，不单独保证程序没有任何其他副作用。
    assert not file_path.exists()
    # 测试结束后pytest清理monkeypatch，原来的sys.argv恢复，后续测试不继承本次值。


def test_main_requires_file_path(
        monkeypatch,
        capsys
):
    # 【目标】模拟python legacy_import.py，缺少必填file_path时应拒绝执行。
    # 启动参数只留下程序名；因此main内部parse_args读取到的sys.argv[1:]是[]。
    monkeypatch.setattr(sys, "argv", ["legacy_import.py"])

    # pytest.raises(SystemExit)返回上下文管理器，用于接住预期的退出异常。
    # as error得到pytest的异常信息对象，不是main的返回值，也不是直接的异常实例。
    # main的创建parser、登记规则两步正常，执行到args=parser.parse_args()时，
    # 解析器发现没有必填位置参数，先打印错误说明，再在库内部抛SystemExit(2)。
    # 异常向外传出main，这次args赋值、导入和成功输出都不执行；pytest接住后继续断言。
    # 如果main没有抛退出异常，raises本身就会判测试失败。
    with pytest.raises(SystemExit) as error:
        main()

    # error.value才是捕获的SystemExit异常实例，.code是实例携带的退出状态。
    # argparse用2表示参数用法错误；这与前面任务输入的ValidationError不是同一种错误。
    assert error.value.code == 2
    # 参数错误写到标准错误，所以检查.err，不是.out。
    # in检查子字符串：只要求错误提示提到file_path，不绑定整段提示格式或语言。
    assert "file_path" in capsys.readouterr().err


def test_main_help_exits_successfully(
        monkeypatch,
        capsys
):
    # 【目标】模拟python legacy_import.py --help，应显示帮助并正常结束。
    # 同样只临时修改当前进程的启动参数，不启动子进程，不连接数据库。
    monkeypatch.setattr(sys, "argv", ["legacy_import.py", "--help"])

    # main执行到parse_args()时，识别默认支持的--help，打印帮助后抛SystemExit(0)。
    # 即使file_path是必填参数，单独请求帮助也不需要提供路径。
    # main后面的导入和结果打印不会执行，避免将帮助输出和成功结果混淆。
    # SystemExit也用于正常退出；是否成功要看.code，不能把所有退出异常都当程序错误。
    with pytest.raises(SystemExit) as error:
        main()

    # code=0表示正常退出；前一项缺参测试期望2，两者不能交换。
    assert error.value.code == 0
    # 帮助信息属于正常输出，用.out读取；应介绍已登记的file_path位置参数。
    # 输出来自argparse内部的帮助处理，不是main最后的成功结果。
    assert "file_path" in capsys.readouterr().out


@pytest.mark.parametrize(
    "import_error",
    [
        ValueError("Simulated invalid data"),
        FileNotFoundError("Simulated missing file"),
        SQLAlchemyError("Simulated database failure"),
    ],
)
def test_main_does_not_report_success_when_import_fails(
    tmp_path,
    monkeypatch,
    capsys,
    import_error,
):
    # 【执行路线】替代函数抛数据/文件/数据库错误→main捕获→exit写标准错误并退出1。
    # SQLAlchemyError用例只模拟库异常，不故意中断真实数据库服务。
    # 不应再向标准输出打印成功数量或映射。原始异常在事务入口外被转换，
    # 不改变真实事务函数先回滚再传播的行为；本测试只验证命令行这层转换。
    file_path = tmp_path / "tasks.json"
    monkeypatch.setattr(sys, "argv", ["legacy_import.py", str(file_path)])

    def failed_import(path):
        raise import_error

    monkeypatch.setattr(legacy_import, "import_legacy_file", failed_import)
    # 现在预期捕获的不是原始ValueError，而是parser.exit产生的SystemExit。
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "导入失败" in captured.err
    assert str(import_error) in captured.err

def test_legacy_task_normalizes_valid_input():
    task={
    "id": 3,
    "title": " 学习导入 ",
    "done": True,
    "priority": " HIGH ",
    "tags": [" SQL ", "Python", "sql"],
}
    validated_task=LegacyTaskInput.model_validate(task)

    assert validated_task.id == 3
    assert validated_task.title=="学习导入"
    assert validated_task.done is True
    assert validated_task.priority == "high"
    assert validated_task.tags == ["sql", "python",]

def test_legacy_task_uses_defaults():
    task={
        "id": 1,
        "title": "测试默认值",

    }

    validated_task=LegacyTaskInput.model_validate(task)

    assert validated_task.done is False
    assert validated_task.priority == "normal"
    assert validated_task.tags == []

@pytest.mark.parametrize(
    "invalid_done",
    ["false",0,1,None],

)
def test_legacy_task_rejects_invalid_done(
        invalid_done,

):
    task={
        "id": 1,
        "title":"invalid_done_test",
        "done": invalid_done,
    }

    with pytest.raises(ValidationError):
        LegacyTaskInput.model_validate(task)


@pytest.mark.parametrize(
    "invalid_id",
    [0, -1, "3", 3.0, True, None],

)
def test_legacy_task_rejects_invalid_id(
        invalid_id,
):
    task={
        "id": invalid_id,
        "title":"invalid_id_test",
    }

    with pytest.raises(ValidationError):
        LegacyTaskInput.model_validate(task)

@pytest.mark.parametrize(
    "invalid_title",
    ["", "   ", "a" * 101, 123, None],

)
def test_legacy_task_rejects_invalid_title(
        invalid_title,
):
    task={
        "id": 1,
        "title": invalid_title,
    }

    with pytest.raises(ValidationError):
        LegacyTaskInput.model_validate(task)

def test_legacy_task_accepts_title_at_max_length():

    task={
        "id": 1,
        "title":"a"*100,
    }

    validated_task=LegacyTaskInput.model_validate(task)
    assert validated_task.title=="a"*100

@pytest.mark.parametrize(
    "invalid_priority",
    ["", "   ", "urgent", 123, True, None],

)
def test_legacy_task_rejects_invalid_priority(
        invalid_priority,
):
    task={
        "id": 1,
        "title":"test_invalid_priority",
        "priority": invalid_priority,
    }

    with pytest.raises(ValidationError):
        LegacyTaskInput.model_validate(task)


@pytest.mark.parametrize(
    "valid_priority",
    ["low", "normal", "high"],

)
def test_legacy_task_accepts_valid_priority(
        valid_priority,
):
    task={
        "id": 1,
        "title":"test_priority",
        "priority": valid_priority,
    }

    validated_task=LegacyTaskInput.model_validate(task)

    assert validated_task.priority == valid_priority


@pytest.mark.parametrize(
    "invalid_tags",
    ["python", None, [123], [None], [""], ["   "]],
)
def test_legacy_task_rejects_invalid_tags(
        invalid_tags,
):
    task={
        "id": 1,
        "title":"test_invalid_tags",
        "tags": invalid_tags,
    }

    with pytest.raises(ValidationError):
        LegacyTaskInput.model_validate(task)

@pytest.mark.parametrize(
    "incomplete_data",
    [
        {"title": "缺少编号"},
        {"id": 1},
    ]
)
def test_legacy_task_rejects_missing_required_fields(
        incomplete_data,
):
    task=incomplete_data

    with pytest.raises(ValidationError):
        LegacyTaskInput.model_validate(task)


def test_legacy_task_accepts_empty_tags():
    task={
        "id": 1,
        "title":"empty_tags_test",
        "tags": [],
    }

    validated_task=LegacyTaskInput.model_validate(task)
    assert validated_task.tags == []

def test_load_legacy_tasks_accepts_empty_list(
        tmp_path
):

    file_path = tmp_path / "tasks.json"

    with open(file_path,"w",encoding="utf-8") as file:
        json.dump([],file)

    result=load_legacy_tasks(file_path)

    assert result == []

def test_load_legacy_tasks_reads_valid_records(
        tmp_path,
):
    file_path = tmp_path / "tasks.json"
    with open(file_path,"w",encoding="utf-8") as file:
        json.dump(
            [
                {
                    "id": 3,
                    "title": " 第一条任务 ",
                    "done": True,
                    "priority": " HIGH ",
                    "tags": [" SQL ", "sql"],
                },
                {
                    "id": 8,
                    "title": "第二条任务",
                },
            ],
            file,
        )

    result=load_legacy_tasks(file_path)

    assert len(result) == 2

    first_task=result[0]
    assert first_task.id == 3
    assert first_task.title=="第一条任务"
    assert first_task.done is True
    assert  first_task.priority == "high"
    assert first_task.tags == ["sql"]

    second_task=result[1]
    assert second_task.id == 8
    assert second_task.done is False
    assert second_task.priority == "normal"
    assert second_task.tags == []

def test_load_legacy_tasks_rejects_missing_file(
        tmp_path
):
    file_path=tmp_path/"missing.json"

    with pytest.raises(FileNotFoundError):
        load_legacy_tasks(file_path)

def test_load_legacy_tasks_rejects_invalid_json(
        tmp_path
):
    file_path=tmp_path/"invalid.json"

    with open(file_path,"w",encoding="utf-8") as file:

        file.write("[")

    with pytest.raises(json.JSONDecodeError):
        load_legacy_tasks(file_path)


@pytest.mark.parametrize(
    "invalid_data",
    [
        {"id": 1, "title": "任务"},
        "text",
        123,
        None,
    ],
)
def test_load_legacy_tasks_rejects_non_list_root(
        tmp_path,
        invalid_data
):
    file_path = tmp_path / "tasks.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(invalid_data, file)

    with pytest.raises(ValueError, match="Not a list"):
        load_legacy_tasks(file_path)


@pytest.mark.parametrize(
    "invalid_item",
    [123, None, {"id": 2, "title": "错误记录", "done": "false"}],
)
def test_load_legacy_tasks_rejects_invalid_item(
        tmp_path,
        invalid_item
):
    file_path = tmp_path / "tasks.json"
    data = [{"id": 1, "title": "合法记录"}, invalid_item]

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file)

    with pytest.raises(ValidationError):
        load_legacy_tasks(file_path)


@pytest.mark.parametrize(
    "source_ids",
    [[3, 3],
    [3, 8, 3]],
)
def test_load_legacy_tasks_rejects_duplicate_ids(
        tmp_path,
        source_ids
):
    file_path = tmp_path / "tasks.json"
    data = [{"id": source_id, "title": f"任务{index}"}
            for index, source_id in enumerate(source_ids)]

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file)

    with pytest.raises(
            ValueError,
            match="Duplicate legacy task id: 3"
    ):
        load_legacy_tasks(file_path)
