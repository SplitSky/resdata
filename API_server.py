""" The API_server file containing all the API calls used by the interface. """

"""Data structure imports"""
import json
from datetime import datetime, timedelta

""" Server and client imports """
from typing import List, Union
from fastapi import FastAPI, HTTPException, status
from jose import jwt
from pymongo.errors import OperationFailure
from pymongo.mongo_client import MongoClient

"""Project imports"""
import datastructure as d
import variables as var
"""Authentication imports"""
from security import User_Auth
from variables import secret_key, algorithm, access_token_expire

"""Connect to the backend variables"""
string = f"mongodb+srv://{var.username}:{var.password}@cluster0.c5rby.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(string)
"""Initialises the API"""
app = FastAPI()


@app.get("/")
async def connection_test() -> bool:
    """Test connection to MongoDB server"""
    try:
        client.server_info()
        return True
    except OperationFailure:
        # Likely to be bad password
        return False

@app.get("/names")
async def return_all_project_names() -> dict:
    """Return a list of all project names"""
    return {"names": client.list_database_names()}

@app.post("/{project_id}/{experiment_id}/{dataset_id}/return_dataset")
async def return_dataset(project_id, experiment_id, dataset_id, user: d.User) -> Union[List[dict], dict]:
    """Return a specific fully specified dataset"""
    # Run authentication
    current_user = User_Auth(username_in=user.username, password_in=user.hash_in, db_client_in=client)
    if not current_user.authenticate_token():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The token failed to authenticate")
    # Connect to experiment
    experiment_collection = client[project_id][experiment_id]
    experiments = experiment_collection.find({"name": dataset_id})
    if experiments is None:
        return {"message": "no data found"}
    else:
        # loop over experiments, appending dataset
        return [{'name': dataset.name, 'data': dataset.data} for dataset in experiments]

@app.post("/{project_id}/{experiment_id}/insert_dataset")
async def insert_single_dataset(project_id: str, experiment_id: str, dataset_to_insert: d.Dataset) -> str:
    """Insert a dataset into the experiment listed"""
    experiments = client[project_id][experiment_id]
    dataset_credentials = dataset_to_insert.return_credentials()
    if dataset_credentials[0] != None and dataset_credentials[1] != None:
        user = User_Auth(username_in=dataset_credentials[0], password_in=dataset_credentials[1], db_client_in=client)
    # authenticate user using the security module or raise exception
    if user.authenticate_token() is False:
        return json.dumps({"message": False})
    experiments.insert_one(dataset_to_insert.convertJSON())  # data insert into database
    return json.dumps(dataset_to_insert.convertJSON())  # return for verification

@app.get("/{project_id}/names")
async def return_all_experiment_names(project_id: str) -> List[str]:
    """Retrieve all experimental names in a given project"""
    experiment_names = client[project_id].list_collection_names()
    experiment_names.remove('config')
    return experiment_names

@app.get("/{project_id}/{experiment_id}/names")
async def return_all_dataset_names(project_id: str, experiment_id: str) -> List[str]:
    return [dataset['name'] for dataset in client[project_id][experiment_id].find()
            if (dataset['data_type'] != "configuration file")]

@app.post("/{project_id}/set_project")
async def update_project_data(project_id: str, data_in: d.Simple_Request_body) -> dict:
    """Update a project with Simple Request"""
    collection = client[project_id]["config"]
    json_dict = {
        "name": data_in.name,
        "meta": data_in.meta,
        "author": data_in.author,
        "data": []
    }
    collection.insert_one(json_dict)
    return json_dict

@app.get("/{project_id}/details")
async def return_project_data(project_id: str) -> dict:
    result = client[project_id]["config"].find_one()  # only one document entry
    if result is None:
        json_dict = {"message": "No config found. Project not initialised"}
    else:
        json_dict = {
            "project_name": result.get("name"),
            "metadata": result.get("meta"),
            "author": result.get("author")
        }
    return json_dict

@app.post("/create_user")
async def create_user(user: d.User) -> dict:
    """Create a new user"""
    auth_obj = User_Auth(user.username, user.hash_in, client)
    response = False
    if user.full_name != None and user.email != None:
        response = auth_obj.add_user(user.full_name, user.email)
    if response:
        # successfully created user
        return {"message": "User Successfully created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User already exists"
        )


#########################
@app.post("{username}/validate_token")
async def validate_token(token: d.Token) -> None:
    """Check if token is not expired and if user exists"""
    payload = jwt.decode(token.access_token, secret_key, algorithms=[algorithm])
    if payload.get("sub") is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is invalid")
    else:
        username = payload.get("sub")

    # Establish user
    if username != None:
        user = User_Auth(username, "None", client)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "request body missing username"
        )
    # Check if exists
    if user.check_username_exists():
        result = client["Authentication"]["Users"].find_one({"username": username})
        if result is not None:
            token_in_db = result.get("token")
            if token_in_db == token.access_token:
                expiry = datetime.fromisoformat(result.get("expiry"))
                # Check for expiry
                if datetime.utcnow() <= expiry:
                    raise HTTPException(status_code=status.HTTP_200_OK, detail="User authenticated")
                else:
                    # deactivate the user
                    user.deactivate_user()
    # Fallback
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User doesn't exist",
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.post("/generate_token", response_model=d.Token)
async def login_for_access_token(credentials: d.User) -> d.Token:
    """Create a token and enable user"""
    user = User_Auth(credentials.username, credentials.hash_in, client)
    if user.check_username_exists():
        if user.check_password_valid():
            # authentication complete
            access_token_expires = timedelta(minutes=access_token_expire)
            temp_token = user.create_access_token(
                expires_delta=access_token_expires)
            # create_access_token activates user and sets expiry date in database
            return d.Token(access_token=temp_token, token_type="bearer")
    # token fails authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The credentials failed to validate"
    )
