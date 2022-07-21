import json
import main as mn # imports the main for api calls
import random
import requests
from datetime import date
import datastructure as d

import testing as t # this import should be removed for deployment



class API_interface():
    def __init__(self, path_in):
        self.path = path_in

    def check_connection(self):
        response = requests.get(self.path)
        if response == 200:
            return True
        else:
            return False

    def insert_dataset(self,project_name : str, experiment_name : str, dataset_in: d.Dataset):
        response = requests.post(url=self.path+project_name+"/"+experiment_name+"/"+dataset_in.get_name(), json=dataset_in.convertJSON())
        print("Inserting single dataset")
        print("response code: " + str(response))
        print("response content: ")
        return response.json()       

    def return_fulldataset(self,project_name: str, experiment_name : str, dataset_name: str):
        response = requests.get(url=self.path+project_name+"/"+experiment_name+"/"+dataset_name)
        print("Retrieving single dataset")
        print("response code: + str(response)")
        return response.json()

    def insert_experiment(self, project_name : str, experiment: d.Experiment):
        # takaes in the experiment object 
        # perform multiple calls to create an experiment directory and then
        # insert datasets one by one
        experiment_name = experiment.get_name()
        response = []
        temp = experiment.return_datasets()
        for dataset in temp:
            # for each dataset in experiment call API 
            response.append(self.insert_dataset(project_name, experiment_name, dataset))
            
        # call to initialise experiment and return structure

    def insert_project(self, project: d.Project):
        response = []
        temp = project.return_experiments()
        for experiment in temp:
            response.append(self.insert_experiment(project.get_name(),experiment))
    

def main():
    project_name = "test1"
    experiment_name = "experiment 1"
    author_name = "j.smith" 
    filename = "test.json"
    path = "http://127.0.0.1:8000/"
    

    
    #t.create_test_file_dataset(filename)
    #dataset_in = t.load_file_dataset(filename)
    
    t.create_test_file_project(filename, [1,1], project_name, author_name)
    project_in = t.load_file_project(filename)


    print("file content")
    print(project_in)

    response = requests.get(path)
    print("Checking for connection...")
    if response == 200:
        print("Connection successful")
        print(response)


main()
