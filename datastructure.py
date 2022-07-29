# Description of datastructures
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class Dataset(BaseModel):
    """Baseline for data storage. Each measurement is a node in terms of a dataset"""
    name: str
    data: list  # list of numbers or bits
    meta: str | None = None
    data_type: str

    def convertJSON(self) -> dict:
        """converts it into nested dictionary"""
        return {
            "name": self.name,
            "meta": self.meta,
            "data_type": self.data_type,
            "data": self.data  # this list can be serialised
        }


###################################################
class Experiment(BaseModel):
    name: str
    children: list[Dataset]  # dictionary of data sets each with ID
    meta: str | None = None  # implemented union as optional variable

    def convertJSON(self) -> dict:  # returns a nested python dictionary
        return {
            "name": self.name,
            "meta": self.meta,
            "datasets": {child.name: child.convertJSON() for child in self.children}
        }


###################################################
class Project(BaseModel):
    name: str
    author: str
    groups: list[Experiment]
    meta: str | None = None

    def convertJSON(self) -> dict:  # returns a dictionary
        return {
            "name": self.name,
            "author": self.author,
            "meta": self.meta,
            "groups": {group.name: group.convertJSON() for group in self.groups}
        }

    def convertDictionary(self, dict_in: dict) -> None:
        self.name = dict_in.get("name")
        self.author = dict_in.get("author")
        self.meta = dict_in.get("meta")
        self.groups = dict_in.get("groups")


###################################################
class simpleRequestBody(BaseModel):
    name: str
    meta: str | None = None
    author: str

    def get_variables(self) -> List[str]:
        return [self.name, self.meta, self.author]

    def convertJSON(self) -> dict:
        return {
            "name": self.name,
            "meta": self.meta,
            "author": self.author
        }


###################################################
class userRequestBody(BaseModel):
    username: str
    hash: str
    permission: str


###################################################
class Group(BaseModel):
    authors: list[str]
    meta: list[str]
    experiments: list[str]  # full experiments attached to the group
    datasets: list[str]  # loose datasets attache

    def convertJSON(self) -> dict:
        return {
            "authors": self.authors,
            "meta": self.meta,
            "experiments": self.experiments,
            "datasets": self.datasets
        }
