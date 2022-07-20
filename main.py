from fastapi import FastAPI
from pydantic import BaseModel
import hashlib as hash
import variables as var
from pymongo.mongo_client import MongoClient
import json
import datastructure as d

string = "mongodb+srv://" + var.username + ":" + var.password + "@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(string)
db = client["test_struct"] # defines database called test 
app = FastAPI()

# functions that work
@app.get("/")
async def connection_test(): # works like main
    try:
        thing = str(client.server_info)
    except:
        thing = "failed to connect"
    return {"message" : thing}
# end get

# 8. Call to return a result of the query of a dataset - "/{project_id}/{experiment_id}/{dataset_id}" - get
@app.get("/{project_id}/{experiment_id}/{dataset_id}")
async def return_queried_data(project_id, experiment_id, dataset_id):
    project = db[project_id]
    experiment = project[experiment_id]
    dataset = experiment[dataset_id]
    temp_return = {}
    temp = dataset.find() 
    if temp == None:
        return {"message" : "no data found"}
    else:
        for dataset in temp:
            dict_struct = {
                "name": dataset.get("name"),
                "data" : dataset.get("data"),
                "meta" : dataset.get("meta"),
                "data_type" : dataset.get("data_type")
            }
            temp_return[dataset.get("name")] = dict_struct
        return {"datasets data" : temp_return}

@app.post("/{project_id}/{experiment_id}/{dataset_id}")
# 1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
async def insert_single_dataset(project_id, experiment_id, dataset_id, item: d.Dataset):
    project_temp = db[project_id] # returns the project
    experiment_temp = project_temp[experiment_id] # returns the experiment or creates if doesn't exist
    dataset_temp = experiment_temp[dataset_id] # returns the dataset 
    # data insert here
    # each experiment has multiple data sets. Each is nested in the experiment collection
    # end of data insert
    dataset_temp.insert_one(item.convertJSON()) # data insert into database
    return item # returns the request body to the API for verification
# end def
# end post

# 5. Call to return a list of all projects "/" - get
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
