from typing import List
from fastapi import APIRouter,Depends,HTTPException
from app.models import CourseCreate,Course,CourseUpdate
from app.database import get_session
from sqlmodel import Session,select

from app.schema import CourseRead

from app.dependencies import get_token_header
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
def create_course(course:CourseCreate,session:Session=Depends(get_session))->Course:
    db_course = Course.model_validate(course)
    session.add(db_course)
    session.commit()
    session.refresh(db_course)
    return db_course

@router.get("/")
def get_courses(session:Session=Depends(get_session))->List[CourseRead]:
    statement = select(Course)
    results = session.exec(statement=statement).all()
    return results

@router.get("/{course_id}")
def get_course_detail(course_id:int,session:Session=Depends(get_session))->CourseRead:
    statement = select(Course).where(Course.id == course_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Course not found")
    return result

@router.put("/{course_id}")
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


