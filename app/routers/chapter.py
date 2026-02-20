from typing import List
from fastapi import APIRouter,Depends,HTTPException
from app.models import Chapter,ChapterCreate,ChapterUpdate,Course
from app.schema import ChapterRead
from app.database import get_session
from sqlmodel import Session,select

from app.dependencies import get_token_header
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/chapters",
    tags=["chapters"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
def create_chapter(chapter:ChapterCreate,session:Session=Depends(get_session))->Chapter:
    db_chapter = Chapter.model_validate(chapter)
    session.add(db_chapter)
    session.commit()
    session.refresh(db_chapter)
    return db_chapter

@router.get("/")
def get_chapter_list(session:Session=Depends(get_session))->List[ChapterRead]:
    statement = select(Chapter)
    results = session.exec(statement=statement).all()
    return results

@router.get("/{chapter_id}")
def get_chapter_detail(chapter_id:int,session:Session=Depends(get_session))->ChapterRead:
    statement = select(Chapter).where(Chapter.id == chapter_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/course/{course_slug}")
def get_chapter_detail_by_courseid(course_slug:str,session:Session=Depends(get_session))->List[ChapterRead]:
    course = session.exec(select(Course).where(Course.slug==course_slug)).first()
    statement = select(Chapter).where(Chapter.course_id == course.id)
    result = session.exec(statement=statement).all()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.put("/{chapter_id}")
def chapter_update(chapter_id:int,chapter_update:ChapterUpdate,session:Session = Depends(get_session))->Chapter:
    chapter_db = session.get(Chapter,chapter_id)
    if not chapter_db:
        raise HTTPException(status_code=400,detail='chapter not found')
    update_data = chapter_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(chapter_db,key,value)
    
    session.add(chapter_db)
    session.commit()
    session.refresh(chapter_db)
    return chapter_db

