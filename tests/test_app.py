import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from http import HTTPStatus

from fastapi_zero.app import app
from fastapi_zero.database import get_session
from fastapi_zero.models import table_registry
from fastapi_zero.schemas import UserPublic

@pytest.fixture
def client(session):
    def get_session_override():
        return session
        
    
    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client
    
    app.dependency_overrides.clear()

def test_ola_mundo(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message':'Olá, mundo.'}


def test_create_user(client):
    response = client.post(
        '/users',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'alice',
        'email': 'alice@example.com',
        'id': 1,
    }

def test_read_user(client):
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}

def test_read_users_with_users(client, user):
    user_schema = UserPublic.from_orm(user).model_dump()
    response = client.get('/users/')
    assert response.json() == {'users': [user_schema]}


def test_update_user(client, user):
    response = client.put(
        f'/users/{user.id}',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': 1,
    }

def test_update_integrity_error(client, user):
    #criando um registro para Fausto
    client.post(
        '/users/',
        json = {
            'username':'fausto',
            'email':'fausto@example.com',
            'password':'secret',
        },
    )

    # Alterando o user.username  das fixture para Fausto
    response_update = client.put(
        f'/users/{user.id}',
        json = {
            'username':'fausto',
            'email':'bob@example.com',
            'password':'mynewpassword',
        },
    )

    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        'detail': 'Username or Email already exists'
    }

def test_delete_user(client, user):
    response = client.delete(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message':'User Deleted'}

def test_update_user_should_return_not_found__exercicio(client):
    response = client.put(
        '/users/666',
        json = {
            'username':'bob',
            'email':'bob@example.com',
            'password':'secret',
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail':'User not found'}

def test_delete_user_should_return_not_found__exercicio(client):
    response = client.delete('/users/666') 

    assert response.status_code == HTTPStatus.NOT_FOUND 
    assert response.json() == {'detail': 'User not found'}

def test_get_user_should_return_not_found__exercicio(client):
    response = client.get('/users/666')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_get_user___exercicio(client, user):
    # Primeiro, cria o usuário bob
    client.post(
        '/users/',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )

    # Agora sim, busca o usuário com ID 1
    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': 1,
    }
