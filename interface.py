from fastapi import FastAPI, Form
from pydantic import BaseModel
import numpy as np
import hashlib as hash
import os
import pymongo
from pymongo.common import WAIT_QUEUE_TIMEOUT
import variables as var
from pymongo.mongo_client import MongoClient
import json
import main as mn
import random
import requests
from datetime import date

def create_test_file(filename_in, structure, project_name, author_name):
    '''
    filename_in     string      the name of the json file
    structure       list        a list containing the number of the experiments and datasets [0,0]
    '''

    x = []
    y = []
    y2 = []
    for i in range(0,100):
        x.append(i)
        y.append(random.randint(0,100))
        y2.append(random.randint(0,100))
    test_data_3D = [x,y,y2]
    # dataset1 = mn.Dataset(name="dataset1", data=test_data_2D, meta="test dataset 1", data_type="2D dataset")
    experiments = []
    datasets = []
    meta_temp = str(date.today())
    for j in range(0,structure[1],1):
        dataset2 = mn.Dataset(name="dataset " + str(j), data=test_data_3D, data_type="3D dataset", meta=meta_temp)
        datasets.append(dataset2) 

    for i in range(0,structure[0],1):
        experiment = mn.Experiment(name="experiment " + str(i), children=datasets, meta=meta_temp)
        experiments.append(experiment)
    
    project = mn.Project(name=project_name, author=author_name, groups=experiments, meta="This is a test")
    with open(filename_in, 'w') as file:
        json.dump(project.convertJSON(),file)
        file.close()
    # project.convertJSON()

def load_file(filename_out): # returns a project object
    # load files. Initially json files in the correct format
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        #python_dict = json.loads(json_string)
        print("The data type is: " + str(type(json_string)))

        project = mn.Project(groups=[]) # initialise empty project
        project.convertDictionary(json_string)
        file.close()
    return project


def load_file_easy(filename_out):
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        #python_dict = json.loads(json_string)
        #print("The data type is: " + str(type(json_string)))
        #project = mn.Project(groups=[]) # initialise empty project
        #project.convertDictionary(json_string)
        file.close()
    return json.dumps(json_string)


class makeAPIcall:

    #def __init__(self):

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
            print(f"Hello person, there's a {response.status_code} error with your request")

def main():

    project_name = "test1"
    author_name = "j.smith" 


    filename = "test.json"
    path = "http://127.0.0.1:8000/"
    create_test_file(filename,[1,1],project_name, author_name)
    json_string = load_file_easy(filename) # returns the json string from the file
    #project = load_file(filename) # returns the project class from the json file
    # api path defined by /{project_id}/{experiment_id}/{dataset_id}
    response = requests.get(path)
    print("Checking for connection...")
    if response == 200:
        print("Connection successful")
        print(response)
    
    print(json_string)
    response = requests.post(url=path + project_name,json=json_string)

    print("Inserting the project from json file")
    print("Response code: " + str(response))
    print("response content: ")
    print(response.json())

    response = requests.get(path+str(project_name))
    print("Retrieving project from database")
    print("Response code: " + str(response))


    # return the whole project from dataset using calls


    # returns just the names of the datasets


    # return just the project names
#end main

main()
