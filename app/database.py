from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel,Session
from app.config import settings

engine = create_engine(settings.sqlalchemy_string)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

def get_session():
    with Session(engine) as session:
        yield session

Base = declarative_base()
SessionDep = Annotated[Session,Depends(get_session)]





