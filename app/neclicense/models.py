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

# nec license tables here 


# nec program 

class Program(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True)
    name:str  = Field(index=True)
    description : str = Field(sa_column=Column(Text),default=None)
    chapters:list["NecSyllabusChapter"] = Relationship(back_populates="program")
    
    slug: Optional[str] = Field(index=True,sa_column_kwargs={"unique": True})
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=True))
    updated_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True))
    
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
                from app.neclicense.models import Program
                data["slug"] = generate_unique_slug(name, session, Program)
            else:
                base_slug = slugify(name)
                data["slug"] = f"{base_slug}-{generate_random_string(4)}"
        return data



class ProgramCreate(SQLModel):
    name:str 

class ProgramUpdate(SQLModel):
    name:str 
    description:str

# nec syllabus chapter

class NecSyllabusChapter(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True)
    name:str = Field(index=True)
    program_id: int | None = Field(default=None,foreign_key='program.id')
    
    program:Optional["Program"] = Relationship(back_populates="chapters")
    subchapters:list["NecSyllabusSubchapter"] = Relationship(back_populates="chapter")
    
    slug: Optional[str] = Field(index=True,sa_column_kwargs={"unique": True})
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=True))
    updated_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True))
    
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
                from app.neclicense.models import NecSyllabusChapter
                data["slug"] = generate_unique_slug(name, session, NecSyllabusChapter)
            else:
                base_slug = slugify(name)
                data["slug"] = f"{base_slug}-{generate_random_string(4)}"
        return data

class NecSyllabusChapterRead(SQLModel):
    id:int 
    name:str
    program_id:int
    subchapters:list
    slug:str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ProgramRead(SQLModel):
    id:int 
    name:str
    description : str
    slug:str
    chapters:list[NecSyllabusChapterRead]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class NecSyllabusChapterCreate(SQLModel):
    name:str
    program_id:int 

class NecSyllabusChapterUpdate(SQLModel):
    name:str
    program_id:int

# nec syllabus topic 

class NecSyllabusSubchapter(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True)
    name:str = Field(index=True)
    chapter_id: int | None = Field(default=None,foreign_key='necsyllabuschapter.id')
    chapter:Optional["NecSyllabusChapter"] = Relationship(back_populates="subchapters")
    questions:list["NecMultipleChoiceQuestion"] = Relationship(back_populates="subchapter")

    slug: Optional[str] = Field(index=True,sa_column_kwargs={"unique": True})
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=True))
    updated_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True))
    
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
                from app.neclicense.models import NecSyllabusSubchapter
                data["slug"] = generate_unique_slug(name, session, NecSyllabusSubchapter)
            else:
                base_slug = slugify(name)
                data["slug"] = f"{base_slug}-{generate_random_string(4)}"
        return data



class NecSyllabusSubchapterCreate(SQLModel):
    name:str
    chapter_id:int


class NecSyllabusSubchapterUpdate(SQLModel):
    name:str
    chapter_id:int


# NEC multiple choice questions 

class NecMultipleChoiceQuestion(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True)
    question:str = Field(index=True)
    subchapter_id: int | None = Field(default=None,foreign_key='necsyllabussubchapter.id')
    
    subchapter:Optional["NecSyllabusSubchapter"] = Relationship(back_populates="questions")
    
    answers:list["NecMultipleChoiceAnswer"] = Relationship(back_populates="question")
    created_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=True))
    updated_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True))

class NecMultipleChoiceQuestionRead(SQLModel):
    id:int 
    question:str
    answers:list
    subchapter_id:int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class NecMultipleChoiceQuestionCreate(SQLModel):
    question:str
    subchapter_id:int 

class NecMultipleChoiceQuestionUpdate(SQLModel):
    question:str
    subchapter_id:int

class NecSyllabusSubchapterRead(SQLModel):
    id:int 
    name:str
    chapter_id:int
    questions:list[NecMultipleChoiceQuestionRead]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

# NEC multiple choice answer

class NecMultipleChoiceAnswer(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True)
    answer:str = Field(index=True)
    question_id: int | None = Field(default=None,foreign_key='necmultiplechoicequestion.id')
    question: Optional["NecMultipleChoiceQuestion"] = Relationship(back_populates="answers")
    
    is_correct:bool = Field(default=False)
    created_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=True))
    updated_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True))

class NecMultipleChoiceAnswerRead(SQLModel):
    id:int 
    answer:str
    question_id:int
    is_correct: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class NecMultipleChoiceAnswerCreate(SQLModel):
    answer:str
    question_id:int 

class NecMultipleChoiceAnswerUpdate(SQLModel):
    answer:str
    question_id:int

class NecMcqCreate(SQLModel):
    question_id:int
    answer:str 
    is_correct:bool























