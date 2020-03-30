from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()
app.counter = 0


@app.get("/")
def root():
    return {"message": "Hello World during the coronavirus pandemic!"}


class HelloResp(BaseModel):
    message: str


@app.get("/hello/{name}", response_model=HelloResp)
def read_item(name: str):
    return HelloResp(message=f"Hello {name}")


class GiveMeSomethingRq(BaseModel):
    first_key: str


class GiveMeSomethingResp(BaseModel):
    received: Dict
    constant_data: str = "python jest super"


@app.post("/dej/mi/coś", response_model=GiveMeSomethingResp)
def receive_something(rq: GiveMeSomethingRq):
    return GiveMeSomethingResp(received=rq.dict())


@app.get("/method")
def get_method():
    return {"method": "GET"}


@app.post("/method")
def post_method():
    return {"method": "POST"}


@app.put("/method")
def put_method():
    return {"method": "PUT"}


@app.delete("/method")
def delete_method():
    return {"method": "DELETE"}


@app.get('/counter')
def counter():
    app.counter += 1
    return app.counter


class AddNewPatient(BaseModel):
    name: str
    surename: str


class ReturnPatient(BaseModel):
    id: int = app.counter
    patient: Dict


app.patients = {}


@app.post("/patient", response_model=ReturnPatient)
def add_patient(patient_info: AddNewPatient):
    _id = counter()
    app.patients[_id] = patient_info.dict()
    return ReturnPatient(id=_id, patient=patient_info.dict())


@app.get("/patient/{pk}")
def find_patient(pk: int):
    if pk not in app.patients.keys():
        raise HTTPException(
            status_code=204,
            detail="Patient with this id not found.")
    return app.patients[pk]
