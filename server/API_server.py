""" The API_server file containing all the API calls used by the interface. """
"""Data structure imports"""
import json
from datetime import datetime, timedelta
from time import sleep
""" Server and client imports """
from typing import List, Dict
from fastapi import FastAPI, HTTPException, status
from jose import jwt
from pymongo.errors import OperationFailure
from pymongo.mongo_client import MongoClient

"""Project imports"""
import datastructure as d
import variables as var

"""Authentication imports"""
from security import User_Auth
from variables import secret_key, algorithm, access_token_expire, API_key
import hashlib as h

# testing string
string = f"mongodb+srv://splitsky:{var.password}@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority"
# virtual machine string
#string = f"mongodb://splitsky:{var.password}@127.0.0.1/?retryWrites=true&w=majority"
client = MongoClient(string)
"""Initialises the API"""
app = FastAPI()

def return_hash(password: str):
    """ Hash function used by the API to decode. It is used to only send hashes and not plain passwords."""
    temp = h.shake_256()
    temp.update(password.encode('utf8'))
    return temp.hexdigest(64)


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
async def return_all_project_names(author: d.Author):
    """ Function which returns a list of project names that the user has permission to view."""
    # validate user
    # check if user was authenticated in and has a valid token
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user hasn't authenticated"
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

    return {"names": names_out}


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
            "name": result.get("name"),
            "data": result.get("data"),
            "meta": result.get("meta"),
            "data_type": result.get("data_type"),
            "author": result.get("author"),
            "data_headings": result.get("data_headings")
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
async def return_all_experiment_names(project_id: str, user: d.Author) -> Dict[str, List[str]]:
    """Retrieve all experimental names in a given project that the user has the permission to access"""
    experiment_names = client[project_id].list_collection_names()
    user_temp = User_Auth(username_in=user.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    ### permission filtering
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user hasn't authenticated"
        )
    exp_names_out = []
    if len(experiment_names) != 0:
        experiment_names.remove('config')
        # filtering based on permission
        for name in experiment_names:
            # get the authors and loop over them
            experiment = client[project_id][name]  # access the experiment config file
            result = experiment.find_one({"name": name})
            if result != None:
                author_list = result.get("author")
                for author in author_list:
                    if author.get("name") == user.name:
                        exp_names_out.append(name)
    return {"names": exp_names_out}


@app.get("/{project_id}/{experiment_id}/names")
async def return_all_dataset_names(project_id: str, experiment_id: str, author: d.Author):
    """ Retrieve all dataset names that the user has access to."""
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user hasn't authenticated"
        )

    names = []
    result = client[project_id][experiment_id].find()
    if result == None:
        # the dataset path isn't initialised
        return {"names": []}
    for dataset in result:
        for entry in dataset['author']:
            if entry['name'] == author.name:
                names.append(dataset['name'])  # returns all datasets including the config
    return {"names": names}


@app.post("/{project_id}/set_project")
async def update_project_data(project_id: str, data_in: d.Simple_Request_body):  # -> Dict:
    """Update a project with Simple Request"""
    collection = client[project_id]['config']
    json_dict = {
        "name": data_in.name,
        "meta": data_in.meta,
        "author": data_in.author,
        "data": [],
        "creator": data_in.creator
    }
    collection.insert_one(json_dict)
    # return json_dict


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


@app.post("/create_user/{ui_public_key}")
async def create_user(user: d.User, ui_public_key) -> Dict:
    """Create a new user"""
    sleep(1)
    auth_obj = User_Auth(user.username, user.hash_in, client)
    # passes initial string key authentication
    auth_obj.read_keys()
    temp_key = user.tunnel_key
    if type(temp_key) != None:
        if not return_hash(API_key) == temp_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="You are not using the appropriate interface.")
    private_key, public_key = auth_obj.read_keys()
    list_temp = [user.username, user.hash_in, user.full_name, user.email]
    temp = []
    for message in list_temp:
        temp.append(auth_obj.decrypt_message(message=message, private_key=private_key))
    username = auth_obj.decrypt_message(private_key=private_key, message=user.username)
    # create the user
    username = temp[0]
    hash_in = temp[1]
    full_name = temp[2]
    email = temp[3]
    response = False
    if full_name != None and email != None:
        # reassign username and hash for the decrypted versions
        auth_obj.username = username
        auth_obj.password = hash_in
        response = auth_obj.add_user(full_name, email)
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
            detail="request body missing username"
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


@app.post("/{project_id}/{experiment_id}/{dataset_id}/{username}/add_author")
async def add_author_to_dataset(project_id: str, experiment_id: str, dataset_id: str, author: d.Author, username: str):
    """API call for adding an author to the dataset or updating the permissions"""
    # autheticate user
    user_temp = User_Auth(username_in=username, password_in="", db_client_in=client)
    user_temp.update_disable_status()  # authenticate the user adding the author
    user_doc = user_temp.fetch_user()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The user has not authenticated"
    )

    if user_doc.get("disabled") == True:
        raise credentials_exception

        # fetch the author list
    result = client[project_id][experiment_id].find_one({"name": dataset_id})
    if result == None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                            detail="The dataset doesn't exist")
    author_list = result.get("author")
    # see if the author already exists. Raise exception if it does
    for entry in author_list:
        if author.name == entry.get("name"):
            if author.permission == entry.get("permission"):
                # permissions are also the same
                raise HTTPException(status_code=status.HTTP_302_FOUND,
                                    detail="The author already exists.")
            else:
                # update just permissions

                entry['permission'] = author.permission  # override the permissions
                # update database
                client[project_id][experiment_id].find_one_and_update({"name": dataset_id},
                                                                      {'$set': {"author": author_list}})
                return status.HTTP_200_OK  # terminate successfully

    # author doesn't exist. Append the author
    author_list.append(author.dict())
    client[project_id][experiment_id].find_one_and_update({"name": dataset_id}, {'$set': {"author": author_list}})
    return status.HTTP_200_OK


@app.get("/{project_id}/{experiment_id}/meta_search")
async def meta_search(project_id: str, experiment_id: str, search_variables: d.Dataset):
    """Querying experiment and returning the names of the datasets that fit the meta data variables"""

    # search_variables.data is a list of dictionaries ex. {"variable_name" : variable value}
    dataset_credentials = search_variables.return_credentials()
    if dataset_credentials[0] != None and dataset_credentials[1] != None:
        user = User_Auth(username_in=dataset_credentials[0], password_in=dataset_credentials[1], db_client_in=client)
        # authenticate user using the security module or raise exception
        if user.authenticate_token() is False:
            return json.dumps({"message": False})
        if search_variables.meta == None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing meta data in search")
        # authenticated
        names = []
        for dataset in client[project_id][experiment_id].find():
            # dataset is a dictionary
            found = True
            for key_meta, value_meta in search_variables.meta.items():
                # dataset.meta[search_meta] - look up of the meta dictionary
                if dataset.get("meta") == None:
                    found = False  # the dataset doesn't have a defined meta variable
                else:
                    if dataset.get("meta").get(
                            key_meta) == None:  # database doesn't have the mete variable with the given name
                        found = False  # return false
                    else:
                        if dataset.get("meta").get(key_meta) != value_meta:
                            found = False
            # end of for loop
            if found == True:
                names.append(dataset.get("name"))  # appends names to a list
        return {"names": names}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Lacking authentication variables")


@app.post("/{project_id}/{experiment_id}/{dataset_id}/{group_name}/add_group_author")
async def add_group_to_dataset(project_id: str, experiment_id: str, dataset_id: str, group_name: str, author: d.Author):
    """API call for adding an author to the dataset or updating the permissions"""
    # autheticate user
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The user has not authenticated"
    )
    if user_doc.get("disabled") == True:
        raise credentials_exception
        # fetch the author list
    result = client[project_id][experiment_id].find_one({"name": dataset_id})
    if result == None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                            detail="The dataset doesn't exist")
    author_list = result.get("author")
    # author_list_new = author_list
    # see if the author already exists. Raise exception if it does
    for entry in author_list:
        if author.name == entry.get("name"):
            if entry.get("permission") == "write":
                # verifies the user has write access to assign group
                group = d.Author(name=group_name, permission=author.permission)
                author_list.append(group.dict())
                client[project_id][experiment_id].find_one_and_update({"name": dataset_id},
                                                                      {'$set': {"author": author_list}})
                return True  # terminate successfully
    # author doesn't exist. Raise exception as not allowed to append to group if the user doesn't have access to the dataset
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="The author doesn't have permission to add group to this dataset")
    # return False


# names function for groups
@app.get("/names_group")  # projects
async def return_all_project_names_group(author: d.Author):
    """ Function which returns a list of project names that the user has permission to view."""
    # validate user
    # check if user was authenticated in and has a valid token
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()

    if author.group_name == None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Missing the group name search parameter")

    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user hasn't authenticated"
        )
    names = client.list_database_names()
    names_out = []
    # remove the not data databases
    names.remove('Authentication')
    names.remove('admin')
    names.remove('local')
    for name in names:
        # fetch database config file
        temp_project = client[name]
        config = temp_project["config"]
        result = config.find_one()
        # there is always only one dataset here
        if result == None:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="The project wasn't initialised properly")
        authors = result.get("author")  # fetches the author dictionary

        for item in authors:  # loop over authors
            if item.get("name") == author.group_name:
                names_out.append(name)
    return {"names": names_out}


@app.get("/{project_id}/names_group")
async def return_all_experiment_names_group(project_id: str, user: d.Author) -> Dict[str, List[str]]:
    """Retrieve all experimental names in a given project that the user has the permission to access"""
    experiment_names = client[project_id].list_collection_names()
    user_temp = User_Auth(username_in=user.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    ### permission filtering
    if user.group_name == None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Missing the group name search parameter")
    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user hasn't authenticated"
        )
    exp_names_out = []
    if len(experiment_names) != 0:
        experiment_names.remove('config')
        # filtering based on permission
        for name in experiment_names:
            # get the authors and loop over them
            experiment = client[project_id][name]  # access the experiment config file
            result = experiment.find_one({"name": name})
            if result != None:
                author_list = result.get("author")
                for author in author_list:
                    if author.get("name") == user.group_name:
                        exp_names_out.append(name)
    return {"names": exp_names_out}


@app.get("/{project_id}/{experiment_id}/names_group")  # datasets
async def return_all_dataset_names_group(project_id: str, experiment_id: str, author: d.Author):
    """ Retrieve all dataset names that the user has access to."""
    user_temp = User_Auth(username_in=author.name, password_in="", db_client_in=client)
    user_temp.update_disable_status()
    user_doc = user_temp.fetch_user()
    if author.group_name == None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Missing the group name search parameter")

    if user_doc.get("disabled") == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user hasn't authenticated"
        )
    names = []
    for dataset in client[project_id][experiment_id].find():
        # see if user is an author
        # TODO: verify this works
        for entry in dataset['author']:
            if entry['name'] == author.group_name:
                names.append(dataset['name'])  # returns all datasets including the config
    return {"names": names}


##### End group API calls


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
        client.drop_database(db_name)  # purge all documents in collection


@app.post("/get_public_key")
async def return_public_key():
    """Fetch the public key for encryption from the API"""
    sleep(1)
    u = User_Auth(username_in="", password_in="", db_client_in=client)
    # generate public and private keys
    private_key, public_key = u.generate_keys()
    u.save_keys(private_key=private_key, public_key=public_key)
    priv_bytes, pub_bytes = u.convert_keys_for_storage(private_key, public_key)
    return {"public_key": pub_bytes}


@app.post("/{project_name}/{experiment_name}/{dataset_name}/collect_fragments_names")
async def collect_fragments(project_name: str, experiment_name: str, dataset_name: str, user: d.User):
    """Collect the dataset parts of a fragmented dataset and return their names"""
    # authenticate user
    current_user = User_Auth(username_in=user.username, password_in=user.hash_in, db_client_in=client)
    if not current_user.authenticate_token():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The token failed to authenticate")
    # authenticate the user access to the dataset
    if not current_user.check_author(project_id=project_name, experiment_id=experiment_name, dataset_id=dataset_name):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You don't have access to the dataset")
    names = []
    search_variables = {"parent_dataset": dataset_name}
    for dataset in client[project_name][experiment_name].find():
        # dataset is a dictionary
        found = True
        for key_meta, value_meta in search_variables.items():
            # dataset.meta[search_meta] - look up of the meta dictionary
            if dataset.get("meta").get(key_meta) == None:  # database doesn't have the mete variable with the given name
                found = False  # return false
            else:
                if dataset.get("meta").get(key_meta) != value_meta:
                    found = False
        # end of for loop
        if found == True:
            names.append(dataset.get("name"))  # appends names to a list
    return {"names": names}
