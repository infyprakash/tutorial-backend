from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_user:str 
    db_password:str
    db_host:str 
    database:str 
    token_api_key:str 
    auth_secret_key:str 

    @computed_field
    @property
    def sqlalchemy_string(self)->str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:5432/{self.database}"
    
    @computed_field
    @property
    def api_key(self)->str:
        return self.token_api_key
    
    @computed_field
    @property
    def secret_key(self)->str:
        return self.auth_secret_key
    
    @computed_field
    @property
    def access_token_expires_day(self)->int:
        return 30

    @computed_field
    @property
    def algorithm(self)->str:
        return "HS256"
    

    model_config = SettingsConfigDict(env_file=".env")
    

    

settings = Settings()

