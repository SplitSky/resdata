from fastapi import FastAPI
import hashlib as hash
import variables as var
from pymongo.mongo_client import MongoClient
import datastructure as d
import json

'''
the project parameters are stored in their own database called "config"
They are updated in the update_project_data call
'''

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

# 8. Call to return a result full dataset - "/{project_id}/{experiment_id}/{dataset_id}" - get
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
    return json.dumps(item.convertJSON())
# end def
# end post

# 5. Call to return a list of all projects "/" - get
@app.get("/")
async def returm_all_project_names():
    return {"project names" : db.list_collection_names()}
# end def
# end get

# 6. Call to return all experiment names for a project - "/{project_id}/" - get
@app.get("/{project_id}")
async def return_all_experiment_names(project_id):
    project = db[project_id] # return collection of experiments
    names_temp = []
    for experiment in project.find():
        names_temp.append(experiment.get("name"))
    return {"names" : names_temp}

# 7. Call to return all dataset names for an experiment - "/{project_id}/{experiment_id}/" - get
@app.get("/{project_id}/{experiment_id}")
async def return_all_dataset_names(project_id, experiment_id):
    project = db[project_id]
    experiment = project[experiment_id]
    names_temp = []
    for dataset in experiment.find():
        names_temp.append(dataset.get("name"))
    return {"dataset names" : names_temp}

@app.get("/{project_id}/{experiment_id}/details") # returns the details without the data
async def return_experiment_details(project_id, experiment_id):
    project = db[project_id]
    result = project.find_one({"name" : experiment_id}) # returns json object
    if result == None:
        return {"message" : "Experiment not found found"}
    else:
        python_dict = json.loads(result)
        json_dict = {
            "name" : python_dict.get("name"),
            "meta" : python_dict.get("meta")
        }
        return json_dict

@app.post("/{project_id}/set_project")
async def update_project_data(project_id, data_in : d.Simple_Request_body):
    project = db[project_id]
    temp = data_in.get_variables()
    json_dict = {
        "name" : temp[0],
        "meta" : temp[1],
        "author" : temp[2]
    }
    project.insert_one({"config" : json_dict})
    return json_dict


@app.get("/{project_id}/details")
async def return_project_data(project_id):
    project = db[project_id]
    result = project.find_one("config")
    if result == None:
        return {"message" : "No config found"}
    else:
        python_dict = json.loads(result)
        json_dict = {
            "name" : python_dict.get("name"),
            "meta" : python_dict.get("meta"),
            "author" : python_dict.get("author")
        }
        return json_dict
