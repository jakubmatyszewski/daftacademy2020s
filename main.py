import secrets
import sqlite3
from typing import List
from hashlib import sha256
from typing import Dict
from fastapi import (
    Depends,
    Response,
    Request,
    FastAPI,
    HTTPException,
    status,
    Cookie
    )
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.responses import RedirectResponse
from functools import wraps


app = FastAPI()

app.counter = 0
app.patients = {}
app.tokens = {}
app.secret_key = "very constatn and random secret, best 64 characters"

security = HTTPBasic()

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


@app.get("/")
def root():
    return {"message": "Hello World during the coronavirus pandemic!"}


def is_logged_in(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        request = kwargs["request"]
        try:
            session_token = request.cookies["session_token"]
        except KeyError:
            session_token = Cookie(None)
        if session_token not in app.tokens.keys():
            raise HTTPException(status_code=401, detail="Unauthorized")
        else:
            return fn(*args, **kwargs)
    return inner


@app.get("/tracks")
async def tracks(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        f"SELECT * FROM tracks LIMIT {per_page} OFFSET {page * per_page}"
        ).fetchall()
    return data


@app.get("/tracks/composers/")
async def composer_tracks(response: Response, composer_name: str):
    app.db_connection.row_factory = lambda cursor, row: row[0]
    data = app.db_connection.execute(
        f"""SELECT name
            FROM tracks
            WHERE composer IS '{composer_name}'
            ORDER BY name"""
        ).fetchall()
    if len(data) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": {"error": "Couldn't find songs by this composer."}}
    else:
        return data


class Album(BaseModel):
    title: str
    artist_id: int


@app.post("/albums")
async def add_albums(response: Response, album: Album):
    app.db_connection.row_factory = lambda cursor, row: row[0]
    data = app.db_connection.execute(
        f"SELECT * FROM artists WHERE ArtistId = ?", (album.artist_id,)
        ).fetchall()
    if len(data) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail":
                {"error": "Can't add album for non-existant artist id."}
                }
    else:
        cursor = app.db_connection.execute(
            f"""INSERT INTO albums (Title, ArtistId)
                VALUES (?, ?)""", (album.title, album.artist_id)
            )
        app.db_connection.commit()
        response.status_code = status.HTTP_201_CREATED
        return {
            "AlbumId": cursor.lastrowid,
            "Title": album.title,
            "ArtistId": album.artist_id,
        }


@app.get("/albums/{album_id}")
async def get_album_by_id(album_id: int):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        f"SELECT * FROM albums WHERE AlbumId = ?", (album_id,)
        ).fetchone()
    return data


class Customer(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None


@app.put("/customers/{customer_id}")
async def update_customer_info(
        response: Response,
        customer_id: int,
        customer: Customer
     ):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
            f"SELECT * FROM customers WHERE CustomerId = ?", (customer_id,)
        ).fetchone()
    if data is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": {"error": "Couldn't find customer with this id."}}
    update_customer = customer.dict(exclude_unset=True)
    query = [f"{k} = '{v}'" for k, v in update_customer.items()]
    query = ', '.join(query)
    cursor = app.db_connection.execute(
        f"UPDATE customers SET {query} WHERE customerid = ?", (customer_id,)
    )
    app.db_connection.commit()

    data = app.db_connection.execute(
            f"SELECT * FROM customers WHERE CustomerId = ?", (customer_id,)
        ).fetchone()

    return data


@app.get("/welcome")
@is_logged_in
def welcome(request: Request, session_token: str = Cookie(None)):
    user = app.tokens[session_token]
    return templates.TemplateResponse(
        "index.html", {"request": request, "user": user})


@app.post("/login")
def get_current_user(
        response: Response,
        credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "trudnY")
    correct_password = secrets.compare_digest(credentials.password, "PaC13Nt")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password")
    session_token = sha256(bytes(
        f"{credentials.username}{credentials.password}{app.secret_key}",
        encoding='utf8')).hexdigest()
    response = RedirectResponse(
        url='/welcome',
        status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session_token", value=session_token)
    app.tokens[session_token] = credentials.username
    return response


@app.post("/logout")
@is_logged_in
def logout_current_user(request: Request, session_token: str = Cookie(None)):
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="session_token")
    del app.tokens[session_token]
    return response


@app.get("/method")
@app.post("/method")
@app.put("/method")
@app.delete("/method")
def get_method(request: Request):
    return {"method": str(request.method)}


def counter():
    app.counter += 1
    return app.counter


class AddNewPatient(BaseModel):
    name: str
    surname: str


class ReturnPatient(BaseModel):
    name: str
    surname: str


@app.post("/patient")
@is_logged_in
def add_patient(request: Request, patient_info: AddNewPatient):
    _id = app.counter
    app.patients[_id] = patient_info.dict()
    counter()
    return RedirectResponse(
        f"/patient/{_id}",
        status_code=status.HTTP_302_FOUND)


@app.get("/patient")
@is_logged_in
def get_all_patients(request: Request):
    return app.patients


@app.get("/patient/{pk}", response_model=ReturnPatient)
@is_logged_in
def find_patient(request: Request, pk: int):
    if pk not in app.patients.keys():
        raise HTTPException(
            status_code=204,
            detail="Patient with this id not found.")
    return app.patients[pk]


@app.delete("/patient/{pk}")
@is_logged_in
def remove_patient(request: Request, pk: int):
    if pk not in app.patients.keys():
        raise HTTPException(
            status_code=204,
            detail="Patient with this id not found.")
    app.patients.pop(pk)
    raise HTTPException(
            status_code=204,
            detail="Patient removed.")
