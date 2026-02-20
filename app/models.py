from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel,Field,Relationship
from pydantic import model_validator
from sqlalchemy import Column,Text,DateTime,func,TEXT
from slugify import slugify

# course model 
class CourseBase(SQLModel):
    name: str = Field(index=True)
    slug: Optional[str] = Field(index=True)
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
    def generate_slug_from_title(cls, data: dict) -> dict:
        """Generates a slug from the title field before validation."""
        if isinstance(data, dict) and "name" in data:
            name = data.get("name")
            if name:
                data["slug"] = slugify(name)
        return data

class Course(CourseBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    chapters: list["Chapter"] = Relationship(back_populates="course")
    model_config = {"validate_assignment": True}



class CourseCreate(CourseBase):
    pass 

class CourseUpdate(SQLModel):
    name: str|None

# chapter model 
class ChapterBase(SQLModel):
    name: str = Field(index=True)
    course_id: int | None = Field(default=None,foreign_key='course.id')
    slug: Optional[str] = Field(index=True)
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
    def generate_slug_from_title(cls, data: dict) -> dict:
        """Generates a slug from the title field before validation."""
        if isinstance(data, dict) and "name" in data:
            name = data.get("name")
            if name:
                data["slug"] = slugify(name)
        return data

class Chapter(ChapterBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    subchapters: list["SubChapter"] = Relationship(back_populates="chapter")
    course: Optional["Course"] = Relationship(back_populates="chapters")
    

class ChapterCreate(ChapterBase):
    pass 

class ChapterUpdate(SQLModel):
    name: str = Field(index=True)
    course_id: int | None = Field(default=None,foreign_key='course.id')


# subchapter model

class SubChapterBase(SQLModel):
    name: str = Field(index=True)
    chapter_id: int | None = Field(default=None,foreign_key='chapter.id')
    slug: Optional[str] = Field(index=True)
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
    def generate_slug_from_title(cls, data: dict) -> dict:
        """Generates a slug from the title field before validation."""
        if isinstance(data, dict) and "name" in data:
            name = data.get("name")
            if name:
                data["slug"] = slugify(name)
        return data

class SubChapter(SubChapterBase,table=True):
    id: int | None = Field(default=None,primary_key=True)
    course_content: Optional["CourseContent"] = Relationship(sa_relationship_kwargs={"uselist": False})
    chapter: Optional["Chapter"] = Relationship(back_populates="subchapters")
    


class SubChapterCreate(SubChapterBase):
    pass 

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







