# this file contains the class which describes the datastructure
from __future__ import annotations

from typing import Union, List

from pydantic import BaseModel
from enum import Enum
import json


# the baseline for data storage. Each measurement is a node in terms of a dataset
from pydantic.typing import NoneType


class Dataset(BaseModel):
    name: str
    data: List  # list of numbers or bits
    meta: Union[List[str], NoneType] = None
    data_type: str
    author : List[dict]
    # variables used in authentication
    username: str | None = None
    token : str | None = None

    def convertJSON(self): # converts it into nested dictionary
        # this function skips over the username and token variables
        python_dict = {
            "name" : self.name,
            "meta" : self.meta,
            "data_type" : self.data_type,
            "data" : self.data, # this list can be serialised
            "author" : self.author
        }
        return python_dict

    def return_credentials(self):
        return [self.username, self.token]

    def set_credentials(self, username, token):
        self.username = username
        self.token = token

    # TODO: The functions should be removed and replaced with self.name etc

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
    children: List[Dataset]  # dictionary of data sets each with ID
    meta: Union[List[str], NoneType] = None  # implemented union as optional variable

    def convertJSON(self):  # returns a nested python dictionary
        temp_dict = {}
        i = 0
        for child in self.children:
            temp_dict[i] = child.convertJSON()
            i += 1
        # end for

        json_dict = {
            "name": self.name,
            "meta": self.meta,
            "datasets": temp_dict  # datatype is dictionary -> double nested
        }
        return json_dict

    def return_datasets(self):  # change the names of those functions to get
        return self.children  # returns a list of objects

    def get_name(self):
        return self.name

    def get_meta(self):
        return self.meta

        # this class is the root node of the data structure


class Project(BaseModel):
    name: str
    author: str
    groups: Union[List[Experiment],NoneType] = None
    meta: Union[List[str], NoneType] = None

    def convertJSON(self):  # returns a dictionary
        temp_dict = {}
        i = 0
        for group in self.groups:
            temp_dict[i] = group.convertJSON()
            i += 1

        json_dict = {
            "name": self.name,
            "author": self.author,
            "meta": self.meta,
            "groups": temp_dict
        }
        return json_dict

    def convertDictionary(self, dict_in):
        self.name = dict_in.get("name")
        self.author = dict_in.get("author")
        self.meta = dict_in.get("meta")
        self.groups = dict_in.get("groups")

    def return_experiments(self):  # return a list of objects
        return self.groups

    # get functions
    def get_name(self):
        return self.name

    def get_author(self):
        return self.author

    def get_meta(self):
        return self.meta

    def print_data(self):
        for exp in self.groups:
            string_out = exp.convertJSON()
            print("printing experiment: ")
            print(string_out)


class Simple_Request_body(BaseModel):
    name: str
    meta: Union[List[str], NoneType] = None
    author: str

    # def get_variables(self):
    #    return [self.name, self.meta, self.author]

    def convertJSON(self):
        json_dict = {
            "name": self.name,
            "meta": self.meta,
            "author": self.author
        }
        return json_dict


# Token used in authentication
class Token(BaseModel):
    access_token: str
    token_type: str


# user class used for authentication
class User(BaseModel):
    username: str
    hash_in: str
    email: Union[str,NoneType] = None
    full_name: Union[str, NoneType] = None


class permission(Enum):
    #ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    PUBLIC = "public"

class Author(BaseModel):
    # object used for representing the author of a dataset, experiment, project
    name : str
    permission : str

    def load_data(self,dict_in): # initialises the author object from json
        #temp = json.loads(json_in)
        self.name = dict_in.get("name")
        self.permission = dict_in.get("permission")
