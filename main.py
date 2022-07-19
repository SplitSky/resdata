from re import L
from fastapi import FastAPI, Form
from pydantic import BaseModel
import numpy as np
import hashlib as hash
import os
import pymongo
import variables as var
from pymongo.mongo_client import MongoClient
import json

class Dataset(BaseModel):
    name: str
    data: list
    meta: str | None = None
    data_type: str

    def convertJSON(self):
        json_dict = {
            "name" : self.name,
            "meta" : self.meta,
            "data_type" : self.data_type,
            "data" : self.data 
        }
        return json_dict

class Experiment(BaseModel):
    name: str
    children: list[Dataset]
    meta: str | None = None # implemented union as optional variable
    def convertJSON(self):
    ### uses the nesting feature of mongodb to allow for hierarchal storage of data
        temp= []
        i = 0
        for dataset in self.children:
            temp.append(dataset.convertJSON())
            # appends the groups 
            i += 1
        json_dict  = {
            "name" : self.name,
            "meta" : self.meta,
            "datasets" : temp # datatype is list -> remember request body deals with validation       
        }

        return json_dict

class Project(BaseModel):
    name: str | None = None
    author: str | None = None
    groups: list[Experiment]
    meta: str | None = None

    def convertJSON(self):
        temp = []
        i = 0
        for group in self.groups:
            temp.append(group.convertJSON())
            i += 1

        json_dict = {
            "name" : self.name,
            "author" : self.author,
            "meta" : self.meta,
            "groups" : temp
        }
        return json_dict

    def convertDictionary(self, dict_in):
        # converts this object into the layout of the inserted nested dictionary
        experiments = []
        ### check if there are any experiments
        self.name = dict_in.get("name")
        self.author = dict_in.get("author")
        self.meta=dict_in.get("meta")

        for i, experiment in dict_in.get("groups").items():
            # experiments is also a dictionary with {number: {dictionary ... }}
            # i and j are not accessed but are required to keep the format as a dictionary during the creation of it
            datasets = []
            for j, dataset in experiment.get("datasets").items():
                datasets.append(Dataset(name=dataset.get("name"),data=dataset.get("data"),meta=dataset.get("meta"), data_type=dataset.get("data_type")))
            experiments.append(Experiment(name=experiment.get("name"),children=datasets,meta=experiment.get("meta")))
        self.groups = experiments


string = "mongodb+srv://" + var.username + ":" + var.password + "@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(string)
db = client["test_struct"] # defines database called test 
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
# 0. passing object in
@app.post("/{project_id}/{experiment_id}/{dataset_id}/test")
async def test(dataset: Dataset):
    return dataset


@app.post("/{project_id}/{experiment_id}/{dataset_id}")
# 1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
async def insert_single_dataset(project_id, experiment_id, dataset_id):
    project_temp = db[project_id] # returns the project
    experiment_temp = project_temp[experiment_id] # returns the experiment or creates if doesn't exist
    dataset_temp = experiment_temp[dataset_id] # returns the dataset 
    # data insert here
    temp = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
    data_temp = Dataset(name="test1", data=temp, data_type="1d array")
    # each experiment has multiple data sets. Each is nested in the experiment collection
    # end of data insert
    dataset_temp.insert_one(data_temp.convertJSON()) # data insert into database
    return data_temp # returns the request body to the API for verification
# end def
# end post

@app.post("/{project_id}/{group_id}")
# 2. Call to insert single group "/{project_id}/{experiment_id}" - post
async def insert_group(project_id, group_id):
    project_temp = db[project_id]
    experiment_temp = project_temp[group_id]
    # data insert here
    dataset_in = Dataset(name="test1", data=[1,2,3,4,5,6,7,8,9,10], data_type="1d array")
    experiment_in = Experiment(name="exp_test_1", children=[dataset_in], meta="This is a test experiment")
    experiment_temp.insert_one(experiment_in.convertJSON())
    return experiment_temp # returns a request body to the API for verification

@app.post("/{project_id}") #### this one ***************************************************************************************************************************************
# 3. Call to insert a whole project "/" - post
async def insert_project(project_id, json_in: Project):
    project_temp = db[project_id] # access or create project folder in database
    #dictionary_temp = json.loads(json_in) # returns a python object
    project_temp.insert_one(json_in.convertJSON()) # inserts a python dictionary 
    print("testing testing ")
    return project_temp # returns a request body to the API for verification

# 4. Call to update a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - patch
@app.patch("/{project_id}/{experiment_id}/{dataset_id}")
async def update_dataset(project_id, experiment_id, dataset_id):
    project_temp = db[project_id]
    experiment_temp = project_temp[experiment_id]
    database_temp = experiment_temp[dataset_id]
    # retrieve the dataset
    dataset_edit = database_temp.find_one(name=dataset_id)
    # update the dataset with data
    new_data = [1,1,1,1,1,1]

    if dataset_edit != None:
        return {"message" : "No file found"}
    else:
        experiment_temp.update_one({"name" : dataset_id}, {"data" : new_data}) 
        return experiment_temp.find({"name" : dataset_id})
    # return confirmation and body of dataset post edit

# 5. Call to return a query of a database return all projects "/" - get
@app.get("/")
async def returm_all_project_names():
    return {"project names" : db.list_collection_names()}
# end def
# end get


# 6. Call to return a query of a project and return all experiment names - "/{project_id}/" - get
@app.get("/{project_id}/")
async def return_all_experiment_names(project_id):
    project = db[project_id] # return collection of experiments
    names_temp = []
    for experiment in project.find():
        names_temp.append(experiment.get("name"))

    return {"experiment names" : names_temp}

# 7. Call to return a query of an experiment and return all dataset names - "/{project_id}/{experiment_id}/" - get
@app.get("/{project_id}/{experiment_id}/")
async def return_all_dataset_names(project_id, experiment_id):
    project = db[project_id]
    experiment = project[experiment_id]
    names_temp = []
    for dataset in experiment.find():
        names_temp.append(dataset.get("name"))

    return {"dataset names" : names_temp}


# 8. Call to return a query of a dataset to return queried data - "/{project_id}/{experiment_id}/{dataset_id}" - get
@app.get("/{project_id}/{experiment_id}/{dataset_id}")
async def return_queried_data(project_id, experiment_id, dataset_id):
    project = db[project_id]
    experiment = project[experiment_id]
    dataset = experiment[dataset_id]
    temp_return = {}
    temp = dataset.find() 
    if temp == None:
        return {"message" : "no data found"}
    elif temp == dict:
        for dataset in temp:
            temp_return.update({dataset.get("name") : dataset.get("data") })
        return {"datasets data" : temp_return}
