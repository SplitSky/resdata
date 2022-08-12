from fastapi import FastAPI, HTTPException, status
import hashlib as hash
import variables as var
from pymongo.mongo_client import MongoClient
import datastructure as d
import json

# authentication imports
from security import User_Auth, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from fastapi.security import HTTPBasicCredentials
from datetime import datetime, timezone, timedelta
# define permanent variables
ACCESS_TOKEN_EXPIRE_MINUTES = var.access_token_expire
SECRET_KEY = var.secret_key
ALGORITHM = var.algorithm



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

#client = MongoClient("mongodb+srv://splitsky:<password>@cluster0.xfvstgi.mongodb.net/?retryWrites=true&w=majority")
#db = client.test



client = MongoClient(string)
#db = client["test_struct"] # defines database called test 
#db = client["dev_struct"]
app = FastAPI()

# functions that work
@app.get("/")
async def connection_test(): # works like main
    try:
        client.server_info
        return True
    except:
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
                "data_type" : dataset.get("data_type"),
                "author" : dataset.get("author")
            }
            temp_return.append(dict_struct)
        return {"datasets data" : temp_return}

@app.post("/{project_id}/{experiment_id}/{dataset_id}/insert_dataset")

# 1. Call to insert a single dataset "/{project_id}/{experiment_id}/{dataset_id}" - post
async def insert_single_dataset(project_id, experiment_id, item: d.Dataset):
    project_temp = client[project_id] # returns the project - database
    experiment_temp = project_temp[experiment_id] # calls the experiment collection 
    temp = item.return_credentials()
    user = User_Auth(username_in=temp[0],password_in=temp[1], db_client_in=client)
    # authenticate user using the security module or raise exception
    if user.authenticate_token() == False:
        return json.dumps({"message" : False})
       # raise HTTPException(
       #     status_code=status.HTTP_401_UNAUTHORIZED,
       #     detail="The token failed to authenticate"    
       # )
    experiment_temp.insert_one(item.convertJSON()) # data insert into database
    return json.dumps(item.convertJSON()) # return for verification
# end def
# end post

# 5. Call to return a list of all projects "/" - get
@app.get("/names")
async def returm_all_project_names(author : d.Author):
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
# end def
# end get

# 6. Call to return all experiment names for a project - "/{project_id}/" - get
@app.get("/{project_id}/names")
async def return_all_experiment_names(project_id, author : d.Author):
    project = client[project_id] # return collection of experiments
    names_temp = project.list_collection_names()
    names_temp.remove("config") # removes the config entry from the experiments list

    

    # filters based on permission

    return {"names" : names_temp}

# 7. Call to return all dataset names for an experiment - "/{project_id}/{experiment_id}/" - get
@app.get("/{project_id}/{experiment_id}/names")
async def return_all_dataset_names(project_id, experiment_id):
    # TODO: Add a filter to not return the config document storing the experiment variables
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
    experiment.insert_one(data_in.convertJSON())
    return data_in.convertJSON()

@app.post("/{project_id}/set_project")
async def update_project_data(project_id, data_in : d.Simple_Request_body):
    project = client[project_id]
    collection = project["config"] # collection containing project variables
    json_dict = {
        "name" : data_in.name,
        "meta" : data_in.meta,
        "creator" : data_in.creator,
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
            "creator" : result.get("creator"),
            "author" : result.get("author")
        }
        return json.dumps(json_dict)

# authentication

# API call creating a user using User_Auth class
@app.post("/create_user")
async def create_user(user : d.User):
    auth_obj = User_Auth(user.username, user.hash_in,client)
    response = auth_obj.add_user(user.full_name, user.email)
    if response:
        # succesfully created user
        return {"message" : "User Succesfully created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User already exists"
        )

# API call for validating a user token
@app.post("{username}/validate_token")
async def validate_token(token : d.Token):
    # check if token is not expired and if user exists
    payload = jwt.decode(token.access_token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("sub") == None:
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

        result = users.find_one({"username" : username})
        # see if user exists
        if result != None:
            token_in_db = result.get("token") # returns the hashed password from database
            # hashes the password in and compares
            if token_in_db == token.access_token: #### change to digest comparison to stop timing attack 
                # the user has the matching token
                # get the expiry time from database
                expiry = datetime.fromisoformat(result.get("expiry")) # converts string to date
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
        headers={"WWW-Authenticate" : "Bearer"}
    )
# API call generating the token -> returns a token
@app.post("/generate_token", response_model=d.Token)
async def login_for_access_token(credentials : d.User):
    user = User_Auth(credentials.username, credentials.hash_in, client) 
    if user.check_username_exists():
        if user.check_password_valid():
            # authentication complete
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            temp_token = user.create_access_token(expires_delta=access_token_expires)
            # create_access_token acitvates user and sets expiry date in database
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
