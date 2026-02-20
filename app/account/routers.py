import jwt
from jwt.exceptions import InvalidTokenError

from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,status
from app.account.utils import bearer_scheme,get_password_hash,create_access_token,verify_password
from app.database import get_session
from app.account.models import User,UserRead,RegisterUser,Token,LoginUser
from sqlmodel import Session,select

from app.config import settings

from fastapi.security import OAuth2PasswordRequestForm,HTTPAuthorizationCredentials


router = APIRouter(
    prefix="/account",
    tags=["account"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# async def get_current_user(
#     token: Annotated[str, Depends(oauth2_scheme)],
#     session: Annotated[Session, Depends(get_session)]
# ) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#     except InvalidTokenError:
#         raise credentials_exception
        
#     user = session.exec(select(User).where(User.username == username)).first()
#     if user is None:
#         raise credentials_exception
#     return user


async def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)]
) -> User:
    try:
        payload = jwt.decode(auth.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
        if not username: raise Exception()
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token")
    
    user = session.exec(select(User).where(User.username == username)).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/register")
def register(register_user:RegisterUser,session:Session=Depends(get_session))->UserRead:
    existing_user = session.exec(select(User).where(User.username==register_user.username)).first()
    if existing_user:
        raise HTTPException(status_code=404, detail="user with username already exists")
    user = User(username=register_user.username,hashed_password=get_password_hash(register_user.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/login")
def login(login_user:LoginUser,session:Session=Depends(get_session))->Token:
    user = session.exec(select(User).where(User.username == login_user.username)).first()
    if not user or not verify_password(login_user.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)])->UserRead:
    return current_user



    

