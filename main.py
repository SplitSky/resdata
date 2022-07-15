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
    data_type: str

    def convertJSON(self):
        json_dict = {
            "id" : self.id,
            "name" : self.name,
            "data" : self.data,
            "meta" : self.meta,
            "data_type" : self.data_type
        }
        return json_dict

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



#@app.post("/get_test/{project_name}/{experiment_id}/{database_id}") # sends the data to the user
#async def find_(collection_id, experiment_id, databse_id):
#    collections = db.list_collection_names()
    # accessing database entries
#    col = db[collection_id] # opens the chosen collection
    # print the data sets
#    temp =  col.find_one()
#    if temp != None:
        #item = Item(name = temp.get('name'), description= temp.get('description'), price=temp.get('price'), tax=temp.get('tax'))
        #temp = assign_values(item)
#    else:
#        item = {"message": "Failed to find"}
    #print(temp) # json object
#    return item
    #entry = temp.get('name')
    #return json_return
# attempt at picking up local file and putting it into a database using


"""
structure
1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
2. Call to insert bulk groups "/{project_id}/" - post
3. Call to insert a whole project "/" - post
4. Call to update a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - patch
5. Call to return a query of a database return all projects "/" - get
6. Call to return a query of a project and return all experiment names - "/{project_id}/" - get
7. Call to return a query of an experiment and return all dataset names - "/{project_id}/{experiment_id}/" - get
8. Call to return a query of a dataset to return queried data - "/{project_id}/{experiment_id}/{dataset_id}" - get
"""

@app.post("/{project_id}/{experiment_id}/{dataset_id}")
async def insert_single_dataset(project_id, experiment_id, dataset_id):
    project_temp = db[project_id] # returns the project
    experiment_temp = project_temp[experiment_id] # returns the experiment
    dataset_temp = experiment_temp[dataset_id] # returns the dataset 

    # data insert here
    
    data_temp = Dataset(id=1, name="test1", data=np.array([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]), data_type="1d array")
    # end of data insert
    dataset_temp.insert_one(data_temp.convertJSON())
     

# end def
# end post
    id: int
    name: str
    data: list[np.float64]
    meta: str | None = None
    data_type: dict

