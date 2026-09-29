from dataclasses import dataclass,asdict


@dataclass
class Task:
    id:int
    title:str
    done:bool=False
    priority: str="normal"


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
            priority=data.get("priority", "normal")
        )






