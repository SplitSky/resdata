from fastapi import FastAPI, HTTPException, status
import hashlib as hash
import variables as var
from pymongo.mongo_client import MongoClient
import datastructure as d
import json

'''
the project parameters are stored in their own database called "config"
They are updated in the update_project_data call
project = database
experiment = collection
dataset = document 
'''

#string = "mongodb+srv://" + var.username + ":" + var.password + "@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority" # local databse for PSI
#string = "mongodb+srv://"+var.username+":"+var.password+"@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority"
string = "mongodb+srv://"+var.username+":"+var.password+"@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient("mongodb+srv://splitsky:<password>@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority")
db = client.test



client = MongoClient(string)
#db = client["test_struct"] # defines database called test 
#db = client["dev_struct"]
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
@app.get("/{project_id}/{experiment_id}/{dataset_id}/return_dataset")
async def return_dataset(project_id, experiment_id, dataset_id):
    project = client[project_id] # database
    experiment = project[experiment_id] # collection
    #dataset = experiment[dataset_id] # document
    temp_return = []
    temp = experiment.find({"name" : dataset_id}) # returns document 
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
            temp_return.append(dict_struct)
        return {"datasets data" : temp_return}

@app.post("/{project_id}/{experiment_id}/{dataset_id}/insert_dataset")

# 1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
async def insert_single_dataset(project_id, experiment_id, item: d.Dataset):
    project_temp = client[project_id] # returns the project - database
    experiment_temp = project_temp[experiment_id] # calls the experiment collection 
    experiment_temp.insert_one(item.convertJSON()) # data insert into database
    return json.dumps(item.convertJSON()) # return for verification
# end def
# end post

# 5. Call to return a list of all projects "/" - get
@app.get("/names")
async def returm_all_project_names():
    return {"names" : client.list_database_names()}
# end def
# end get

# 6. Call to return all experiment names for a project - "/{project_id}/" - get
@app.get("/{project_id}/names")
async def return_all_experiment_names(project_id):
    project = client[project_id] # return collection of experiments
    names_temp = project.list_collection_names()
    names_temp.remove("config") # removes the config entry from the experiments list

    return {"names" : names_temp}

# 7. Call to return all dataset names for an experiment - "/{project_id}/{experiment_id}/" - get
@app.get("/{project_id}/{experiment_id}/names")
async def return_all_dataset_names(project_id, experiment_id):
    project = client[project_id]
    experiment = project[experiment_id]
    names_temp = []
    for dataset in experiment.find():
        names_temp.append(dataset.get("name"))
    return {"names" : names_temp}

@app.get("/{project_id}/{experiment_id}/details") # returns the details without the data -> this function is not used
async def return_experiment_details(project_id, experiment_id):
    project = client[project_id]
    experiment = project[experiment_id]
    result = experiment.find_one({"data_type" : "configuration file"}) # returns json object
    if result == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment was not initialised"
        )
    else:
        python_dict = json.loads(result)
        json_dict = {
            "name" : python_dict.get("name"),
            "meta" : python_dict.get("meta")
        }
        return json.dumps(json_dict)

@app.post("/{project_id}/{experiment_id}/set_experiment") # this function is redundant and can be replaced with insert dataset
async def update_experiment_data(project_id, experiment_id, data_in : d.Dataset):
    project = client[project_id]
    print("The experiment update function is running")
    experiment = project[experiment_id]
   # json_dict = {
   #     "ref" : "config", # called a ref to avoid confusion with experiment variable name
   #     "name" : data_in.name,
   #     "meta" : data_in.meta,
   #     "data type" : "configuration data"
   # }
   # experiment.insert_one(json_dict)
   # return json_dict
    experiment.insert_one(data_in.convertJSON())
    return data_in.convertJSON()

@app.post("/{project_id}/set_project")
async def update_project_data(project_id, data_in : d.Simple_Request_body):
    project = client[project_id]
    collection = project["config"] # collection containing project variables
    json_dict = {
        "name" : data_in.name,
        "meta" : data_in.meta,
        "author" : data_in.author,
        "data" : []
    }
    collection.insert_one(json_dict)
    return json.dumps(json_dict)

@app.get("/{project_id}/details")
async def return_project_data(project_id):
    project = client[project_id]
    collection = project["config"]
    result = collection.find_one() # only one document entry
    if result == None:
        return {"message" : "No config found. Project not initialised"}
    else:
        json_dict = {
            "name" : result.get("name"),
            "meta" : result.get("meta"),
            "author" : result.get("author")
        }
        return json.dumps(json_dict)
