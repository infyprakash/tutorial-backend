from typing import Annotated
from fastapi import Header,HTTPException,Depends
from fastapi.security import APIKeyHeader,OAuth2PasswordBearer
from app.config import settings

header_scheme = APIKeyHeader(name='token')
async def get_token_header(x_token: Annotated[str, Depends(header_scheme)]):
    if x_token != settings.api_key:
        raise HTTPException(status_code=400,detail="X-Token header invalid")
