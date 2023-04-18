# this file contains the class which describes the datastructure
from ctypes import string_at
from typing import Union, List
from pydantic import BaseModel
import random
from datetime import date


class Dataset(BaseModel):
    """The lowest node of the tree data structure. This object contains the actual data being stored."""
    name: str
    """The unique name of the dataset. This is used by most of the code to find and retrieve the dataset."""
    data: List  # list of numbers or bits
    """List storing any variable type. Used as the unit of storage."""
    meta: Union[dict, None] = None
    """User generated metadata. It's a list of string variables. Datasets are time stamped upon insertion into the dataset."""
    data_type: str
    """Allows for user generated flag which distinguishes types of data included"""
    author: List[dict]
    """List of authors with their given permissions. Used in authentication and retrieval."""
    # variables used in authentication
    username: Union[str, None] = None
    """Optional variable used during authentication. Works as a credentials requests body. Contain the username of the user inserting the dataset"""
    token: Union[str, None] = None
    """Optional variable used during authentication. Generated JWT token which is then used to verify that the user authenticated."""

    # additions not finalised
    data_headings: List[str]
    '''Variable containing the headings for the data contained within the data array.'''

    def convertJSON(self):  # converts it into nested dictionary
        """Function returning a dictionary containing data to be inserted into the database."""
        # this function skips over the username and token variables
        python_dict = {
            "name": self.name,
            "meta": self.meta,
            "data_type": self.data_type,
            "data": self.data,  # this list can be serialised
            "author": self.author,
            "data_headings": self.data_headings
        }
        return python_dict

    def return_credentials(self):
        """Used to return the credentials during authentication."""
        return [self.username, self.token]

    def set_credentials(self, username, token):
        """Set function for the credentials."""
        self.username = username
        self.token = token


class Experiment(BaseModel):
    """Node containing datasets within the data structure. Equivalent to the collection in the database."""
    name: str
    """The experiment name. Used during query to locate the dataset."""
    children: List[Dataset]
    """List of dataset objects."""
    meta: Union[dict, None] = None  # implemented union as optional variable
    """User generated metadata."""
    author: List[dict]
    """Experiment author"""

    def convertJSON(self):  # returns a nested python dictionary
        """Returns a nested Python dictionary by recursively calling the dataset function."""
        temp_dict = {}
        i = 0
        if self.children != None:
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


class Project(BaseModel):
    """Root of the data structure. Equivalent to a database."""
    name: str
    """The project name. Used during query and retrieval."""
    creator: str
    """The username of the user that created the project."""
    groups: Union[List[Experiment], None] = None
    """List of experiements belonging to the project."""
    meta: Union[dict, None] = None
    """User generated metadata."""
    author: List[dict]
    """List of authors of the project along with their permissions. Used in authentication and determining the scope of the access."""

    def convertJSON(self):  # returns a dictionary
        """Returns a nested Python dictionary by recursively calling the experiment function."""
        temp_dict = {}
        i = 0
        if self.groups != None:
            for group in self.groups:
                temp_dict[i] = group.convertJSON()
                i += 1

        json_dict = {
            "name": self.name,
            "author": self.author,
            "meta": self.meta,
            "creator": self.creator,
            "groups": temp_dict
        }
        return json_dict

    def convertDictionary(self, dict_in):
        """Updates variables within the project using a dictionary as an input."""
        self.name = dict_in.get("name")
        self.creator = dict_in.get("creator")
        self.meta = dict_in.get("meta")
        self.groups = dict_in.get("groups")
        self.author = dict_in.get("author")


class Simple_Request_body(BaseModel):
    """Request body used to update the variables within the project config file in the database."""
    name: str
    """Name of the project"""
    meta: Union[dict, None] = None
    "User generated metadata."""
    author: List[dict]
    """Project author list. See project."""
    creator: str
    """Username of the user that created the project"""

    def convertJSON(self):
        """Returns a python dictionary of the data structure."""
        json_dict = {
            "name": self.name,
            "meta": self.meta,
            "creator": self.creator,
            "author": self.author
        }
        return json_dict


# Token used in authentication
class Token(BaseModel):
    """Token request body used in authentication"""
    access_token: str
    """The variable storing the JWT token"""
    token_type: str
    """Variable storing the token type"""


# user class used for authentication
class User(BaseModel):
    """User request body. Used in user creation."""
    username: str
    """Unique username"""
    hash_in: str
    """Hash of the password obtained within the interface"""
    email: Union[str, None] = None
    """Optional email variable"""
    full_name: Union[str, None] = None
    """Optional full name variable"""
    tunnel_key: Union[str, None] = None
    """Optional key used for secure communication with API"""


class Author(BaseModel):
    """Author request body. Used in determining the scope of the access."""
    # object used for representing the author of a dataset, experiment, project
    name: str
    """Username belonging to the author"""
    permission: str
    """The permissions granted to the user"""

    # optional name used in groups
    group_name: Union[str, None] = None
    """The variable used in group assignment and """


    def load_data(self, dict_in):  # initialises the author object from json
        """Updates the variables based on Python dictionary input."""
        # temp = json.loads(json_in)
        self.name = dict_in.get("name")
        self.permission = dict_in.get("permission")


class Ring(BaseModel):
    ring_id: int
    ring_dio: float
    quality: Union[int, None]
    pitch: Union[float, None]
    threshold: Union[float, None]
    spectrum_dataset: List[List]
    spectrum_headings: List[List[str]]
    spectrum_names: List[str]
    spectrum_data_types: List[str]

    author: List[dict]
    datasets: Union[List, None]

    def convert_to_document_list(self):
        self.datasets = [] # clear dataset
        # initialise the dimensions dataset
        dataset = Dataset(name="ring_no. " + str(self.ring_id),
                          data=[self.ring_dio, self.quality, self.pitch, self.threshold],
                          data_type="dimensions",
                          meta={"ring_id": self.ring_id},
                          author=self.author,
                          data_headings=["ring diameter", "quality", "pitch", "threshold"])
        self.datasets.append(dataset)
        # initialise spectrum list
        for i in range(0,len(self.spectrum_names)):
            dataset = Dataset(name=self.spectrum_names[i] + " - ring no." + str(self.ring_id),
                              data=self.spectrum_dataset[i],
                              data_type=self.spectrum_data_types[i], 
                              meta={"ring_id": self.ring_id}, 
                              author=self.author, 
                              data_headings=self.spectrum_headings[i])
            self.datasets.append(dataset)
        return self.datasets
