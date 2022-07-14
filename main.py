from re import L
from fastapi import FastAPI, Form
from pydantic import BaseModel
import numpy as np
import hashlib as hash
import os
import pymongo
import variables as var
from pymongo.mongo_client import MongoClient


data_type_dict = {
    1 : "1d array",
    2 : "2d array",
    3 : "3d array",
    4 : "picture",
    5 : "other"
}

class Dataset(BaseModel):
    id: int
    name: str
    data: list[np.float64]
    meta: str | None = None
    data_type: dict

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

# remove name and password from here and declare them in separate file
string = "mongodb+srv://" + var.username + ":" + var.password + "@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(string)
db = client["test"] # defines database called test 
app = FastAPI()

@app.get("/")
async def connection_test(): # works like main
    try:
        thing = str(client.server_info)
    except:
        thing = "failed to connect"
    return {"message" : thing}
# end get
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

can return the body as a json by returning just an object
This allows for a validation
"""


#@app.get("/send_project")
## sends the project given a whole set of data
#async def send_test(): # sends the data to the server
#    item = Item(name="thing", description="random description", price=0.42)
#    ### creates the things collection
#    mycol = db["things"]
#    ### convert the object data into union
#    json_format = {
#        "name" : item.name,
#        "description" : item.description,
#        "price" : item.price,
#        "tax" : item.tax
#    }
#    err = mycol.insert_one(json_format)
#    ### put it into the database
#    return item

@app.post("/get_test/{collection_id}/{project_name}") # sends the data to the user
async def get_test(collection_id, ):
    collections = db.list_collection_names()
    # accessing database entries
    col = db[collection_id] # opens the chosen collection
    # print the data sets
    temp =  col.find_one()
    if temp != None:
        item = Item(name = temp.get('name'), description= temp.get('description'), price=temp.get('price'), tax=temp.get('tax'))
        #temp = assign_values(item)
    else:
        item = {"message": "Failed to find"}
    #print(temp) # json object
    return item
    #entry = temp.get('name')
    #return json_return
# attempt at picking up local file and putting it into a database using
