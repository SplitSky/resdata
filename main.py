# Datastructure imports
import json
from datetime import datetime, timezone, timedelta

# Server and client imports
from fastapi import FastAPI, HTTPException, status
from jose import jwt
from pymongo.mongo_client import MongoClient

# Project imports
import datastructure as d
import variables as var
# authentication imports
from security import User_Auth, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM

#########################
# Connect to the backend
string = f"mongodb+srv://{var.username}:{var.password}@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(string)
# Initialize API
app = FastAPI()


#########################

# functions that work
@app.get("/")
async def connection_test():  # works like main
    try:
        client.server_info()
        return True
    except BaseException as E:
        return False


# end get

# 8. Call to return a result full dataset - "/{project_id}/{experiment_id}/{dataset_id}" - get
@app.post("/{project_id}/{experiment_id}/{dataset_id}/return_dataset")
async def return_dataset(project_id, experiment_id, dataset_id, user : d.User):

    # authenticate
    user_temp = User_Auth(username_in=user.username,password_in=user.hash_in, db_client_in=client)
    if user_temp.authenticate_token() == False:
        #return json.dumps({"message" : False})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The token failed to authenticate"
        )



    project = client[project_id]  # database
    experiment = project[experiment_id]  # collection
    # dataset = experiment[dataset_id] # document
    temp_return = []
    temp = experiment.find({"name": dataset_id})  # returns document
    if temp is None:
        return {"message": "no data found"}
    else:
        for dataset in temp:
            dict_struct = {
                "name": dataset.get("name"),
                "data": dataset.get("data"),
                "meta": dataset.get("meta"),
                "data_type" : dataset.get("data_type"),
                "author" : dataset.get("author")
            }
            temp_return.append(dict_struct)
        return {"datasets data": temp_return}


@app.post("/{project_id}/{experiment_id}/{dataset_id}/insert_dataset")
# 1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
async def insert_single_dataset(project_id, experiment_id, item: d.Dataset):
    project_temp = client[project_id]  # returns the project - database
    experiment_temp = project_temp[experiment_id]  # calls the experiment collection
    temp = item.return_credentials()
    user = User_Auth(username_in=temp[0], password_in=temp[1], db_client_in=client)
    # authenticate user using the security module or raise exception
    print("Authenticate_token : ")
    print(user.authenticate_token())
    if user.authenticate_token() == False:
        return json.dumps({"message" : False})
       # raise HTTPException(
       #     status_code=status.HTTP_401_UNAUTHORIZED,
       #     detail="The token failed to authenticate"
       # )
    print("Data inserted into database")
    print(item.convertJSON())
    experiment_temp.insert_one(item.convertJSON())  # data insert into database
    return json.dumps(item.convertJSON())  # return for verification


# end def
# end post

# 5. Call to return a list of all projects "/" - get
@app.get("/names")
async def return_all_project_names():
    return {"names": client.list_database_names()}


# end def
# end get

# 6. Call to return all experiment names for a project - "/{project_id}/" - get
@app.get("/{project_id}/names")
async def return_all_experiment_names(project_id):
    project = client[project_id]  # return collection of experiments
    names_temp = project.list_collection_names()
    names_temp.remove("config")  # removes the config entry from the experiments list

    return {"names": names_temp}


# 7. Call to return all dataset names for an experiment - "/{project_id}/{experiment_id}/" - get
@app.get("/{project_id}/{experiment_id}/names")
async def return_all_dataset_names(project_id, experiment_id):
    project = client[project_id]
    experiment = project[experiment_id]
    names_temp = []
    for dataset in experiment.find():
        names_temp.append(dataset.get("name"))
    return {"names": names_temp}


@app.get("/{project_id}/{experiment_id}/details")  # returns the details without the data -> this function is not used
async def return_experiment_details(project_id, experiment_id):
    project = client[project_id]
    experiment = project[experiment_id]
    result = experiment.find_one({"data_type": "configuration file"})  # returns json object
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment was not initialised"
        )
    else:
        python_dict = json.loads(result)
        json_dict = {
            "name": python_dict.get("name"),
            "meta": python_dict.get("meta")
        }
        return json.dumps(json_dict)


@app.post(
    "/{project_id}/{experiment_id}/set_experiment")  # this function is redundant and can be replaced with insert
# dataset
async def update_experiment_data(project_id, experiment_id, data_in: d.Dataset):
    project = client[project_id]
    print("The experiment update function is running")
    experiment = project[experiment_id]
    experiment.insert_one(data_in.convertJSON())
    return data_in.convertJSON()


@app.post("/{project_id}/set_project")
async def update_project_data(project_id, data_in: d.Simple_Request_body):
    project = client[project_id]
    collection = project["config"]  # collection containing project variables
    json_dict = {
        "name": data_in.name,
        "meta": data_in.meta,
        "author": data_in.author,
        "data": []
    }
    collection.insert_one(json_dict)
    return json.dumps(json_dict)


@app.get("/{project_id}/details")
async def return_project_data(project_id):
    project = client[project_id]
    collection = project["config"]
    result = collection.find_one()  # only one document entry
    if result is None:
        return {"message": "No config found. Project not initialised"}
    else:
        json_dict = {
            "name": result.get("name"),
            "meta": result.get("meta"),
            "author": result.get("author")
        }
        return json.dumps(json_dict)


# authentication

# API call creating a user using User_Auth class
@app.post("/create_user")
async def create_user(user: d.User):
    auth_obj = User_Auth(user.username, user.hash_in, client)
    response = auth_obj.add_user(user.full_name, user.email)
    if response:
        # successfully created user
        return {"message": "User Successfully created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User already exists"
        )


# API call for validating a user token
@app.post("{username}/validate_token")
async def validate_token(token: d.Token):
    # check if token is not expired and if user exists
    payload = jwt.decode(token.access_token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid"
        )
    else:
        username = payload.get("sub")
    user = User_Auth(username, "None", client)
    if user.check_username_exists():
        # access database and validate the token by looking up username
        auth = client["Authentication"]
        users = auth["Users"]

        result = users.find_one({"username": username})
        # see if user exists
        if result is not None:
            token_in_db = result.get("token")  # returns the hashed password from database
            # hashes the password in and compares
            if token_in_db == token.access_token:
                # the user has the matching token
                # get the expiry time from database
                expiry = datetime.fromisoformat(result.get("expiry"))  # converts string to date
                if datetime.utcnow() <= expiry: # check if token is not expired
                    print("user authenticated")
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="User authenticated",
                    )
                else:
                    # deactivate the user
                    user.deactive_user()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User doesn't exist",
        headers={"WWW-Authenticate": "Bearer"}
    )


# API call generating the token -> returns a token
@app.post("/generate_token", response_model=d.Token)
async def login_for_access_token(credentials: d.User):
    user = User_Auth(credentials.username, credentials.hash_in, client)
    if user.check_username_exists():
        if user.check_password_valid():
            # authentication complete
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            temp_token = user.create_access_token(
                                                  expires_delta=access_token_expires)
            # create_access_token activates user and sets expiry date in database
            return d.Token(access_token=temp_token, token_type="bearer")
    # token fails authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The credentials failed to validate"
    )

# TODO: remove this function for deployment
@app.post("/testing_stuff")
async def insert_single_dataset_test(item: d.Dataset):
    temp = item.return_credentials()
    user = User_Auth(username_in=temp[0],password_in=temp[1], db_client_in=client)
    # authenticate user using the security module or raise exception
    if user.authenticate_token() == False:
        return json.dumps({"message" : False})
       # raise HTTPException(
       #     status_code=status.HTTP_401_UNAUTHORIZED,
       #     detail="The token failed to authenticate"
       # )
    print("Data inserted into database")
    print(item.convertJSON())
    return json.dumps({"message" : True}) # return for v
