import string
import random
from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship
from pydantic import model_validator, ValidationInfo
from sqlalchemy import Column, Text, DateTime, func, select
from slugify import slugify

from app.database import Session



def generate_random_string(length: int = 4) -> str:
    letters = string.ascii_letters
    return ''.join(random.choices(letters, k=length))


def generate_unique_slug(name: str, session: Session, model) -> str:
    base_slug = slugify(name)
    slug = base_slug

    while True:
        statement = select(model).where(model.slug == slug)
        existing = session.exec(statement).first()

        if not existing:
            return slug

        slug = f"{base_slug}-{generate_random_string(4)}"




class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: Optional[str] = Field(default=None, index=True, sa_column_kwargs={"unique": True})
    is_active: bool = Field(default=True)

    created_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()}
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now()
        }
    )

    @model_validator(mode="before")
    @classmethod
    def generate_slug_from_name(cls, data: dict, info: ValidationInfo):
        if not isinstance(data, dict):
            return data

        name = data.get("name")
        slug = data.get("slug")

        if name and not slug:
            context = info.context or {}
            session = context.get("session")
            model_class = context.get("model_class")

            if session and model_class:
                data["slug"] = generate_unique_slug(name, session, model_class)
            else:
                data["slug"] = f"{slugify(name)}-{generate_random_string(4)}"

        return data


# models for category 
class Category(BaseModel, table=True):
    name: str = Field(index=True)

    datasets: List["Dataset"] = Relationship(back_populates="category")
    reports: List["Report"] = Relationship(back_populates="category")


class CategoryCreate(SQLModel):
    name: str


class CategoryRead(SQLModel):
    id: int
    name: str
    slug: str


# models for tag 
class Tag(BaseModel, table=True):
    name: str = Field(index=True)

    dataset_links: List["DatasetTag"] = Relationship(back_populates="tag")
    report_links: List["ReportTag"] = Relationship(back_populates="tag")


class TagCreate(SQLModel):
    name: str


class TagRead(SQLModel):
    id: int
    name: str
    slug: str


# models for dataset 

class Dataset(BaseModel, table=True):
    name: str = Field(index=True)
    description: str = Field(sa_column=Column(Text))
    file_path: Optional[str] = None

    # One-to-Many Category
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="datasets")

    # Many-to-Many Tags
    tag_links: List["DatasetTag"] = Relationship(back_populates="dataset")


class DatasetCreate(SQLModel):
    name: str
    description: str
    category_id: Optional[int]


class DatasetRead(SQLModel):
    id: int
    name: str
    description: str
    slug: str
    file_path: Optional[str]
    is_active: bool



# models for dataset tag 
class DatasetTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    dataset_id: int = Field(foreign_key="dataset.id")
    tag_id: int = Field(foreign_key="tag.id")

    dataset: Optional[Dataset] = Relationship(back_populates="tag_links")
    tag: Optional[Tag] = Relationship(back_populates="dataset_links")

# models for report 

class Report(BaseModel, table=True):
    name: str = Field(index=True)
    description: str = Field(sa_column=Column(Text))
    content: str = Field(sa_column=Column(Text))

    # One-to-Many Category
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="reports")

    # Many-to-Many Tags
    tag_links: List["ReportTag"] = Relationship(back_populates="report")


class ReportCreate(SQLModel):
    name: str
    description: str
    content: str
    category_id: Optional[int]


class ReportRead(SQLModel):
    id: int
    name: str
    description: str
    content: str
    slug: str
    is_active: bool


# models for report tag

class ReportTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    report_id: int = Field(foreign_key="report.id")
    tag_id: int = Field(foreign_key="tag.id")

    report: Optional[Report] = Relationship(back_populates="tag_links")
    tag: Optional[Tag] = Relationship(back_populates="report_links")

# nested tags for READ

class TagNestedRead(SQLModel):
    id: int
    name: str
    slug: str


class DatasetTagNestedRead(SQLModel):
    id: int
    tag: TagNestedRead


class ReportTagNestedRead(SQLModel):
    id: int
    tag: TagNestedRead


class CategoryNestedRead(SQLModel):
    id: int
    name: str
    slug: str


class DatasetNestedRead(SQLModel):
    id: int
    name: str
    description: str
    slug: str
    file_path: Optional[str]

    category: Optional[CategoryNestedRead]
    tag_links: List[DatasetTagNestedRead]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ReportNestedRead(SQLModel):
    id: int
    name: str
    description: str
    content: str
    slug: str

    category: Optional[CategoryNestedRead]
    tag_links: List[ReportTagNestedRead]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]