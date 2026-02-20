from typing import List
from fastapi import APIRouter,Depends,HTTPException
from app.models import SubChapter,SubChapterCreate,SubChapterUpdate
from app.database import get_session
from sqlmodel import Session,select
from app.schema import SubChapterRead

from app.dependencies import get_token_header
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/subchapters",
    tags=["subchapters"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
def create_subchapter(subchapter:SubChapterCreate,session:Session=Depends(get_session))->SubChapter:
    db_subchapter = SubChapter.model_validate(subchapter)
    session.add(db_subchapter)
    session.commit()
    session.refresh(db_subchapter)
    return db_subchapter

@router.get("/")
def get_subchapter_list(session:Session=Depends(get_session))->List[SubChapter]:
    statement = select(SubChapter)
    results = session.exec(statement=statement).all()
    return results

@router.get("/{subchapter_id}")
def get_subchapter_detail(subchapter_id:int,session:Session=Depends(get_session))->SubChapterRead:
    statement = select(SubChapter).where(SubChapter.id == subchapter_id)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.get("/slug/{subchapter_slug}")
def get_subchapter_detail(subchapter_slug:str,session:Session=Depends(get_session))->SubChapterRead:
    statement = select(SubChapter).where(SubChapter.slug == subchapter_slug)
    result = session.exec(statement=statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return result

@router.put("/{subchapter_id}")
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