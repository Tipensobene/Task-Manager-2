from dataclasses import dataclass

from utils import log_operation
from models import Task
from storage import save_tasks


@dataclass
class TaskManager:
    tasks: list[Task]

    def _generate_next_id(self) -> int:

        used_ids = {task.id for task in self.tasks}

        next_id = 1

        while next_id in used_ids:
            next_id += 1

        return next_id

    def _find_task_by_id(self, task_id: int) -> Task | None:

        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    @log_operation("Added task")
    def add_task(self, title: str,priority:str="normal") -> Task:

        title = title.strip()

        if not title:
            raise ValueError("Task title cannot be empty")

        priority = priority.strip().lower()

        if not priority:
            priority = "normal"
        elif priority not in ["normal", "high", "low"]:
            raise ValueError("优先级不合法，请输入 low / normal / high")

        new_id = self._generate_next_id()

        new_task = Task(id=new_id, title=title, priority=priority)
        self.tasks.append(new_task)

        save_tasks(self.tasks)


        return new_task

    def list_tasks(self) -> list[Task]:
        return self.tasks.copy()

    @log_operation("Completed tasks")
    def complete_task(self, task_id: int) -> Task:

        find_task = self._find_task_by_id(task_id)

        if find_task is None:
            raise ValueError("task cannot be found")

        if find_task.done:
            raise ValueError("task already done")

        find_task.complete()
        save_tasks(self.tasks)


        return find_task

    @log_operation("Deleted tasks")
    def delete_task(self, task_id: int) -> Task:

        find_task = self._find_task_by_id(task_id)
        if find_task is None:
            raise ValueError("task cannot be found")

        self.tasks.remove(find_task)
        save_tasks(self.tasks)

        return find_task

    def search_task(self, keyword: str) -> list[Task]:

        keyword = keyword.strip().lower()

        if not keyword:
            raise ValueError("Search keyword cannot be empty")

        result_list = []

        for task in self.tasks:

            temp_name = task.title.strip().lower()

            if keyword in temp_name:
                result_list.append(task)

        return result_list

    def get_uncompleted_tasks(self) -> list[Task]:
        result_list = []
        for task in self.tasks:
            if not task.done:
                result_list.append(task)

        return result_list

    def get_statistics(self) -> dict:

        total = len(self.tasks)

        uncompleted_num = len(self.get_uncompleted_tasks())

        completed_num = total - uncompleted_num

        return {"total": total,
                "uncompleted_num": uncompleted_num,
                "completed_num": completed_num
                }

    def search_by_priority(self,priority:str) -> list[Task]:


        priority = priority.strip().lower()

        if not priority:
            raise ValueError("优先级不能为空")

        elif priority not in ["normal", "high", "low"]:
            raise ValueError("优先级不合法，请输入 low / normal / high")

        result_list = []
        for task in self.tasks:
            if task.priority == priority:
                result_list.append(task)

        return result_list

    def get_task(self, task_id: int) -> Task | None:
        return self._find_task_by_id(task_id)