import json

from models import Task
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR/"tasks.json"

def save_tasks(tasks:list[Task]) -> None:

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    tasks_dict=[]
    for task in tasks:

        task_temp=task.to_dict()
        tasks_dict.append(task_temp)

    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(
            tasks_dict,
            f,
            ensure_ascii=False,
            indent=4
        )

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

    except json.JSONDecodeError:
        print("文件格式错误,将使用空文件")
        return []

    except OSError as error:
        print("读取文件失败",error)
        return []


    return tasks


if __name__ == '__main__':
    task1 = Task(
        id=1,
        title="学习 Git"
    )

    task2 = Task(
        id=2,
        title="学习 Python"
    )

    tasks_t = [task1, task2]

    save_tasks(tasks_t)

    print("测试load_tasks:")
    print()
    loaded_tasks = load_tasks()
    print(loaded_tasks)

    print(type(loaded_tasks))
    # print(type(loaded_tasks[0]))