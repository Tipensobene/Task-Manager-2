import json

from models import Task
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR/"tasks.json"
TEMP_DATA_FILE=DATA_DIR/"tasks_tmp.json"

class StorageError(Exception):
    pass



def save_tasks(tasks:list[Task]) -> None:
    try:

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        tasks_dict=[]
        for task in tasks:

            task_temp=task.to_dict()
            tasks_dict.append(task_temp)

        with open(TEMP_DATA_FILE,"w",encoding="utf-8") as f:
            json.dump(
                tasks_dict,
                f,
                ensure_ascii=False,
                indent=4
            )

        TEMP_DATA_FILE.replace(DATA_FILE)

    except OSError as error:
        raise StorageError("保存任务文件失败") from error

def load_tasks() -> list[Task]:


    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:

            data=json.load(f)

            tasks=[]

            for item in data:

               task=Task.from_dict(item)

               tasks.append(task)

    except FileNotFoundError:
        print("未找到文件")
        return []

    except json.JSONDecodeError as error:

        raise StorageError("任务数据文件格式错误") from error



    except OSError as error:

        raise StorageError("读取任务文件失败") from error

    return tasks




