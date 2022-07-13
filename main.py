from fastapi import FastAPI, Form
from pydantic import BaseModel
import numpy as np
import hashlib as hash
import os

data_type_dict = {
    "1" : "1d array",
    "2" : "2d array",
    "3" : "3d array",
    "4" : "picture",
    "5" : "other"
}


class Dataset(BaseModel):
    id: int
    name: str
    data: list[np.float64]
    meta: str | None = None

class Group(BaseModel):
    id: int
    name: str
    children: list[Dataset]
    meta: str | None = None # implemented union as optional variable

class Project(BaseModel):
    id: int
    name: str
    author: str
    groups: list[Group]


app = FastAPI()

"""
path parameters
@app.get("/items/{item_id}")
item_id is a variable that's passed in
async def read_item(item_id):
    return {"item_id" : item_id}

// hashing for authentication
salt = os.urandom(blake2d.SALT_SIZE)
h1 = blake2b(salt=salt1)
h1.update(thing)

request body is data sent from client to API 
use post

"""


@app.get("/")
async def root(): # works like main
    return {"message" : "Hello World"}

@app.post("/projects/")
async def create_project(item: Project):
    # write function for sending data
    # 1. compile data from local file or some input
    # 2. load it into data structure
    # 3. send it
    return item

