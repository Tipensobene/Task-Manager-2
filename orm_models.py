from sqlalchemy import Boolean,Column,ForeignKey,Integer,Table,Text,Identity,text,DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationship
from datetime import datetime
# 字符串形式相当于告诉 SQLAlchemy：
# 先保存这个字符串，等所有模型定义完成后再解析。
class Base(DeclarativeBase):
    pass

task_tags_table=Table(
    'task_tags',
    # Base 保存的表结构登记册
    Base.metadata,
    Column(
        "task_id",
        Integer,
        ForeignKey(
            "tasks.id",
            ondelete="CASCADE",
        ),
        primary_key=True
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey(
            "tags.id",
            ondelete="CASCADE",
        ),
        primary_key=True
    ),
)


class TaskRecord(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(
        Identity(always=True),
        primary_key=True,

    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    done: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    priority: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="normal",
        server_default=text("'normal'"),
    )
    # 通过中间关联表建立的多对多关系
    tags:Mapped[list["TagRecord"]]=relationship(
        secondary=task_tags_table,
        back_populates="tasks",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),

    )

    description:Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )

class TagRecord(Base):
    __tablename__ = 'tags'
    id:Mapped[int]= mapped_column(
        Identity(always=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False,unique=True)
    tasks:Mapped[list["TaskRecord"]]=relationship(
        secondary=task_tags_table,
        back_populates="tags",
    )