### this file contains the class which describes the datastructure

from pydantic import BaseModel

# the baseline for data storage. Each measurement is a node in terms of a dataset
class Dataset(BaseModel):
    name: str
    data: list # list of numbers or bits
    meta: str | None = None
    data_type: str

    def convertJSON(self):
        json_dict = {
            "name" : self.name,
            "meta" : self.meta,
            "data_type" : self.data_type,
            "data" : self.data 
        }
        return json_dict

    def return_name(self):
        return self.name

class Experiment(BaseModel):
    name: str
    children: dict # dictionary of data sets each with ID
    meta: str | None = None # implemented union as optional variable
    
    def convertJSON(self):
    ### uses the nesting feature of mongodb to allow for hierarchal storage of data
        json_dict  = {
            "name" : self.name,
            "meta" : self.meta,
            "datasets" : self.children # datatype is dicitonary -> double nested      
        }
        return json_dict

    def return_datasets(self):
        return self.children

        # this class is the root node of the data structure
class Project(BaseModel):
    name: str | None = None
    author: str | None = None
    groups: dict
    meta: str | None = None

    def convertJSON(self):
        json_dict = {
            "name" : self.name,
            "author" : self.author,
            "meta" : self.meta,
            "groups" : self.groups
        }
        return json_dict

    def convertDictionary(self, dict_in):
        self.name = dict_in.get("name")
        self.author = dict_in.get("author")
        self.meta = dict_in.get("meta")
        self.groups = dict_in.get("groups")


