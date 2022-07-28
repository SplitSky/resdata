### this file contains the class which describes the datastructure

from pydantic import BaseModel
from enum import Enum
import datetime
### enum for permissions
class Permission(Enum):
    admin = "admin"


# the baseline for data storage. Each measurement is a node in terms of a dataset
class Dataset(BaseModel):
    name: str
    data: list # list of numbers or bits
    meta: str | None = None
    data_type: str

    def convertJSON(self): # converts it into nested dictionary
        json_dict = {
            "name" : self.name,
            "meta" : self.meta,
            "data_type" : self.data_type,
            "data" : self.data # this list can be serialised 
        }
        return json_dict

    def return_name(self):
        return self.name

    # get functions
    def get_name(self):
        return self.name

    def get_data(self):
        return self.data

    def get_meta(self):
        return self.meta

    def get_datatype(self):
        return self.data_type

class Experiment(BaseModel):
    name: str
    children: list[Dataset] # dictionary of data sets each with ID
    meta: str | None = None # implemented union as optional variable
    
    def convertJSON(self): # returns a nested python dictionary
        temp_dict = {}
        i = 0
        for child in self.children:
            temp_dict[i] = child.convertJSON()
            i += 1
        # end for

        json_dict  = {
            "name" : self.name,
            "meta" : self.meta,
            "datasets" : temp_dict # datatype is dicitonary -> double nested      
        }
        return json_dict

    def return_datasets(self): # change the names of those functions to get
        return self.children # returns a list of objects

    def get_name(self):
        return self.name

    def get_meta(self):
        return self.meta


        # this class is the root node of the data structure
class Project(BaseModel):
    name: str
    author: str
    groups: list[Experiment]
    meta: str | None = None

    def convertJSON(self): # returns a dictionary
        temp_dict = {}
        i = 0
        for group in self.groups:
            temp_dict[i] = group.convertJSON()
            i += 1

        json_dict = {
            "name" : self.name,
            "author" : self.author,
            "meta" : self.meta,
            "groups" : temp_dict
        }
        return json_dict

    def convertDictionary(self, dict_in):
        self.name = dict_in.get("name")
        self.author = dict_in.get("author")
        self.meta = dict_in.get("meta")
        self.groups = dict_in.get("groups")

    def return_experiments(self): # return a list of objects
        return self.groups

    # get functions
    def get_name(self):
        return self.name

    def get_author(self):
        return self.author

    def get_meta(self):
        return self.meta


class Simple_Request_body(BaseModel):
    name : str
    meta : str | None = None
    author : str

    def get_variables(self):
        return [self.name, self.meta, self.author]

    def convertJSON(self):
        json_dict = {
            "name" : self.name,
            "meta" : self.meta,
            "author" : self.author
        }
        return json_dict

class User_Request_Body(BaseModel):
    username : str
    hash : str
    full_name : str
    email : str
    # permissions are given separately
    def get_username(self):
        return self.username
    def get_password(self):
        return self.hash
    def get_full_name(self):
        return self.full_name
    def get_email(self):
        return self.email
    def get_hash(self):
        return self.hash


class User(User_Request_Body):
    disabled : bool # this variable is a flag for the API to know whether the user has been authenticated
    salt : str
    token : str
    expiry : datetime.date
    
    def get_disabled(self):
        return self.disabled
    def get_salt(self):
        return self.salt
    def get_token(self):
        return self.token
    def get_expiry(self):
        return self.expiry

class Group(BaseModel):
    name : str
    authors : list[str]
    share : list [str]
    meta : list[str]
    experiments : list[str] # full experiments attached to the group
    datasets : list[str] # loose datasets attache

    # get functions
    def get_authors(self):
        return self.authors

    def get_meta(self):
        return self.meta

    def get_experiments(self):
        return self.experiments

    def get_datasets(self):
        return self.get_datasets

    def get_name(self):
        return self.name

    def get_share(self):
        return self.share

    def convertJSON(self):
        json_dict = {
            "authors" : self.authors,
            "share" : self.share,
            "meta" : self.meta,
            "experiments" : self.experiments,
            "datasets" : self.datasets
        }
        return json_dict
