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
from app.config import settings

import pandas as pd 
import pyarrow

from app.infography.query_engine import ChartQueryEngine


router = APIRouter(
    prefix="/infography",
    tags=["infography"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = Path("uploads/datasets")
# PARQUET_DIR = Path("parquet_data")
PARQUET_DIR = BASE_DIR / "parquet_data"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_DIR.mkdir(parents=True, exist_ok=True)

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

def get_parquet_filename(filename: str):
    p = Path(filename)
    return f"{p.stem}.parquet"

def get_parquet_filepath(original_path: str):
    # original_path is "uploads/datasets/uuid_name.csv"
    filename = Path(original_path).name
    pq_name = get_parquet_filename(filename)
    # This returns the absolute path to the parquet file
    return PARQUET_DIR / pq_name


def convert_to_parquet(file_path):
    filename = file_path.split("/")[-1]
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith('.json'):
        df = pd.read_json(file_path)
    elif filename.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Invalid file input")

    output_filename = get_parquet_filename(filename=filename)
    output_file = PARQUET_DIR / output_filename
    df.to_parquet(output_file,engine='pyarrow',index=False)
    
    
# category routes 

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):

    unique_filename = f"{uuid4().hex}_{file.filename}"
    path = f"uploads/graphs/{unique_filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"{settings.api_host}{path}"}

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

@router.get("/datasets/all", response_model=List[DatasetNestedRead])
def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    statement = (
        select(Dataset)
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
    
    # # Save file
    
    file_path = save_file(file)
    convert_to_parquet(file_path=file_path)

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


# @router.put("/datasets/{dataset_id}", response_model=DatasetNestedRead)
# def update_dataset(
#     dataset_id: int,
#     name: Optional[str] = Form(None),
#     description: Optional[str] = Form(None),
#     category_id: Optional[int] = Form(None),
#     tag_ids: Optional[str] = Form(None),
#     file: Optional[UploadFile] = File(None),
#     session: Session = Depends(get_session),
# ):

#     dataset = session.get(Dataset, dataset_id)

#     if not dataset:
#         raise HTTPException(status_code=404, detail="Dataset not found.")

#     # Update fields
#     if name:
#         dataset.name = name

#     if description:
#         dataset.description = description

#     if category_id is not None:
#         category = session.get(Category, category_id)
#         if not category:
#             raise HTTPException(status_code=404, detail="Category not found.")
#         dataset.category_id = category_id

#     # Replace file if provided
#     if file:
#         # Delete old file safely
#         if dataset.file_path and Path(dataset.file_path).exists():
#             Path(dataset.file_path).unlink()

#         dataset.file_path = save_file(file)

#     session.add(dataset)
#     session.commit()

#     # Replace tags if provided
#     if tag_ids is not None:
#         # Remove old links
#         existing_links = session.exec(
#             select(DatasetTag).where(DatasetTag.dataset_id == dataset_id)
#         ).all()

#         for link in existing_links:
#             session.delete(link)

#         session.commit()

#         # Add new links
#         tag_id_list = [int(t.strip()) for t in tag_ids.split(",")]

#         for tag_id in tag_id_list:
#             tag = session.get(Tag, tag_id)
#             if not tag:
#                 raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")

#             new_link = DatasetTag(dataset_id=dataset_id, tag_id=tag_id)
#             session.add(new_link)

#         session.commit()

#     return get_dataset_with_relations(dataset_id, session)

@router.put("/datasets/{dataset_id}", response_model=DatasetNestedRead)
def update_dataset(
    dataset_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tag_ids: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),   
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
):

    dataset = session.get(Dataset, dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")



    if name:
        dataset.name = name

    if description:
        dataset.description = description

    if category_id is not None:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        dataset.category_id = category_id

    if is_active is not None:
        dataset.is_active = is_active

    if file:
        # Delete old file safely
        if dataset.file_path and Path(dataset.file_path).exists():
            Path(dataset.file_path).unlink()

        dataset.file_path = save_file(file)

        convert_to_parquet(file_path=dataset.file_path)

    session.add(dataset)
    session.commit()
    session.refresh(dataset)  

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

            selectinload(Report.topics).selectinload(ReportTopic.graphs),

            selectinload(Report.dataset_links).selectinload(ReportDataset.dataset),
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

import asyncio



@router.get("/reports/graphconfig/{report_id}/{topic_id}/{graph_id}")
async def get_report_related_graph_config(
    report_id: int,
    topic_id: int,
    graph_id: int,
    session: Session = Depends(get_session)  # use your current sync session
):
    # fetch related dataset
    report_dataset = session.exec(
        select(ReportDataset).where(ReportDataset.report_id == report_id)
    ).first()
    if not report_dataset:
        return {"error": "ReportDataset not found"}

    dataset = session.exec(
        select(Dataset).where(Dataset.id == report_dataset.dataset_id)
    ).first()
    if not dataset:
        return {"error": "Dataset not found"}

    report_graph = session.exec(
        select(ReportGraph).where(ReportGraph.id == graph_id)
    ).first()
    if not report_graph:
        return {"error": "ReportGraph not found"}

    # prepare chart config
    parquet_path = get_parquet_filepath(dataset.file_path)
    chart_config = json.loads(report_graph.chart_config)
    chart_config['dataset'] = str(parquet_path)

    # run CPU-heavy chart execution in threadpool to avoid blocking server
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, lambda: ChartQueryEngine(config=chart_config).execute()
    )
    return result

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


# routers for reportTopic

@router.post("/report-topics", response_model=ReportTopicRead)
def create_report_topic(
    payload: ReportTopicCreate,
    session: Session = Depends(get_session),
):
    # Validate report
    report = session.get(Report, payload.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    topic = ReportTopic.model_validate(
        payload.model_dump(),
        context={"session": session, "model_class": ReportTopic},
    )

    session.add(topic)
    session.commit()
    session.refresh(topic)

    return topic

@router.get("/report-topics/report/{report_id}", response_model=List[ReportTopicNestedRead])
def filter_report_topics_by_report(
    report_id: int,
    session: Session = Depends(get_session),
):
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    statement = (
        select(ReportTopic)
        .where(ReportTopic.report_id == report_id)
        .options(
            selectinload(ReportTopic.graphs)
        )
        .order_by(desc(ReportTopic.created_at))
    )

    topics = session.exec(statement).all()
    return topics

@router.get("/report-topics", response_model=List[ReportTopicNestedRead])
def list_report_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    session: Session = Depends(get_session),
):
    offset = (page - 1) * page_size

    statement = (
        select(ReportTopic)
        .options(
            selectinload(ReportTopic.graphs)
        )
        .order_by(desc(ReportTopic.created_at))
    )

    topics = session.exec(statement).all()
    return topics


@router.put("/report-topics/{topic_id}", response_model=ReportTopicNestedRead)
def update_report_topic(
    topic_id: int,
    name: Optional[str] = Form(None),
    topic_content: Optional[str] = Form(None),
    report_id: Optional[int] = Form(None),
    session: Session = Depends(get_session),
):
    topic = session.get(ReportTopic, topic_id)

    if not topic:
        raise HTTPException(status_code=404, detail="Report topic not found.")

    # Update fields
    if name:
        topic.name = name

    if topic_content:
        topic.topic_content = topic_content

    if report_id is not None:
        report = session.get(Report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        topic.report_id = report_id

    session.add(topic)
    session.commit()

    # Reload with relations (graphs)
    statement = (
        select(ReportTopic)
        .where(ReportTopic.id == topic_id)
        .options(selectinload(ReportTopic.graphs))
    )

    updated_topic = session.exec(statement).first()

    return updated_topic

# routers for ReportGraph 

def get_report_graph_with_relations(graph_id: int, session: Session):
    statement = (
        select(ReportGraph)
        .where(ReportGraph.id == graph_id)
        .options(
            selectinload(ReportGraph.topic),
            selectinload(ReportGraph.dataset),  
        )
    )
    return session.exec(statement).first()

@router.post("/report-graphs", response_model=ReportGraphRead)
def create_report_graph(
    payload: ReportGraphCreate,
    session: Session = Depends(get_session),
):
    topic = session.get(ReportTopic, payload.report_topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Report topic not found.")

    if payload.dataset_id:
        dataset = session.get(Dataset, payload.dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found.")

    graph = ReportGraph(**payload.model_dump())

    session.add(graph)
    session.commit()
    session.refresh(graph)

    if graph.chart_config:
        chart_config = graph.chart_config
        if dataset:
            parquet_path = get_parquet_filepath(dataset.file_path)
            config = json.loads(chart_config)
            config["dataset"] = str(parquet_path)
            result = ChartQueryEngine(config=config).execute().get("data")
            config["data"] = result
            graph.chart_config = json.dumps(config)
    
    session.add(graph)
    session.commit()
    session.refresh(graph)

    return graph


@router.get(
    "/report-graphs/topic/{report_topic_id}",
    response_model=List[ReportGraphRead],
)
def filter_graphs_by_topic(
    report_topic_id: int,
    session: Session = Depends(get_session),
):
    topic = session.get(ReportTopic, report_topic_id)

    if not topic:
        raise HTTPException(status_code=404, detail="Report topic not found.")

    statement = (
        select(ReportGraph)
        .where(ReportGraph.report_topic_id == report_topic_id)
        .order_by(desc(ReportGraph.created_at))
    )

    graphs = session.exec(statement).all()

    return graphs


@router.put("/report-graphs/{graph_id}", response_model=ReportGraphRead)
def update_report_graph(
    graph_id: int,
    title: Optional[str] = Form(None),
    chart_config: Optional[str] = Form(None),
    report_topic_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),  
    session: Session = Depends(get_session),
):
    graph = session.get(ReportGraph, graph_id)

    if not graph:
        raise HTTPException(status_code=404, detail="Report graph not found.")

    if title:
        graph.title = title

    if dataset_id is not None:
        if dataset_id:
            dataset = session.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found.")
        graph.dataset_id = dataset_id

    if report_topic_id is not None:
        topic = session.get(ReportTopic, report_topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Report topic not found.")
        graph.report_topic_id = report_topic_id

    dataset = None

    if graph.dataset_id:
        dataset = session.get(Dataset, graph.dataset_id)

    if not dataset:
        topic = session.get(ReportTopic, graph.report_topic_id)
        if topic:
            report_dataset = session.exec(
                select(ReportDataset).where(
                    ReportDataset.report_id == topic.report_id
                )
            ).first()

            if report_dataset:
                dataset = session.get(Dataset, report_dataset.dataset_id)

    if chart_config:
        if not dataset:
            raise HTTPException(status_code=400, detail="No dataset available for graph")

        parquet_path = get_parquet_filepath(dataset.file_path)
        config = json.loads(chart_config)
        config["dataset"] = str(parquet_path)

        result = ChartQueryEngine(config=config).execute().get("data")

        config["data"] = result
        graph.chart_config = json.dumps(config)

    session.add(graph)
    session.commit()
    session.refresh(graph)

    return graph


@router.get("/report-graphs", response_model=List[ReportGraphRead])
def get_all_report_graphs(session: Session = Depends(get_session)):
    statement = (
        select(ReportGraph)
        .order_by(desc(ReportGraph.created_at))
    )

    graphs = session.exec(statement).all()
    return graphs

# routers for ReportDataset
def get_report_dataset_with_relations(link_id: int, session: Session):
    statement = (
        select(ReportDataset)
        .where(ReportDataset.id == link_id)
        .options(selectinload(ReportDataset.dataset))
    )
    return session.exec(statement).first()

@router.post("/report-datasets", response_model=ReportDatasetNestedRead)
def create_report_dataset(
    payload: ReportDatasetCreate,
    session: Session = Depends(get_session),
):
    report = session.get(Report, payload.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    dataset = session.get(Dataset, payload.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    link = ReportDataset(**payload.model_dump())

    session.add(link)
    session.commit()
    session.refresh(link)

    return get_report_dataset_with_relations(link.id, session)


@router.get(
    "/report-datasets/report/{report_id}",
    response_model=List[ReportDatasetNestedRead],
)
def filter_datasets_by_report(
    report_id: int,
    session: Session = Depends(get_session),
):
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    statement = (
        select(ReportDataset)
        .where(ReportDataset.report_id == report_id)
        .options(selectinload(ReportDataset.dataset))
    )

    links = session.exec(statement).all()

    return links

# @router.put("/report-datasets/{link_id}", response_model=ReportDatasetNestedRead)
# def update_report_dataset(
#     link_id: int,
#     report_id: Optional[int] = Form(None),
#     dataset_id: Optional[int] = Form(None),
#     session: Session = Depends(get_session),
# ):
#     link = session.get(ReportDataset, link_id)

#     if not link:
#         raise HTTPException(status_code=404, detail="Report dataset link not found.")

#     if report_id is not None:
#         report = session.get(Report, report_id)
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found.")
#         link.report_id = report_id

#     if dataset_id is not None:
#         dataset = session.get(Dataset, dataset_id)
#         if not dataset:
#             raise HTTPException(status_code=404, detail="Dataset not found.")
#         link.dataset_id = dataset_id

#     session.add(link)
#     session.commit()

#     return get_report_dataset_with_relations(link_id, session)

from fastapi import Body

@router.put("/report-datasets/{link_id}", response_model=ReportDatasetNestedRead)
def update_report_dataset(
    link_id: int,
    report_id: Optional[int] = Body(None),
    dataset_id: Optional[int] = Body(None),
    session: Session = Depends(get_session),
):
    link = session.get(ReportDataset, link_id)

    if not link:
        raise HTTPException(status_code=404, detail="Report dataset link not found.")

    if report_id is not None:
        report = session.get(Report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        link.report_id = report_id

    if dataset_id is not None:
        dataset = session.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        link.dataset_id = dataset_id


    session.commit()
    session.refresh(link)

    return get_report_dataset_with_relations(link_id, session)

@router.get("/report-datasets", response_model=List[ReportDatasetNestedRead])
def get_all_report_datasets(session: Session = Depends(get_session)):
    statement = (
        select(ReportDataset)
        .options(selectinload(ReportDataset.dataset))
    )

    links = session.exec(statement).all()

    return links