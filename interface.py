from fastapi import FastAPI, Form
from pydantic import BaseModel
import numpy as np
import hashlib as hash
import os
import pymongo
import variables as var
from pymongo.mongo_client import MongoClient
import json
import main as mn
import random
import requests

def create_test_file(filename_in):
    test_data_2D = []
    test_data_3D = []
    for i in range(0,100):
        test_data_2D.append([i,random.randint(0,100),random.randint(0,100) ])
        test_data_3D.append([i,random.randint(0,100),random.randint(0,100),random.randint(0,100)])
    
    dataset1 = mn.Dataset(name="dataset1", data=test_data_2D, meta="test dataset 1", data_type="2D dataset")
    dataset2 = mn.Dataset(name="dataset2", data=test_data_3D, data_type="3D dataset")

    experiment = mn.Experiment(name="experiment1", children=[dataset1, dataset2])
    project = mn.Project(name="test project", author="J. Smith", groups=[experiment], meta="This is a test")
    with open(filename_in, 'w') as file:
        json.dump(project.convertJSON(),file)

    # project.convertJSON()

def load_file(filename_out): # returns a project object
    # load files. Initially json files in the correct format
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        python_dict = json.loads(json_string)

        project = mn.Project(groups=[]) # initialise empty project
        project.convertDictionary(python_dict)
        file.close()

    return project

class makeAPIcall:

    def __init__(self):
        


    def formatted_print(self, obj):
        text = json.dumps(obj, sort_keys=True, indent=4)
        print(text)
 


    def get_dataset_data(self, api):
        response = requests.get(f"{api}")
        if response.status_code == 200:
            print("sucessfully fetched the data")
            self.formatted_print(response.json())
        else:
            print("Hello person, there's a {response.status_code} error with your request")

    def get_user_data(self, api, parameters):
        response = requests.get(f"{api}", params=parameters)
        if response.status_code == 200:
            print("sucessfully fetched the data with parameters provided")
            self.formatted_print(response.json())
        else:
            print(
                f"Hello person, there's a {response.status_code} error with your request")
     

def main():
    filename = "test.json"
    project = load_file(filename)
    # api path defined by /{project_id}/{experiment_id}/{dataset_id}
    #response = requests.get(f"{api}")
    

#end main

main()
