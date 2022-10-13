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
from variables import secret_key, algorithm, access_token_expire, cluster_id

"""Connect to the backend variables"""
string = f"mongodb+srv://{var.username}:{var.password}@cluster0.{cluster_id}.mongodb.net/?retryWrites=true&w=majority"
# string = mongodb+srv://<username>:<password>@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority
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
async def returm_all_project_names(author : d.Author):
    """ Function which returns a list of project names that the user has permission to view."""
    # validate user
    # check if user was authenticated in and has a valid token
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "The user hasn't authenticated"
        )

    names = client.list_database_names()
    names_out = []
    # 'Authentication', 'S_Church', 'admin', 'local'
    # remove the not data databases
    names.remove('Authentication')
    names.remove('admin')
    names.remove('local')
    for name in names:
        # fetch database config file
        temp_project = client[name]
        config = temp_project["config"]
        result = config.find_one()
        if result == None:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="The project wasn't initialised properly"
            )
        authors = result.get("author")
        for item in authors:
            # item is a dictionary
            if item.get("name") == author.name:
                names_out.append(name)
    
    return {"names" : names_out}

@app.post("/{project_id}/{experiment_id}/{dataset_id}/return_dataset")
async def return_dataset(project_id, experiment_id, dataset_id, user: d.User) -> str:
    """Return a single fully specified dataset"""
    # Run authentication
    current_user = User_Auth(username_in=user.username, password_in=user.hash_in, db_client_in=client)
    if not current_user.authenticate_token():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The token failed to authenticate")
    # Connect to experiment
    experiment_collection = client[project_id][experiment_id]
    result = experiment_collection.find_one({"name": dataset_id})
    if result is None:
        return json.dumps({"message": False})
    else:
        dict_struct = {
            "name" : result.get("name"),
            "data" : result.get("data"),
            "meta" : result.get("meta"),
            "data_type" : result.get("data_type"),
            "author" : result.get("author"),
            "data_headings" : result.get("data_headings")
        }
        temp = json.dumps(dict_struct)
        return temp

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
async def return_all_experiment_names(project_id: str, user : d.Author) -> dict[str,List[str]]:
    """Retrieve all experimental names in a given project that the user has the permission to access"""
    experiment_names = client[project_id].list_collection_names()
    user_temp = User_Auth(username_in=user.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    ### permission filtering
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "The user hasn't authenticated"
        )
    exp_names_out = []
    if len(experiment_names) != 0:
        experiment_names.remove('config')
        # filtering based on permission
        for name in experiment_names:
            # get the authors and loop over them
            experiment = client[project_id][name] # access the experiment config file
            result = experiment.find_one({"name" : name})
            if result != None:
                author_list = result.get("author")
                for author in author_list:
                    if author.get("name") == user.name:
                        exp_names_out.append(name)
    return {"names" : exp_names_out}

@app.get("/{project_id}/{experiment_id}/names")
async def return_all_dataset_names(project_id: str, experiment_id: str, author : d.Author):
    """ Retrieve all dataset names that the user has access to."""
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "The user hasn't authenticated"
        )
    
    names = []
    for dataset in client[project_id][experiment_id].find():
        # see if user is an author
        # TODO: verify this works
        for entry in dataset['author']:
            if entry['name'] == author.name:
                names.append(dataset['name']) # returns all datasets including the config
    return {"names" : names}

@app.post("/{project_id}/set_project")
async def update_project_data(project_id: str, data_in: d.Simple_Request_body): #-> dict:
    """Update a project with Simple Request"""
    collection = client[project_id]['config']
    json_dict = {
        "name": data_in.name,
        "meta": data_in.meta,
        "author": data_in.author,
        "data": [],
        "creator" : data_in.creator
    }
    collection.insert_one(json_dict)
    #return json_dict

@app.get("/{project_id}/details")
async def return_project_data(project_id: str) -> str:
    """Returns the project variables from the config collection within the project_id database. """
    result = client[project_id]["config"].find_one()  # only one document entry
    if result is None:
        json_dict = {"message": "No config found. Project not initialised"}
    else:
        json_dict = {
            "name": result.get("name"),
            "meta": result.get("meta"),
            "author": result.get("author"),
            "creator": result.get("creator")
        }
    return json.dumps(json_dict)

@app.post("/create_user")
async def create_user(user: d.User) -> dict:
    # TODO: don't allow duplicate usernames -> not implemented
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

@app.post("/{project_id}/{experiment_id}/{dataset_id}/add_author")
async def add_author_to_dataset(project_id : str, experiment_id : str, dataset_id : str,author : d.Author):
    """API call for adding an author to the dataset or updating the permissions"""
    # autheticate user
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    credentials_exception = HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "The user has not authenticated"
    )

    if user_doc.get("disabled") == True:
        raise credentials_exception 

    # fetch the author list
    result = client[project_id][experiment_id].find_one({"name" : dataset_id})
    if result == None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                            detail= "The dataset doesn't exist")
    author_list = result.get("author") 
    #author_list_new = author_list
    # see if the author already exists. Raise exception if it does
    for entry in author_list:
        if author.name == entry.get("name"):
            if author.permission == entry.get("permission"):
                # permissions are also the same
                raise HTTPException(status_code=status.HTTP_302_FOUND,
                                    detail="The author already exists.")
            else:
                # update just permissions

                entry['permission'] = author.permission # override the permissions
                # update database
                client[project_id][experiment_id].find_one_and_update({"name" : dataset_id},{'$set' : {"author" : author_list}})
                return status.HTTP_200_OK # terminate successfully
    
    # author doesn't exist. Append the author
    author_list.append(author.dict())
    client[project_id][experiment_id].find_one_and_update({"name" : dataset_id},{'$set' : {"author" : author_list}})
    return status.HTTP_200_OK

#@app.post("/{project_id}/add_author")
#async def add_author_to_project(project_id, author : d.Author):
#    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
#    user_temp.update_disable_status()
#    user_doc = user_temp.fetch_user()
#    credentials_exception = HTTPException(
#            status_code= status.HTTP_401_UNAUTHORIZED,
#            detail= "The user has not authenticated"
#    )
#
#    if user_doc.get("disabled") == True:
#        raise credentials_exception
#    # fetch the author list
#    result = client[project_id]['config'].find_one({"name" : project_id})
#    if result == None:
#        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
#                            detail= "The dataset doesn't exist")
#    author_list = result.get("author")

@app.post("/purge")
async def purge_function():
    # testing function to be removed after
    """Clears the database. Requires admin priviledge for user. Testing function. Remove for deployment """
    # return the names of all collections
    names = client.list_database_names()
    # remove the not data databases
    names.remove('admin')
    names.remove('local') 
    for db_name in names:
        client.drop_database(db_name) # purge all documents in collection
