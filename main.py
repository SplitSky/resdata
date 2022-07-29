from fastapi import FastAPI
import variables as var
from pymongo.mongo_client import MongoClient
import datastructure as d
import json
import hashlib as h
import random

'''
the project parameters are stored in their own database called "config"
They are updated in the update_project_data call

project = database
experiment = collection
dataset = document 



'''

# string = "mongodb+srv://" + var.username + ":" + var.password + "@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority" # local databse for PSI
# string = "mongodb+srv://"+var.username+":"+var.password+"@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority"
string = "mongodb+srv://" + var.username + ":" + var.password + "@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient("mongodb+srv://splitsky:<password>@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority")
db = client.test

client = MongoClient(string)
# db = client["test_struct"] # defines database called test
# db = client["dev_struct"]
app = FastAPI()


### authentication functions which return whether the user is allowed or not
def check_username_exists(username):
    auth = client["Authentication"]
    users = auth["Users"]
    result = users.find_one({"username": username})
    if result is None:
        return False
    else:
        return True


# returns True or False
# hashing done using shake_256
def authenticate(username, password):
    # look up the Users database to see if the user exists.
    auth = client["Authentication"]
    users = auth["Users"]
    result = users.find_one({"username": username})
    # if it exists check if the password matches the hash
    if result is None:
        return False
    # if yes return True
    else:
        # user is found
        # validate password
        hash_result = result.get("hash")
        if hash_result == h.shake_256(password):
            return True
        else:
            return False
    # if fails at any point return False and "Failed to Authenticate" message


def return_final_hash(username, hash_init):
    auth = client["Authentication"]
    users = auth["Users"]
    result = users.find_one({"username": username})
    if result != None:
        salt = result.get("salt")
        return h.shake_256(salt + hash_init)


# functions that work
@app.get("/")
async def connection_test():  # works like main
    try:
        thing = str(client.server_info)
    except:
        thing = "failed to connect"
    return {"message": thing}


# end get

# 8. Call to return a result full dataset - "/{project_id}/{experiment_id}/{dataset_id}" - get
@app.get("/{project_id}/{experiment_id}/{dataset_id}")
async def return_dataset(project_id, experiment_id, dataset_id):
    project = client[project_id]  # database
    experiment = project[experiment_id]  # collection
    # dataset = experiment[dataset_id] # document
    temp_return = {}
    temp = experiment.find({"name": dataset_id})  # returns document
    if temp == None:
        return {"message": "no data found"}
    else:
        for dataset in temp:
            dict_struct = {
                "name": dataset.get("name"),
                "data": dataset.get("data"),
                "meta": dataset.get("meta"),
                "data_type": dataset.get("data_type")
            }
            temp_return[dataset.get("name")] = dict_struct
        return {"datasets data": temp_return}


@app.post("/{project_id}/{experiment_id}/{dataset_id}")
# 1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
async def insert_single_dataset(project_id, experiment_id, item: d.Dataset):
    project_temp = client[project_id]  # returns the project - database
    experiment_temp = project_temp[experiment_id]  # calls the experiment collection
    experiment_temp.insert_one(item.convertJSON())  # data insert into database
    return json.dumps(item.convertJSON())  # return for verification


# end def
# end post

# 5. Call to return a list of all projects "/" - get
@app.get("/names")
async def returm_all_project_names():
    return {"names": client.list_database_names()}


# end def
# end get

# 6. Call to return all experiment names for a project - "/{project_id}/" - get
@app.get("/{project_id}/names")
async def return_all_experiment_names(project_id):
    project = client[project_id]  # return collection of experiments
    names_temp = project.list_collection_names()
    return {"names": names_temp}


# 7. Call to return all dataset names for an experiment - "/{project_id}/{experiment_id}/" - get
@app.get("/{project_id}/{experiment_id}")
async def return_all_dataset_names(project_id, experiment_id):
    project = client[project_id]
    experiment = project[experiment_id]
    names_temp = []
    for dataset in experiment.find():
        names_temp.append(dataset.get("name"))
    return {"dataset names": names_temp}


@app.get("/{project_id}/{experiment_id}/details")  # returns the details without the data
async def return_experiment_details(project_id, experiment_id):
    project = client[project_id]
    experiment = project[experiment_id]
    result = experiment.find_one({"ref": "config"})  # returns json object
    if result == None:
        return {"message": "Experiment not found found. Experiment not initialised"}
    else:
        python_dict = json.loads(result)
        json_dict = {
            "name": python_dict.get("name"),
            "meta": python_dict.get("meta")
        }
        return json_dict


@app.post("/{project_id}/{experiment_id}/set_experiment")
async def update_experiment_data(project_id, experiment_id, data_in: d.simpleRequestBody):
    project = client[project_id]
    experiment = project[experiment_id]
    temp = data_in.get_variables()
    json_dict = {
        "ref": "config",  # called a ref to avoid confusion with experiment variable name
        "name": temp[0],
        "meta": temp[1]
    }
    experiment.insert_one(json_dict)
    return json_dict


@app.post("/{project_id}/set_project")
async def update_project_data(project_id, data_in: d.simpleRequestBody):
    project = client[project_id]
    collection = project["config"]  # collection containing project variables
    temp = data_in.get_variables()
    json_dict = {
        "name": temp[0],
        "meta": temp[1],
        "author": temp[2],
        "data": []
    }
    collection.insert_one(json_dict)
    return json_dict


@app.get("/{project_id}/details")
async def return_project_data(project_id):
    project = client[project_id]
    collection = project["config"]
    result = collection.find_one()  # only one document entry
    if result is None:
        return {"message": "No config found. Project not initialised"}
    else:
        python_dict = json.loads(result)
        json_dict = {
            "name": python_dict.get("name"),
            "meta": python_dict.get("meta"),
            "author": python_dict.get("author")
        }
        return json_dict


### functions managing grouping of existing datasets and experiments
'''
1. create a group using a list of names
2. remove the group
3. add a dataset to a group
4. remove a dataset from a group
5. add an experiment to a group
6. remove an experiment from  a group
'''


# 1. create a group using an object
# @app.post("{group_name}/{username}/{hash_init}/group_init")
# async def create_group(group_name, username, hash_init, group_init, group : d.Group)
# compose the group document
# experiments =
# insert


# functions managing authentication
@app.get("{username}/{hash_init}/authenticate")
async def create_user(
        user_data: d.userRequestBody):  # permission variable to be removed and added to the admin interface
    # variables
    username = user_data.get_username()
    hash_init = user_data.get_hash()
    permission = user_data.get_permission()

    # see if user already exists
    result = check_username_exists(username)
    if result:
        return {"message": "User already exists"}
    else:
        # generate salt and insert it into database
        salt_init = random.SystemRandom().getrandbits(256)
        temp = h.shake_256()
        password = str(salt_init) + hash_init

        temp.update(password.encode('utf8'))
        # open database and insert a user document
        user_json = {
            "username": username,
            "hash": temp.digest(64),  # 64 length digest of the hash
            "permission": permission
        }
        # enter the document into the database
        auth = client["Authentication"]
        users = auth["Users"]
        users.insert_one(user_json)
        return {"message": "User created"}
