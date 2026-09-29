from service import TaskManager
from storage import load_tasks
from models import Task
from utils import get_valid_int


def show_menu() -> None:
    print("""
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
""")


def display_tasks(tasks: list[Task]) -> None:
    print(
        f"{'ID':<5}"
        f"{'状态':<8}"
        f"{'优先级':<15}"
        f"{'任务名称':<20}"
    )

    for task in tasks:

        done_flag = "×"
        if task.done:
            done_flag = "√"

        status = f"[{done_flag}]"

        print(
            f"{task.id:<5}"
            f"{status:<8}"
            f"{task.priority:<15}"
            f"{task.title:<20}"
        )

def show_all_tasks(manager:TaskManager) -> bool:
    tasks = manager.list_tasks()

    if not tasks:
        print("暂无任务")
        return False

    display_tasks(tasks)
    return True

def main() -> None:
    manager = TaskManager(load_tasks())

    while True:
        show_menu()

        choice = input("请输入功能序号：\n").strip()

        match choice:

            case "1":
                try:

                    title = input("请输入名称：\n")
                    priority=input("请输入任务优先级[low/normal/high]（回车默认 normal）：\n")

                    added_task = manager.add_task(title, priority)

                    print(f"任务添加成功:{added_task.title}")

                except ValueError as e:
                    print(e)

            case "2":
                show_all_tasks(manager)


            case "3":

                if not show_all_tasks(manager):
                    continue


                try:



                    find_id = get_valid_int("请输入待查询的ID：\n")
                    com_task = manager.complete_task(find_id)
                    print(f"任务已完成：{com_task.title}")


                except ValueError as e:
                    print(e)

            case "4":

                if not show_all_tasks(manager):
                    continue

                try:
                    find_id = get_valid_int("请输入待查询的ID：\n")
                    del_task = manager.delete_task(find_id)
                    print(f"任务已删除：{del_task.title}")

                except ValueError as e:
                    print(e)

            case "5":
                key = input("请输入待查询关键词：\n")

                try:
                    res = manager.search_task(key)

                    if not res:
                        print("当前没有匹配任务！")

                    else:
                        display_tasks(res)

                except ValueError as e:
                    print(e)

            case "6":
                uncompleted_tasks = manager.get_uncompleted_tasks()

                if not uncompleted_tasks:
                    print("当前暂无未完成任务！")

                else:
                    display_tasks(uncompleted_tasks)

            case "7":
                statistics = manager.get_statistics()
                print(
                    f"总任务数：{statistics['total']}\n"
                    f"已完成任务数：{statistics['completed_num']}\n"
                    f"未完成任务数：{statistics['uncompleted_num']}"
                )

            case "8":

                try:
                    priority = input("请输入想要查找的任务优先级：\n")
                    priority_tasks = manager.search_by_priority(priority)

                    if not priority_tasks:
                        print("当前暂无符合您所需优先级的任务！")
                    else:
                        display_tasks(priority_tasks)

                except ValueError as e:
                    print(e)


            case "0":


                print("感谢使用 Task Manager 2.0！")
                break

            case _:
                print("输入不合法请重新输入")


if __name__ == '__main__':
    main()
