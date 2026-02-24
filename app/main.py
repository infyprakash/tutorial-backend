from fastapi import FastAPI,Depends
from app.database import engine
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


# from app.routers import course as course_router
# from app.routers import chapter as chapter_router
# from app.routers import subchapter as subchapter_router
# from app.routers import coursecontent as coursecontent_router

from app.tutorial import routers as tutorial_router
from app.account import routers as account_router
from app.neclicense import router as nec_router

from app.dependencies import get_token_header


@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting up..........")
    print("creating database and tables................")
    # from app.models import Course,Chapter,SubChapter,CourseContent
    from app.tutorial.models import Course,Chapter,SubChapter,CourseContent
    SQLModel.metadata.create_all(engine)
    yield
    print("Shutting down........")

app = FastAPI(lifespan=lifespan)
app.include_router(tutorial_router.router)
app.include_router(account_router.router)
app.include_router(nec_router.router)

# app.include_router(course_router.router)
# app.include_router(chapter_router.router)
# app.include_router(subchapter_router.router)
# app.include_router(coursecontent_router.router)

origins = [
    "https://ezexplanation.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    







