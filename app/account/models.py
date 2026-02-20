from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel,Field,Relationship
from pydantic import model_validator
from sqlalchemy import Column,Text,DateTime,func,TEXT
from slugify import slugify

class User(SQLModel,table=True):
    id: int | None = Field(default=None,primary_key=True)
    username: str = Field(index=True,unique=True)
    hashed_password:str
    is_active:bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=True
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        )
    )

class RegisterUser(SQLModel):
    username:str = Field()
    password: str = Field()

class LoginUser(SQLModel):
    username:str = Field()
    password: str = Field()

class UserRead(SQLModel):
    id:int 
    username:str 

class Token(SQLModel):
    access_token:str 
    token_type:str 


