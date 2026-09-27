from dataclasses import dataclass,asdict


@dataclass
class Task:
    id:int
    title:str
    done:bool=False

    def complete(self):
        self.done=True

        return None

    def to_dict(self):
        return asdict(self)

    def rename(self,newtitle:str):
        self.title=newtitle

    @classmethod
    def from_dict(cls,data):
        return cls(**data)

if __name__ == '__main__':
    t1=Task(1,"Task 1")

    print("t1的内容：",t1)

    t1.complete()

    print("调用complete后 t1的内容：",t1)

    t1_dict=t1.to_dict()
    print(t1_dict)

    t1.rename("test1")
    print("rename后：",t1)

    t1_ret1=t1.from_dict(t1_dict)
    print(t1_ret1)




