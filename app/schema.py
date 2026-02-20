from sqlmodel import SQLModel
from typing import List


class SubChapterRead(SQLModel):
    id: int 
    name: str 
    slug:str
    chapter_id:int 

class ChapterRead(SQLModel):
    id:int 
    name:str
    slug:str
    course_id:int
    subchapters:List[SubChapterRead]

class CourseRead(SQLModel):
    id:int
    name:str 
    slug:str
    chapters:List[ChapterRead]

