from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sqlalchemy_string: str = "postgresql://prakash:adminadmin@localhost:5432/tutorialdb"
    api_key:str = "70504d0ef78832dac8bcc465b976033b07261975ec5936a1ea45ac2b5deed372"
    secret_key:str = "41998da4dcf4c423442d8fb6bbd67f3021f8cbae27ee701ce0e63014f90bc07e"
    access_token_expires_days:int = 30 
    algorithm:str = "HS256"
settings = Settings()

