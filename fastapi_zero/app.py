from http import HTTPStatus
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import  IntegrityError

from fastapi import Depends, FastAPI, HTTPException

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import Message,Token, UserDB, UserSchema, UserPublic, UserList
from fastapi_zero.security import create_access_token, get_current_user, get_password_hash, verify_password

app = FastAPI()
database = []

@app.get('/', status_code=HTTPStatus.OK, response_model = Message)
def read_root():
    return {'message':'Olá, mundo.'}


@app.post('/users/', status_code = HTTPStatus.CREATED, response_model = UserPublic)
def created_user(user: UserSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code= HTTPStatus.CONFLICT,
                detail = 'User already exists',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code = HTTPStatus.CONFLICT,
                detail = 'email already exists',
            )

    hashed_password = get_password_hash(user.password)   
    
    db_user = User(username = user.username, password = hashed_password, email = user.email)
    session.add(db_user)
    session.commit()
    session.refresh(db_user) 

    return db_user

@app.post('/token', response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session:Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user:
        raise HTTPException(
            status_code= HTTPStatus.UNAUTHORIZED,
            detail = 'Incorrect email or password'
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code= HTTPStatus.UNAUTHORIZED,
            detail = 'Incorrect email or password'  
        )
    
    access_token = create_access_token(data = {'sub': user.email})

    return {'access_token':access_token, 'token_type': 'bearer'}


@app.get('/users/', response_model=UserList)
def read_users(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
):
    users = session.scalars(select(User).offset(skip).limit(limit)).all()
    return {'users': users}


@app.put('/users/{user_id}', response_model=UserPublic)
def update_user(
    user_id: int, 
    user: UserSchema, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
):  
    db_user = session.scalar(select(User).where(User.id == user_id))
    if not db_user: 
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail= 'Not enough permissions'
        )

    try:
        current_user.username = user.username
        current_user.password = get_password_hash(user.password)
        current_user.email = user.email
        session.commit()
        session.refresh(current_user)

        return current_user
    except IntegrityError: 
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, 
            detail='Username or Email already exists'
        )

@app.delete('/users/{user_id}', response_model=Message)
def delete_user(
    user_id:int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):

    db_user = session.scalar(select(User).where(User.id == user_id))

    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )
    
    session.delete(db_user)
    session.commit()

    return {'message':'User Deleted'}
    
@app.get('/users/{user_id}', response_model=UserPublic)
def read_user__exercicio( user_id: int, user: UserSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    return db_user