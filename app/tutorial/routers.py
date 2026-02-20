from typing import List
from fastapi import APIRouter,Depends,HTTPException
from app.tutorial.models import *
from app.tutorial.schema import *
# from app.models import Chapter,ChapterCreate,ChapterUpdate,Course
# from app.schema import ChapterRead
from app.database import get_session
from sqlmodel import Session,select

from app.dependencies import get_token_header
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/tutorial",
    tags=["tutorial"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# routers for course 
@router.post("/courses")
def create_course(course:CourseCreate,session:Session=Depends(get_session))->Course:
    db_course = Course.model_validate(course.model_dump(),context={"session": session})
    session.add(db_course)
    session.commit()
    session.refresh(db_course)
    return db_course

@router.get("/courses")
def get_courses(session:Session=Depends(get_session))->List[CourseRead]:
    statement = select(Course)
    results = session.exec(statement=statement).all()
    return results

@router.get("/courses/{course_id}")
def get_course_detail(course_id:int,session:Session=Depends(get_session))->CourseRead:
    statement = select(Course).where(Course.id == course_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Course not found")
    return result

@router.put("/courses/{course_id}")
def update_course(course_id:int,course_update:CourseUpdate,session:Session=Depends(get_session))->Course:
    course_db = session.get(Course,course_id)
    if not course_db:
        raise HTTPException(status_code=400,detail='course not found')
    update_data = course_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(course_db,key,value)
    
    session.add(course_db)
    session.commit()
    session.refresh(course_db)
    return course_db


# routers for chapters 
@router.post("/chapters")
def create_chapter(chapter:ChapterCreate,session:Session=Depends(get_session))->Chapter:
    db_chapter = Chapter.model_validate(chapter.model_dump(),context={"session": session})
    session.add(db_chapter)
    session.commit()
    session.refresh(db_chapter)
    return db_chapter

@router.get("/chapters")
def get_chapter_list(session:Session=Depends(get_session))->List[ChapterRead]:
    statement = select(Chapter)
    results = session.exec(statement=statement).all()
    return results

@router.get("/chapters/{chapter_id}")
def get_chapter_detail(chapter_id:int,session:Session=Depends(get_session))->ChapterRead:
    statement = select(Chapter).where(Chapter.id == chapter_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/chapters/course/{course_slug}")
def get_chapter_detail_by_courseid(course_slug:str,session:Session=Depends(get_session))->List[ChapterRead]:
    course = session.exec(select(Course).where(Course.slug==course_slug)).first()
    statement = select(Chapter).where(Chapter.course_id == course.id)
    result = session.exec(statement=statement).all()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.put("/chapters/{chapter_id}")
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

# routers for subchapters 
@router.post("/subchapters")
def create_subchapter(subchapter:SubChapterCreate,session:Session=Depends(get_session))->SubChapter:
    db_subchapter = SubChapter.model_validate(subchapter.model_dump(),context={"session": session})
    session.add(db_subchapter)
    session.commit()
    session.refresh(db_subchapter)
    return db_subchapter

@router.get("/subchapters")
def get_subchapter_list(session:Session=Depends(get_session))->List[SubChapter]:
    statement = select(SubChapter)
    results = session.exec(statement=statement).all()
    return results

@router.get("/subchapters/{subchapter_id}")
def get_subchapter_detail(subchapter_id:int,session:Session=Depends(get_session))->SubChapterRead:
    statement = select(SubChapter).where(SubChapter.id == subchapter_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/subchapters/slug/{subchapter_slug}")
def get_subchapter_detail(subchapter_slug:str,session:Session=Depends(get_session))->SubChapterRead:
    statement = select(SubChapter).where(SubChapter.slug == subchapter_slug)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/subchapters/course/{course_id}")
def get_subchapter_detail(course_id:int,session:Session=Depends(get_session))->List[SubChapterRead]:
    statement = select(SubChapter).where(SubChapter.chapter.has(Chapter.course.has(Course.id == course_id)))
    result = session.exec(statement=statement).all()
    if not result:
        raise HTTPException(status_code=404, detail="subchapters not found")
    return result

@router.put("/subchapters/{subchapter_id}")
def update_subchapter(subchapter_id:int,subchapter_update:SubChapterUpdate,session:Session = Depends(get_session))->SubChapterRead:
    subchapter_db = session.get(SubChapter,subchapter_id)
    if not subchapter_db:
        raise HTTPException(status_code=400,detail='subchapter not found')
    update_data = subchapter_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(subchapter_db,key,value)
    
    session.add(subchapter_db)
    session.commit()
    session.refresh(subchapter_db)
    return subchapter_db

# routers for coursecontent 
@router.post("/course-content")
def create_course_content(course_content:CourseContentCreate,session:Session=Depends(get_session))->CourseContent:
    db_course_content = CourseContent.model_validate(course_content)
    print(db_course_content)
    session.add(db_course_content)
    session.commit()
    session.refresh(db_course_content)
    return db_course_content

@router.get("/course-content")
def get_course_contents(session:Session=Depends(get_session))->List[CourseContent]:
    statement = select(CourseContent)
    results = session.exec(statement=statement).all()
    return results

@router.get("/course-content/{course_content_id}")
def get_course_content_detail(course_content_id:int,session:Session=Depends(get_session))->CourseContent:
    statement = select(CourseContent).where(CourseContent.id == course_content_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/course-content/subchapter/{subchapter_slug}")
def get_course_content_by_subchapter(subchapter_slug:str,session:Session=Depends(get_session))->CourseContent:
    subchapter = session.exec(select(SubChapter).where(SubChapter.slug==subchapter_slug)).first()
    statement = select(CourseContent).where(CourseContent.subchapter_id==subchapter.id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Course content not found")
    return result

@router.put("/course-content/subchapter/{subchapter_slug}")
def update_course_content(subchapter_slug:str,course_content_update:CourseContentUpdate,session:Session = Depends(get_session))->CourseContent:
    subchapter = session.exec(select(SubChapter).where(SubChapter.slug==subchapter_slug)).first()
    statement = select(CourseContent).where(CourseContent.subchapter_id==subchapter.id)
    db_content = session.exec(statement=statement).first()
    if not db_content:
        # print(CourseContent.model_validate(course_content_update),'=================')
        db_course_content = CourseContent.model_validate(course_content_update)
        session.add(db_course_content)
        session.commit()
        session.refresh(db_course_content)
        return db_course_content
    else:
        for key,value in course_content_update.model_dump(exclude_unset=True).items():
            setattr(db_content,key,value)
    session.add(db_content)
    session.commit()
    session.refresh(db_content)
    return db_content

@router.put("/course-content/{course_content_id}")
def update_course_content(course_content_id:int,course_content_update:CourseContentUpdate,session:Session = Depends(get_session))->CourseContent:
    content_db = session.get(CourseContent,course_content_id)
    if not content_db:
        raise HTTPException(status_code=400,detail='content not found')
    update_data = course_content_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(content_db,key,value)
    
    session.add(content_db)
    session.commit()
    session.refresh(content_db)
    return content_db



