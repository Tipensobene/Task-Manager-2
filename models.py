from dataclasses import dataclass,asdict,field


@dataclass
class Task:
    id:int
    title:str
    done:bool=False
    priority: str="normal"
    tags:list[str]=field(default_factory=list)


    def complete(self):
        self.done=True

        return None

    def to_dict(self):
        return asdict(self)

    def rename(self,newtitle:str):
        self.title=newtitle

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            title=data["title"],
            done=data.get("done", False),
            priority=data.get("priority", "normal"),
            tags=data.get("tags", [])
        )






