# Description of datastructures
from __future__ import annotations
# For pydantic typing
from typing import Union, List

# Base model
from pydantic import BaseModel


class Dataset(BaseModel):
    """Baseline for data storage. Each measurement is a node in terms of a dataset"""
    name: str
    data: list  # list of numbers or bits
    meta: Union[str, None] = None
    data_type: str


###################################################
class Experiment(BaseModel):
    name: str
    children: List[Dataset]  # dictionary of data sets each with ID
    meta: Union[str, None] = None  # implemented union as optional variable

    def json(self) -> dict:  # returns a nested python dictionary
        return {
            "name": self.name,
            "meta": self.meta,
            "datasets": {child.name: child.json() for child in self.children}
        }


###################################################
class Project(BaseModel):
    name: str
    author: str
    groups: List[Experiment]
    meta: Union[str, None] = None

    def json(self) -> dict:  # returns a dictionary
        return {
            "name": self.name,
            "author": self.author,
            "meta": self.meta,
            "groups": {group.name: group.json() for group in self.groups}
        }

    def convertDictionary(self, dict_in: dict) -> None:
        self.name = dict_in.get("name")
        self.author = dict_in.get("author")
        self.meta = dict_in.get("meta")
        self.groups = dict_in.get("groups")


###################################################
class simpleRequestBody(BaseModel):
    name: str
    meta: Union[str, None] = None
    author: str


###################################################
class userRequestBody(BaseModel):
    username: str
    hash: str
    permission: str


###################################################
class Group(BaseModel):
    authors: List[str]
    meta: List[str]
    experiments: List[str]  # full experiments attached to the group
    datasets: List[str]  # loose datasets attache
