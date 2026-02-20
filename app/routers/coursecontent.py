from typing import List
from fastapi import APIRouter,Depends,HTTPException
from app.models import CourseContent,CourseContentCreate,CourseContentUpdate,SubChapter
from app.database import get_session
from sqlmodel import Session,select

from app.dependencies import get_token_header
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/course-content",
    tags=["course-content"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
def create_course_content(course_content:CourseContentCreate,session:Session=Depends(get_session))->CourseContent:
    db_course_content = CourseContent.model_validate(course_content)
    print(db_course_content)
    session.add(db_course_content)
    session.commit()
    session.refresh(db_course_content)
    return db_course_content

@router.get("/")
def get_course_contents(session:Session=Depends(get_session))->List[CourseContent]:
    statement = select(CourseContent)
    results = session.exec(statement=statement).all()
    return results

@router.get("/{course_content_id}")
def get_course_content_detail(course_content_id:int,session:Session=Depends(get_session))->CourseContent:
    statement = select(CourseContent).where(CourseContent.id == course_content_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/subchapter/{subchapter_slug}")
def get_course_content_by_subchapter(subchapter_slug:str,session:Session=Depends(get_session))->CourseContent:
    subchapter = session.exec(select(SubChapter).where(SubChapter.slug==subchapter_slug)).first()
    statement = select(CourseContent).where(CourseContent.subchapter_id==subchapter.id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Course content not found")
    return result

@router.put("/subchapter/{subchapter_slug}")
def update_course_content(subchapter_slug:str,course_content_update:CourseContentUpdate,session:Session = Depends(get_session))->CourseContent:
    subchapter = session.exec(select(SubChapter).where(SubChapter.slug==subchapter_slug)).first()
    statement = select(CourseContent).where(CourseContent.subchapter_id==subchapter.id)
    db_content = session.exec(statement=statement).first()
    if not db_content:
        print(CourseContent.model_validate(course_content_update),'=================')
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

@router.put("/{course_content_id}")
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

