import os
import json
import shutil
from pathlib import Path
from uuid import uuid4

from typing import List
from fastapi import APIRouter,Depends,HTTPException,Form,UploadFile,File,Query
from app.infography.models import *

from app.database import get_session
from sqlmodel import Session,select,desc
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.dependencies import get_token_header

router = APIRouter(
    prefix="/infography",
    tags=["infography"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


UPLOAD_DIR = Path("uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}


def validate_file(file: UploadFile):
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: csv, xlsx, xls, json"
        )
    
def get_dataset_with_relations(dataset_id: int, session: Session):
    statement = (
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .options(
            selectinload(Dataset.category),
            selectinload(Dataset.tag_links).selectinload(DatasetTag.tag),
        )
    )

    return session.exec(statement).first()


def save_file(file: UploadFile) -> str:
    validate_file(file)

    unique_filename = f"{uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return str(file_path)


# category routes 

@router.post("/categories", response_model=CategoryRead)
def create_category(
    payload: CategoryCreate,
    session: Session = Depends(get_session),
):
    category = Category.model_validate(
        payload.model_dump(),
        context={"session": session, "model_class": Category},
    )

    session.add(category)

    try:
        session.commit()
        session.refresh(category)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Category already exists.")

    return category



@router.put("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryCreate,
    session: Session = Depends(get_session),
):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    category.name = payload.name

    session.add(category)
    session.commit()
    session.refresh(category)

    return category



@router.get("/categories", response_model=List[CategoryRead])
def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    statement = (
        select(Category)
        .order_by(desc(Category.created_at))
        .offset(offset)
        .limit(page_size)
    )

    categories = session.exec(statement).all()
    return categories


@router.get("/categories/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: int,
    session: Session = Depends(get_session),
):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    return category


# routers for tags 

@router.post("/tags", response_model=TagRead)
def create_tag(
    payload: TagCreate,
    session: Session = Depends(get_session),
):
    tag = Tag.model_validate(
        payload.model_dump(),
        context={"session": session, "model_class": Tag},
    )

    session.add(tag)

    try:
        session.commit()
        session.refresh(tag)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Tag already exists.")

    return tag



@router.put("/tags/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int,
    payload: TagCreate,
    session: Session = Depends(get_session),
):
    tag = session.get(Tag, tag_id)

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found.")

    tag.name = payload.name

    session.add(tag)
    session.commit()
    session.refresh(tag)

    return tag


@router.get("/tags", response_model=List[TagRead])
def list_tags(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    statement = (
        select(Tag)
        .order_by(desc(Tag.created_at))
        .offset(offset)
        .limit(page_size)
    )

    tags = session.exec(statement).all()
    return tags


@router.get("/tags/{tag_id}", response_model=TagRead)
def get_tag(
    tag_id: int,
    session: Session = Depends(get_session),
):
    tag = session.get(Tag, tag_id)

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found.")

    return tag

# routers for datsset 

@router.get("/datasets", response_model=List[DatasetNestedRead])
def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    statement = (
        select(Dataset)
        .where(Dataset.is_active == True)
        .options(
            selectinload(Dataset.category),
            selectinload(Dataset.tag_links).selectinload(DatasetTag.tag),
        )
        .order_by(desc(Dataset.created_at))
        .offset(offset)
        .limit(page_size)
    )

    datasets = session.exec(statement).all()
    return datasets

@router.get("/datasets/latest", response_model=List[DatasetNestedRead])
def latest_datasets(session: Session = Depends(get_session)):
    statement = (
        select(Dataset)
        .where(Dataset.is_active == True)
        .options(
            selectinload(Dataset.category),
            selectinload(Dataset.tag_links).selectinload(DatasetTag.tag),
        )
        .order_by(desc(Dataset.created_at))
        .limit(5)
    )

    datasets = session.exec(statement).all()
    return datasets

@router.get("/datasets/all", response_model=List[DatasetNestedRead])
def all_datasets(session: Session = Depends(get_session)):
    statement = (
        select(Dataset)
        .where(Dataset.is_active == True)
        .options(
            selectinload(Dataset.category),
            selectinload(Dataset.tag_links).selectinload(DatasetTag.tag),
        )
        .order_by(desc(Dataset.created_at))
    )

    datasets = session.exec(statement).all()
    return datasets

@router.post("/datasets", response_model=DatasetNestedRead)
def create_dataset(
    name: str = Form(...),
    description: str = Form(...),
    category_id: Optional[int] = Form(None),
    tag_ids: Optional[str] = Form(None),  
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):

    if category_id:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

    # Save file
    file_path = save_file(file)

    # Create dataset with slug generation
    dataset = Dataset(
        name=name,
        description=description,
        file_path=file_path,
        category_id=category_id,
    )

    dataset = Dataset.model_validate(
        dataset.model_dump(),
        context={"session": session, "model_class": Dataset},
    )

    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    # Attach tags
    if tag_ids:
        tag_id_list = [int(t.strip()) for t in tag_ids.split(",")]

        for tag_id in tag_id_list:
            tag = session.get(Tag, tag_id)
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")

            link = DatasetTag(dataset_id=dataset.id, tag_id=tag_id)
            session.add(link)

        session.commit()

    return get_dataset_with_relations(dataset.id, session)


@router.put("/datasets/{dataset_id}", response_model=DatasetNestedRead)
def update_dataset(
    dataset_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tag_ids: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
):

    dataset = session.get(Dataset, dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    # Update fields
    if name:
        dataset.name = name

    if description:
        dataset.description = description

    if category_id is not None:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        dataset.category_id = category_id

    # Replace file if provided
    if file:
        # Delete old file safely
        if dataset.file_path and Path(dataset.file_path).exists():
            Path(dataset.file_path).unlink()

        dataset.file_path = save_file(file)

    session.add(dataset)
    session.commit()

    # Replace tags if provided
    if tag_ids is not None:
        # Remove old links
        existing_links = session.exec(
            select(DatasetTag).where(DatasetTag.dataset_id == dataset_id)
        ).all()

        for link in existing_links:
            session.delete(link)

        session.commit()

        # Add new links
        tag_id_list = [int(t.strip()) for t in tag_ids.split(",")]

        for tag_id in tag_id_list:
            tag = session.get(Tag, tag_id)
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")

            new_link = DatasetTag(dataset_id=dataset_id, tag_id=tag_id)
            session.add(new_link)

        session.commit()

    return get_dataset_with_relations(dataset_id, session)



@router.get("/datasets/{dataset_id}", response_model=DatasetNestedRead)
def get_dataset(dataset_id: int, session: Session = Depends(get_session)):
    dataset = get_dataset_with_relations(dataset_id, session)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset

@router.get("/datasets/detail/{dataset_slug}", response_model=DatasetNestedRead)
def get_dataset_detail(dataset_slug: str, session: Session = Depends(get_session)):
    dataset = session.exec(select(Dataset).where(Dataset.slug==dataset_slug)).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset

@router.get("/datasets/filter/category/{category_slug}", response_model=List[DatasetNestedRead])
def filter_datasets_by_category(
    category_slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    # Validate category
    category = session.exec(select(Category).where(Category.slug==category_slug)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    statement = (
        select(Dataset)
        .where(Dataset.category_id == category.id, Dataset.is_active == True)
        .options(
            selectinload(Dataset.category),
            selectinload(Dataset.tag_links).selectinload(DatasetTag.tag),
        )
        .order_by(desc(Dataset.created_at))
        .offset(offset)
        .limit(page_size)
    )

    return session.exec(statement).all()


@router.get("/datasets/filter/tags", response_model=List[DatasetNestedRead])
def filter_datasets_by_tags(
    tag_ids: str = Query(..., description="Comma separated tag ids: 1,2,3"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    # Convert string to list[int]
    tag_id_list = [int(t.strip()) for t in tag_ids.split(",")]

    # Validate tags
    existing_tags = session.exec(
        select(DatasetTag.tag_id).where(DatasetTag.tag_id.in_(tag_id_list))
    ).all()
    if not existing_tags:
        raise HTTPException(status_code=404, detail="No valid tags found")

    statement = (
        select(Dataset)
        .join(DatasetTag)
        .where(DatasetTag.tag_id.in_(tag_id_list), Dataset.is_active == True)
        .options(
            selectinload(Dataset.category),
            selectinload(Dataset.tag_links).selectinload(DatasetTag.tag),
        )
        .order_by(desc(Dataset.created_at))
        .distinct()
        .offset(offset)
        .limit(page_size)
    )

    return session.exec(statement).all()

from fastapi.responses import FileResponse

@router.get("/download/{filename}")
async def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(path=file_path, filename=filename)
    return {"error": "File not found"}




# Report routers 



@router.post("/reports", response_model=ReportNestedRead)
def create_report(
    name: str = Form(...),
    description: str = Form(...),
    content: str = Form(...),
    category_id: Optional[int] = Form(None),
    tag_ids: Optional[str] = Form(None),  # comma-separated: "1,2,3"
    session: Session = Depends(get_session),
):
    # Validate category
    if category_id:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

    # Ensure content is stored as a JSON string
    if isinstance(content, (dict, list)):
        content_str = json.dumps(content)
    else:
        content_str = content

    # Create report
    report = Report(
        name=name,
        description=description,
        content=content_str,
        category_id=category_id,
    )

    report = Report.model_validate(
        report.model_dump(),
        context={"session": session, "model_class": Report},
    )

    session.add(report)
    session.commit()
    session.refresh(report)

    # Attach tags if any
    if tag_ids:
        tag_list = [int(t.strip()) for t in tag_ids.split(",")]
        for tag_id in tag_list:
            tag = session.get(Tag, tag_id)
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")
            report_tag = ReportTag(report_id=report.id, tag_id=tag_id)
            session.add(report_tag)
        session.commit()

    return get_report_with_relations(report.id, session)

@router.get("/reports/latest", response_model=List[ReportNestedRead])
def latest_reports(session: Session = Depends(get_session)):
    statement = (
        select(Report)
        .where(Report.is_active == True)
        .options(
            selectinload(Report.category),
            selectinload(Report.tag_links).selectinload(ReportTag.tag),
        )
        .order_by(desc(Report.created_at))
        .limit(5)
    )

    reports = session.exec(statement).all()
    return reports

@router.get("/reports/all", response_model=List[ReportNestedRead])
def all_reports(session: Session = Depends(get_session)):
    statement = (
        select(Report)
        .where(Report.is_active == True)
        .options(
            selectinload(Report.category),
            selectinload(Report.tag_links).selectinload(ReportTag.tag),
        )
        .order_by(desc(Report.created_at))
    )

    reports = session.exec(statement).all()
    return reports


@router.put("/reports/{report_id}", response_model=ReportNestedRead)
def update_report(
    report_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tag_ids: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    report = session.get(Report, report_id)
    if not report or not report.is_active:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Update fields
    if name:
        report.name = name
    if description:
        report.description = description
    if content:
        # Convert object content to JSON string
        if isinstance(content, (dict, list)):
            report.content = json.dumps(content)
        else:
            report.content = content
    if category_id is not None:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        report.category_id = category_id

    session.add(report)
    session.commit()

    # Replace tags if provided
    if tag_ids is not None:
        # Delete old tags
        existing_tags = session.exec(select(ReportTag).where(ReportTag.report_id == report_id)).all()
        for t in existing_tags:
            session.delete(t)
        session.commit()

        # Add new tags
        new_tag_ids = [int(t.strip()) for t in tag_ids.split(",")]
        for tag_id in new_tag_ids:
            tag = session.get(Tag, tag_id)
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")
            report_tag = ReportTag(report_id=report_id, tag_id=tag_id)
            session.add(report_tag)
        session.commit()

    return get_report_with_relations(report_id, session)



@router.get("/reports/{report_id}", response_model=ReportNestedRead)
def get_report(report_id: int, session: Session = Depends(get_session)):
    report = get_report_with_relations(report_id, session)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/reports/detail/{report_slug}", response_model=ReportNestedRead)
def get_report_detail(report_slug: str, session: Session = Depends(get_session)):
    report = session.exec(select(Report).where(Report.slug==report_slug)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report



@router.get("/reports", response_model=List[ReportNestedRead])
def list_reports(
    page: int = 1,
    page_size: int = 10,
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size
    statement = (
        select(Report)
        .where(Report.is_active == True)
        .options(
            selectinload(Report.category),
            selectinload(Report.tag_links).selectinload(ReportTag.tag),
        )
        .order_by(desc(Report.created_at))
        .offset(offset)
        .limit(page_size)
    )
    return session.exec(statement).all()



def get_report_with_relations(report_id: int, session: Session):
    statement = (
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.category),
            selectinload(Report.tag_links).selectinload(ReportTag.tag),
        )
    )
    return session.exec(statement).first()


@router.get("/reports/filter/category/{category_slug}", response_model=List[ReportNestedRead])
def filter_reports_by_category(
    category_slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    # Validate category
    category = session.exec(select(Category).where(Category.slug==category_slug)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    statement = (
        select(Report)
        .where(
            Report.category_id == category.id,
            Report.is_active == True,
        )
        .options(
            selectinload(Report.category),
            selectinload(Report.tag_links).selectinload(ReportTag.tag),
        )
        .order_by(desc(Report.created_at))
        .offset(offset)
        .limit(page_size)
    )

    return session.exec(statement).all()

@router.get("/reports/filter/tags", response_model=List[ReportNestedRead])
def filter_reports_by_tags(
    tag_ids: str = Query(..., description="Comma separated tag ids: 1,2,3"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    # Convert string to list[int]
    tag_id_list = [int(t.strip()) for t in tag_ids.split(",")]

    # Validate tags
    existing_tags = session.exec(
        select(Tag.id).where(Tag.id.in_(tag_id_list))
    ).all()

    if not existing_tags:
        raise HTTPException(status_code=404, detail="No valid tags found")

    statement = (
        select(Report)
        .join(ReportTag)
        .where(
            ReportTag.tag_id.in_(tag_id_list),
            Report.is_active == True,
        )
        .options(
            selectinload(Report.category),
            selectinload(Report.tag_links).selectinload(ReportTag.tag),
        )
        .order_by(desc(Report.created_at))
        .distinct()
        .offset(offset)
        .limit(page_size)
    )

    return session.exec(statement).all()







# @router.get("/tagtype")
# def get_tagtype(session:Session=Depends(get_session))->List[TagTypeRead]:
#     results = session.exec(select(TagType)).all()
#     return results

# @router.post("/tagtype")
# def create_tagtype(tagtype_create:TagTypeCreate,session:Session=Depends(get_session))->TagTypeRead:
#     db = TagType.model_validate(tagtype_create.model_dump(),context={'session':session,'model_class':TagType})
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# @router.get("/tagtype/{tagtype_id}")
# def get_tagtype_detail(tagtype_id:int,session:Session=Depends(get_session))->TagTypeRead:
#     result = session.exec(select(TagType).where(TagType.id == tagtype_id)).first()
#     return result

# @router.put("/tagtype/{tagtype_id}")
# def update_tagtype(tagtype_id:int,tagtype_update:TagTypeUpdate,session:Session=Depends(get_session))->TagTypeRead:
#     db = session.get(TagType,tagtype_id)
#     if not db:
#         raise HTTPException(status_code=400,detail='tag type not found')
#     update_data = tagtype_update.model_dump(exclude_unset=True)
#     for key,value in update_data.items():
#         setattr(db,key,value)
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# # routers for tag 

# @router.get("/tag")
# def get_tag(session:Session=Depends(get_session))->List[TagRead]:
#     results = session.exec(select(Tag)).all()
#     return results

# @router.post("/tag")
# def create_tag(tag_create:TagCreate,session:Session=Depends(get_session))->TagRead:
#     db = Tag.model_validate(tag_create.model_dump(),context={'session':session,'model_class':Tag})
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# @router.get("/tag/{tag_id}")
# def get_tag_detail(tag_id:int,session:Session=Depends(get_session))->TagRead:
#     result = session.exec(select(Tag).where(Tag.id == tag_id)).first()
#     return result

# @router.put("/tag/{tag_id}")
# def update_tag(tag_id:int,tag_update:TagUpdate,session:Session=Depends(get_session))->TagRead:
#     db = session.get(Tag,tag_id)
#     if not db:
#         raise HTTPException(status_code=400,detail='tag not found')
#     update_data = tag_update.model_dump(exclude_unset=True)
#     for key,value in update_data.items():
#         setattr(db,key,value)
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# # router for dataset
 
# UPLOAD_DIR = Path("uploads")
# UPLOAD_DIR.mkdir(exist_ok=True)

# @router.get("/dataset")
# def get_dataset(session:Session=Depends(get_session))->List[DatasetNestedRead]:
#     results = session.exec(select(Dataset).where(Dataset.is_active==True)).all()
#     return results

# # @router.post("/dataset")
# # def create_dataset(name:str=Form(...),description:str=Form(...),file:UploadFile=File(...),session:Session=Depends(get_session))->DatasetRead:
# #     file_path = UPLOAD_DIR / file.filename
# #     with file_path.open("wb") as buffer:
# #         shutil.copyfileobj(file.file,buffer)
# #     unique_slug = generate_unique_slug(name, session, Dataset)
# #     db = Dataset(name=name,description=description,slug=unique_slug,file_path=str(file_path))
# #     session.add(db)
# #     session.commit()
# #     session.refresh(db)
# #     return db


# @router.post("/dataset", response_model=DatasetRead)
# def create_dataset(
#     name: str = Form(...),
#     description: str = Form(...),
#     tag_ids: List[str] = Form(...),  
#     file: UploadFile = File(...),
#     session: Session = Depends(get_session)
# ):
    
#     file_path = UPLOAD_DIR / file.filename
#     with file_path.open("wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)


#     unique_slug = generate_unique_slug(name, session, Dataset)
    
#     db_dataset = Dataset(
#         name=name,
#         description=description,
#         slug=unique_slug,
#         file_path=str(file_path)
#     )
#     session.add(db_dataset)
#     session.flush() # Flush to get the db_dataset.id without committing yet
    
#     tag_ids = tag_ids[0].split(",")

#     for t_id in tag_ids:
#         print(t_id)
#         new_link = DatasetTag(dataset_id=db_dataset.id, tag_id= int(t_id))
#         session.add(new_link)

#     session.commit()
#     session.refresh(db_dataset)
    
#     return db_dataset

# from fastapi import APIRouter, Form, File, UploadFile, Depends, HTTPException
# from sqlalchemy import delete

# @router.patch("/dataset/{dataset_id}", response_model=DatasetRead)
# def update_dataset(
#     dataset_id: int,
#     name: str = Form(None),
#     description: str = Form(None),
#     tag_ids: List[str] = Form(None),  
#     file: UploadFile = File(None),
#     session: Session = Depends(get_session)
# ):
#     # 1. Fetch existing dataset
#     db_dataset = session.get(Dataset, dataset_id)
#     if not db_dataset:
#         raise HTTPException(status_code=404, detail="Dataset not found")

#     # 2. Update basic fields
#     if name:
#         # Update slug if name changes
#         if name != db_dataset.name:
#             db_dataset.slug = generate_unique_slug(name, session, Dataset)
#         db_dataset.name = name
#     if description:
#         db_dataset.description = description

#     # 3. Handle File Update (Only if a new file is uploaded)
#     if file:
#         file_path = UPLOAD_DIR / file.filename
#         with file_path.open("wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#         db_dataset.file_path = str(file_path)

#     # 4. Update Tags (Syncing logic)
#     if tag_ids:
#         # Clean the input based on your specific split format
#         processed_tag_ids = [int(t_id) for t_id in tag_ids[0].split(",") if t_id.strip()]
        
#         # Remove existing links for this dataset
#         statement = delete(DatasetTag).where(DatasetTag.dataset_id == dataset_id)
#         session.exec(statement)
        
#         # Add new links
#         for t_id in processed_tag_ids:
#             new_link = DatasetTag(dataset_id=dataset_id, tag_id=t_id)
#             session.add(new_link)

#     session.add(db_dataset)
#     session.commit()
#     session.refresh(db_dataset)
#     return db_dataset

# @router.get("/dataset/{dataset_id}")
# def get_dataset(dataset_id:int,session:Session=Depends(get_session))->DatasetNestedRead:
#     results = session.exec(select(Dataset).where(Dataset.id== dataset_id)).first()
#     return results

# @router.get("/dataset/detail/{dataset_slug}")
# def get_dataset_detail(dataset_slug:str,session:Session=Depends(get_session))->DatasetNestedRead:
#     results = session.exec(select(Dataset).where(Dataset.slug== dataset_slug)).first()
#     return results

# @router.put("/dataset/{dataset_id}")
# def create_dataset(dataset_id:int,name:str=Form(...),description:str=Form(...),file:UploadFile=File(...),session:Session=Depends(get_session))->DatasetRead:
#     db = session.get(Dataset,dataset_id)
#     if not db:
#         raise HTTPException(status_code=404, detail="Dataset not found")
#     if file:
#         if db.file_path and os.path.exists(db.file_path):
#             os.remove(db.file_path)

#         file_path = UPLOAD_DIR / f"{generate_random_string(4)}_{file.filename}"
#         with file_path.open("wb") as buffer:
#             shutil.copyfileobj(file.file,buffer)
#         db.file_path = str(file_path)
    
#     if db.name != name:
#         db.name = name
#         db.slug = generate_unique_slug(name, session, Dataset)

#     db.description = description

#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db 

# # routers for data tag 

# @router.get("/dataset/tag/")
# def get_dataset_tag(session:Session=Depends(get_session))->List[DatasetTagRead]:
#     results = session.exec(select(DatasetTag)).all()
#     return results

# @router.post("/dataset/tag/")
# def create_dataset_tag(dataset_tag_create:DatasetTagCreate,session:Session=Depends(get_session))->DatasetTagRead:
#     db = DatasetTag.model_validate(dataset_tag_create.model_dump(),context={'session':session,'model_class':DatasetTag})
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# @router.get("/dataset/tag/{dataset_id}")
# def get_dataset_tag_by_dataset_id(dataset_id:int,session:Session=Depends(get_session))->DatasetTag:
#     result = session.exec(select(DatasetTag).where(DatasetTag.dataset_id==dataset_id)).first()
#     return result

# @router.put("/dataset/tag/{dataset_tag_id}")
# def update_dataset_tag(dataset_tag_id:int,dataset_tag_update:DatasetTagUpdate,session:Session=Depends(get_session))->DatasetTagRead:
#     db = session.get(DatasetTag,dataset_tag_id)
#     if not db:
#         raise HTTPException(status_code=400,detail='dataset tag not found')
#     update_data = dataset_tag_update.model_dump(exclude_unset=True)
#     for key,value in update_data.items():
#         setattr(db,key,value)
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# # routers for report 
# @router.get('/report')
# def get_reports(session:Session=Depends(get_session))->List[ReportNestedRead]:
#     results = session.exec(select(Report).where(Report.is_active==True)).all()
#     return results

# @router.get("/report/recent")
# def get_recent_reports(session: Session = Depends(get_session))->List[ReportNestedRead]:
#     """
#     Fetch the 10 most recently created reports.
#     """
#     statement = (select(Report).order_by(desc(Report.created_at)).limit(10))    
#     results = session.exec(statement).all()
#     return results

# @router.get("/report/filter")
# def filter_reports_by_tags(tag_ids: List[int] = Query(...), session: Session = Depends(get_session)):
#     """
#     Filter reports that are associated with any of the provided tag IDs.
#     Example: /reports/filter?tag_ids=1&tag_ids=5
#     """
#     print(tag_ids,)
#     statement = (select(Report).join(ReportTag).where(ReportTag.tag_id.in_(tag_ids)).distinct())
    
#     results = session.exec(statement).all()
    
#     return results

# @router.get('/report/{report_id}')
# def get_reports(report_id:int,session:Session=Depends(get_session))->ReportNestedRead:
#     results = session.exec(select(Report).where(Report.id==report_id)).first()
#     return results

# @router.get('/report/detail/{report_slug}')
# def get_report_detail(report_slug:str,session:Session=Depends(get_session))->ReportNestedRead:
#     results = session.exec(select(Report).where(Report.slug==report_slug)).first()
#     return results

# @router.post("/report", response_model=ReportRead)
# def create_report(
#     name: str = Form(...),
#     content: str = Form(...),
#     tag_ids: str = Form(...), # Expecting "1,2,3"
#     session: Session = Depends(get_session)):
#     # 1. Generate unique slug manually (or via validator context)
#     unique_slug = generate_unique_slug(name, session, Report)
    
#     # 2. Create the Report instance
#     db_report = Report(
#         name=name,
#         content=content,
#         slug=unique_slug
#     )
#     session.add(db_report)
#     session.flush() # Get the db_report.id

#     # 3. Handle multiple tags
#     # Clean the string and split it
#     id_list = [int(t_id.strip()) for t_id in tag_ids.split(",") if t_id.strip()]
    
#     for t_id in id_list:
#         report_tag = ReportTag(report_id=db_report.id, tag_id=t_id)
#         session.add(report_tag)

#     session.commit()
#     session.refresh(db_report)
#     return db_report


# @router.patch("/report/{report_id}", response_model=ReportRead)
# def update_report(
#     report_id: int,
#     name: str = Form(None),
#     content: str = Form(None),
#     tag_ids: str = Form(None), # Expecting "1,4,5"
#     session: Session = Depends(get_session)
# ):
#     # 1. Check if report exists
#     db_report = session.get(Report, report_id)
#     if not db_report:
#         raise HTTPException(status_code=404, detail="Report not found")

#     # 2. Update basic fields
#     if name:
#         if name != db_report.name:
#             db_report.slug = generate_unique_slug(name, session, Report)
#         db_report.name = name
#     if content:
#         db_report.content = content

#     if tag_ids is not None:
#         # Delete old tag associations
#         statement = delete(ReportTag).where(ReportTag.report_id == report_id)
#         session.exec(statement)
        
#         # Add new tag associations
#         id_list = [int(t_id.strip()) for t_id in tag_ids.split(",") if t_id.strip()]
#         for t_id in id_list:
#             new_link = ReportTag(report_id=report_id, tag_id=t_id)
#             session.add(new_link)

#     session.add(db_report)
#     session.commit()
#     session.refresh(db_report)
#     return db_report




# @router.post("/report/tag/")
# def create_report_tag(report_tag_create:ReportTagCreate,session:Session=Depends(get_session))->ReportTagRead:
#     db = ReportTag.model_validate(report_tag_create.model_dump(),context={'session':session,'model_class':ReportTag})
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

# @router.get("/report/tag/{report_id}")
# def get_report_tag_by_report_id(report_id:int,session:Session=Depends(get_session))->ReportTagRead:
#     result = session.exec(select(ReportTag).where(ReportTag.report_id== report_id)).first()
#     return result


# @router.put("/report/tag/{report_tag_id}")
# def update_report_tag(report_tag_id:int,report_tag_update:ReportTagUpdate,session:Session=Depends(get_session))->ReportTagRead:
#     db = session.get(ReportTag,report_tag_id)
#     if not db:
#         raise HTTPException(status_code=400,detail='report tag not found')
#     update_data = report_tag_update.model_dump(exclude_unset=True)
#     for key,value in update_data.items():
#         setattr(db,key,value)
#     session.add(db)
#     session.commit()
#     session.refresh(db)
#     return db

 






