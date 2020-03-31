from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()
app.counter = 0
app.patients = {}


@app.get("/")
def root():
    return {"message": "Hello World during the coronavirus pandemic!"}


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


def counter():
    app.counter += 1
    return app.counter


class AddNewPatient(BaseModel):
    name: str
    surename: str


class ReturnPatient(BaseModel):
    id: int = app.counter
    patient: Dict


@app.post("/patient", response_model=ReturnPatient)
def add_patient(patient_info: AddNewPatient):
    _id = app.counter
    app.patients[_id] = patient_info.dict()
    counter()
    return ReturnPatient(id=_id, patient=patient_info.dict())


@app.get("/patient/{pk}")
def find_patient(pk: int):
    if pk not in app.patients.keys():
        raise HTTPException(
            status_code=204,
            detail="Patient with this id not found.")
    return app.patients[pk]


@app.get("/allpatients/")
def all_patients():
    return app.patients


@app.get("/testpatients")
def testpatients():
    for i in range(10):
        add_patient(patient_info=AddNewPatient(name=f"J_{i}", surename="B"))
    return app.patients
