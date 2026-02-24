import string
import random

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel,Field,Relationship
from pydantic import model_validator,ValidationInfo
from sqlalchemy import Column,Text,DateTime,func,TEXT,select
from slugify import slugify

from app.database import Session




def generate_random_string(length: int = 4) -> str:
    letters = string.ascii_letters  # Upper + lower
    return ''.join(random.choices(letters, k=length))


def generate_unique_slug(name: str, session: Session, model) -> str:
    """
    Generate a unique slug by checking database.
    """
    base_slug = slugify(name)
    slug = base_slug

    while True:
        statement = select(model).where(model.slug == slug)
        existing = session.exec(statement).first()

        if not existing:
            return slug

        slug = f"{base_slug}-{generate_random_string(4)}"
    

# course model 
class CourseBase(SQLModel):
    name: str = Field(index=True)
    description : str = Field(sa_column=Column(Text),default=None)
    slug: Optional[str] = Field(index=True,sa_column_kwargs={"unique": True})
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=True
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        )
    )
    @model_validator(mode="before")
    @classmethod
    def generate_slug_from_title(cls, data: dict, info: ValidationInfo) -> dict:

        if not isinstance(data, dict):
            return data

        name = data.get("name")
        slug = data.get("slug")

        if name and not slug:

            session: Session = info.context.get("session") if info.context else None

            if session:
                from app.tutorial.models import Course
                data["slug"] = generate_unique_slug(name, session, Course)
            else:
                base_slug = slugify(name)
                data["slug"] = f"{base_slug}-{generate_random_string(4)}"

        return data


class Course(CourseBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    chapters: list["Chapter"] = Relationship(back_populates="course")
    model_config = {"validate_assignment": True}



class CourseCreate(SQLModel):
    name:str
    description : str

class CourseUpdate(SQLModel):
    name: str|None
    description : str

# chapter model 
class ChapterBase(SQLModel):
    name: str = Field(index=True)
    course_id: int | None = Field(default=None,foreign_key='course.id')
    slug: Optional[str] = Field(index=True,sa_column_kwargs={"unique": True})
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=True
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        )
    )
    @model_validator(mode="before")
    @classmethod
    def generate_slug_from_title(cls, data: dict, info: ValidationInfo) -> dict:

        if not isinstance(data, dict):
            return data

        name = data.get("name")
        slug = data.get("slug")

        if name and not slug:

            session: Session = info.context.get("session") if info.context else None

            if session:
                from app.tutorial.models import Chapter
                data["slug"] = generate_unique_slug(name, session, Chapter)
            else:
                base_slug = slugify(name)
                data["slug"] = f"{base_slug}-{generate_random_string(4)}"

        return data

class Chapter(ChapterBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    subchapters: list["SubChapter"] = Relationship(back_populates="chapter")
    course: Optional["Course"] = Relationship(back_populates="chapters")
    

class ChapterCreate(SQLModel):
    name:str 
    course_id:int

class ChapterUpdate(SQLModel):
    name: str = Field(index=True)
    course_id: int | None = Field(default=None,foreign_key='course.id')


# subchapter model

class SubChapterBase(SQLModel):
    name: str = Field(index=True)
    chapter_id: int | None = Field(default=None,foreign_key='chapter.id')
    slug: Optional[str] = Field(index=True,sa_column_kwargs={"unique": True})
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=True
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        )
    )
    @model_validator(mode="before")
    @classmethod
    def generate_slug_from_title(cls, data: dict, info: ValidationInfo) -> dict:

        if not isinstance(data, dict):
            return data

        name = data.get("name")
        slug = data.get("slug")

        if name and not slug:

            session: Session = info.context.get("session") if info.context else None

            if session:
                from app.tutorial.models import SubChapter
                data["slug"] = generate_unique_slug(name, session, SubChapter)
            else:
                base_slug = slugify(name)
                data["slug"] = f"{base_slug}-{generate_random_string(4)}"

        return data

class SubChapter(SubChapterBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    course_content: Optional["CourseContent"] = Relationship(sa_relationship_kwargs={"uselist": False})
    chapter: Optional["Chapter"] = Relationship(back_populates="subchapters")
    

class SubChapterCreate(SQLModel):
    name:str 
    chapter_id:int

class SubChapterUpdate(SQLModel):
    name: str = Field(index=True)
    chapter_id: int | None = Field(default=None,foreign_key='chapter.id')

# content model 

class CourseContentBase(SQLModel):
    content: str = Field(sa_column=Column(Text))
    subchapter_id: int = Field(foreign_key='subchapter.id',unique=True)
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=True
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        )
    )
    

class CourseContent(CourseContentBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    subchapter:Optional[SubChapter] = Relationship(back_populates="course_content")

class CourseContentCreate(CourseContentBase):
    pass

class CourseContentUpdate(SQLModel):
    content: str = Field(sa_column=Column(Text))
    subchapter_id: int = Field(default=None,foreign_key='subchapter.id')







