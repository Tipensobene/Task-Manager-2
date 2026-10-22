from orm_models import TaskRecord,TagRecord
from task_repository import TaskRepository

class TaskService:
    def __init__(self,repository: TaskRepository):
        self.repository = repository

    def create_task(
            self,
            title: str,
            priority:str="normal",
            tags:list[str]|None=None,
            description:str="",
    )->TaskRecord:

        title = title.strip()
        if not title:
            raise ValueError("Task title cannot be empty")

        priority = priority.strip().lower()
        standard_priority=["low","normal","high"]
        if priority not in standard_priority:
            raise ValueError(
                "Priority must be low, normal, or high"
            )

        if not isinstance(description,str):
            raise ValueError("Description must be a string")

        description = description.strip()
        if len(description)>500:
            raise ValueError("Description cannot be longer than 500 characters")

        cleaned_tags=[]
        if tags is None:
            tags = []
        else:

            for tag in tags:
                cleaned_tag = tag.strip().lower()
                if not cleaned_tag:
                    raise ValueError("Tag cannot be empty")

                if cleaned_tag not in cleaned_tags:
                    cleaned_tags.append(cleaned_tag)

        task = TaskRecord(
            title=title,
            priority=priority,
            description=description,
        )

        task_tags=[]
        for tag_name in cleaned_tags:
            tag_record=self.repository.get_tag_by_name(tag_name)

            if tag_record is None:
                tag_record = TagRecord(name=tag_name)

            task_tags.append(tag_record)

        task.tags = task_tags

        return self.repository.add_task(task)

    def get_task(self,task_id:int)->TaskRecord|None:

        return self.repository.get_by_id(task_id)

    def list_tasks(
            self,
            priority:str|None=None,
            done:bool|None=None,
            keyword:str|None=None,
            tag:str|None=None,
    )->list[TaskRecord]:

        if priority is not None:
            priority = priority.strip().lower()

            if priority not in ["low","normal","high"]:
                raise ValueError("Priority must be low, normal, or high")

        if keyword is not None:
            keyword = keyword.strip().lower()

            if not keyword:
                raise ValueError("Keyword cannot be empty")

        if tag is not None:
            tag = tag.strip().lower()

            if not tag:
                raise ValueError("Tag cannot be empty")

        return self.repository.list_tasks(
            priority=priority,
            done=done,
            keyword=keyword,
            tag=tag,
        )

    def get_stats(self)->dict[str,int]:
        return self.repository.get_stats()

    def complete_task(
        self,
        task_id:int,
    )->TaskRecord|None:
        task=self.repository.get_by_id(task_id)

        if task is None:
            return None

        task.done=True

        return task

    def delete_task(
        self,
        task_id:int,
    )->TaskRecord|None:

        task=self.repository.get_by_id(task_id)

        if task is None:
            return None

        self.repository.delete_task(task)

        return task

    def update_task(
        self,
        task_id:int,
        update_data:dict,
    )->TaskRecord|None:
        task=self.repository.get_by_id(task_id)

        if task is None:
            return None

        for key, value in update_data.items():

            if value is None:
                raise ValueError(f"{key} cannot be null")

        if "title" in update_data:
            cleaned_title = update_data["title"].strip()

            if not cleaned_title:
                raise ValueError("Task title cannot be empty")

            task.title = cleaned_title
        if "priority" in update_data:
            cleaned_priority = update_data["priority"].strip().lower()

            if cleaned_priority not in ["low","normal","high"]:
                raise ValueError("Priority must be low, normal, or high")

            task.priority = cleaned_priority

        if "description" in update_data:

            if not isinstance(update_data["description"],str):
                raise ValueError("Description must be a string")

            cleaned_description = update_data["description"].strip()
            if len(cleaned_description)>500:
                raise ValueError("Description cannot be longer than 500 characters")

            task.description = cleaned_description

        if "tags" in update_data:

            cleaned_tags=[]
            for tag_name in update_data["tags"]:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    raise ValueError("Tag cannot be empty")


                if tag_name not in cleaned_tags:
                    cleaned_tags.append(tag_name)

            task_tags=[]
            for tag_name in cleaned_tags:
                tag_record=self.repository.get_tag_by_name(tag_name)

                if tag_record is None:
                    tag_record = TagRecord(name=tag_name)

                task_tags.append(tag_record)

            task.tags = task_tags




        return task