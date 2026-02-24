from typing import List
from fastapi import APIRouter,Depends,HTTPException
from app.neclicense.models import *
from app.database import get_session
from sqlmodel import Session,select

from app.dependencies import get_token_header

router = APIRouter(
    prefix="/nec",
    tags=["nec"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post("/program")
def create_program(program:ProgramCreate,session:Session=Depends(get_session))->ProgramRead:
    db_program = Program.model_validate(program.model_dump(),context={"session": session})
    session.add(db_program)
    session.commit()
    session.refresh(db_program)
    return db_program

@router.get('/program')
def read_program(session:Session=Depends(get_session))->List[ProgramRead]:
    statement = select(Program).where(Program.is_active==True)
    results = session.exec(statement=statement).all()
    return results

@router.get('/program/detail/{program_id}')
def read_program(program_id:int, session:Session=Depends(get_session))->ProgramRead:
    statement = select(Program).where(Program.id==program_id)
    result = session.exec(statement=statement).first()
    return result

@router.get('/program/{program_slug}')
def read_program_by_slug(program_slug:str,session:Session=Depends(get_session))->ProgramRead:
    statement = select(Program).where(Program.slug==program_slug)
    results = session.exec(statement=statement).first()
    return results

@router.put("/program/{program_id}")
def update_program(program_id:int,program_update:ProgramUpdate,session:Session=Depends(get_session))->ProgramRead:
    program_db = session.get(Program,program_id)
    if not program_db:
        raise HTTPException(status_code=400,detail='program not found')
    update_data = program_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(program_db,key,value)
    
    session.add(program_db)
    session.commit()
    session.refresh(program_db)
    return program_db

# router for chapters

@router.post("/chapter")
def create_chapter(chapter:NecSyllabusChapterCreate,session:Session=Depends(get_session))->NecSyllabusChapterRead:
    db = NecSyllabusChapter.model_validate(chapter.model_dump(),context={"session": session})
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

@router.get('/chapter')
def read_chapter(session:Session=Depends(get_session))->List[NecSyllabusChapterRead]:
    statement = select(NecSyllabusChapter).where(NecSyllabusChapter.is_active==True)
    results = session.exec(statement=statement).all()
    return results


@router.get('/chapter/{chapter_slug}')
def read_chapter_by_slug(chapter_slug:str,session:Session=Depends(get_session))->NecSyllabusChapterRead:
    statement = select(NecSyllabusChapter).where(NecSyllabusChapter.slug == chapter_slug)
    results = session.exec(statement=statement).first()
    return results

@router.get('/chapter/by/program/{program_id}')
def filter_chapter_by_program(program_id:int,session:Session=Depends(get_session))->List[NecSyllabusChapterRead]:
    statement = select(NecSyllabusChapter).where(NecSyllabusChapter.program_id == program_id)
    results = session.exec(statement=statement).all()
    return results

@router.put("/chapter/{chapter_id}")
def update_chapter(chapter_id:int,chapter_update:NecSyllabusChapterUpdate,session:Session=Depends(get_session))->NecSyllabusChapterRead:
    db = session.get(NecSyllabusChapter,chapter_id)
    if not db:
        raise HTTPException(status_code=400,detail='chapter not found')
    update_data = chapter_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(db,key,value)
    
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

# routers for subchapter
@router.post("/subchapter")
def create_subchapter(subchapter:NecSyllabusSubchapterCreate,session:Session=Depends(get_session))->NecSyllabusSubchapterRead:
    db = NecSyllabusSubchapter.model_validate(subchapter.model_dump(),context={"session": session})
    session.add(db)
    session.commit()
    session.refresh(db)
    return db


@router.get('/subchapter')
def read_subchapter(session:Session=Depends(get_session))->List[NecSyllabusSubchapter]:
    statement = select(NecSyllabusSubchapter).where(NecSyllabusSubchapter.is_active==True)
    results = session.exec(statement=statement).all()
    return results

@router.get('/subchapter/{subchapter_slug}')
def read_subchapter(subchapter_slug:str,session:Session=Depends(get_session))->NecSyllabusSubchapterRead:
    statement = select(NecSyllabusSubchapter).where(NecSyllabusSubchapter.slug==subchapter_slug)
    result = session.exec(statement=statement).first()
    return result

@router.put("/subchapter/{subchapter_id}")
def update_subchapter(subchapter_id:int,subchapter_update:NecSyllabusSubchapterUpdate,session:Session=Depends(get_session))->NecSyllabusSubchapterRead:
    db = session.get(NecSyllabusChapter,subchapter_id)
    if not db:
        raise HTTPException(status_code=400,detail='chapter not found')
    update_data = subchapter_update.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(db,key,value)
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

# routers for mcq

@router.post('/question')
def create_multiplechoice_question(question_create:NecMultipleChoiceQuestionCreate,session:Session=Depends(get_session))->NecMultipleChoiceQuestionRead:
    db = NecMultipleChoiceQuestion.model_validate(question_create.model_dump())
    session.add(db)
    session.commit()
    session.refresh(db)
    return db  

@router.get('/question')
def get_multiplechoice_question(session:Session=Depends(get_session))->List[NecMultipleChoiceQuestionRead]:
    result = session.exec(select(NecMultipleChoiceQuestion)).all()
    return result

@router.post('/mcq')
def create_mcq(nec_mcq_create:NecMcqCreate,session:Session=Depends(get_session))->NecMultipleChoiceAnswerRead:
    db = NecMultipleChoiceAnswer.model_validate(nec_mcq_create.model_dump())
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

@router.get('/mcq')
def read_mcq(session:Session=Depends(get_session))->List[NecMultipleChoiceAnswerRead]:
    result = session.exec(select(NecMultipleChoiceAnswer)).all()
    return result

















