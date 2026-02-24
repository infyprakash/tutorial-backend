from datetime import datetime
from sqlmodel import SQLModel
from typing import List,Optional
from app.tutorial.models import *


class SubChapterRead(SQLModel):
    id: int 
    name: str 
    slug:str
    chapter_id:int 
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ChapterRead(SQLModel):
    id:int 
    name:str
    slug:str
    course_id:int
    subchapters:List[SubChapterRead]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class CourseRead(SQLModel):
    id:int
    name:str 
    description : str
    slug:str
    chapters:List[ChapterRead]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# for sitemap 
class CourseNested(SQLModel):
    id: int
    name: str
    slug: str


# -------------------
# Minimal Chapter
# -------------------
class ChapterNested(SQLModel):
    id: int
    name: str
    slug: str
    course: CourseNested


# -------------------
# SubChapter Detail
# -------------------
class SubChapterNested(SQLModel):
    id: int
    name: str
    slug: str
    chapter: ChapterNested
    created_at: Optional[datetime]
    updated_at: Optional[datetime]







