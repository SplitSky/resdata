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

    def insert_dataset(self,project_name, experiment_name, dataset_in):
        response = requests.post(url=self.path+project_name+"/"+experiment_name+"/"+dataset_in.return_name(), json=dataset_in.convertJSON())
        print("Inserting single dataset")
        print("response code: " + str(response))
        print("response content: ")
        return response.json()       

    def return_fulldataset(self,project_name, experiment_name, dataset_name):
        response = requests.get(url=self.path+project_name+"/"+experiment_name+"/"+dataset_name)
        print("Retrieving single dataset")
        print("response code: + str(response)")
        return response.json()

    def insert_experiment(self, project_name, experiment_name, experiment: d.Experiment):
        # takaes in the experiment object 
        # perform multiple calls to create an experiment directory and then
        # insert datasets one by one
        experiment_dict = experiment.return_datasets() # returns the dictionary of experiment

        for i,entry in experiment_dict.items():
            # 
            self.insert_dataset(project_name, experiment_name, entry.get("name")) 

        # call to initialise experiment and return structure

        # loop of calls updating each dataset
    

def main():
    project_name = "test1"
    experiment_name = "experiment 1"
    author_name = "j.smith" 
    filename = "test.json"
    path = "http://127.0.0.1:8000/"
    

    t.create_test_file_dataset(filename)
    dataset_in = t.load_file_dataset(filename)
    
    response = requests.get(path)
    print("Checking for connection...")
    if response == 200:
        print("Connection successful")
        print(response)
    
    # inserting one dataset

    
    # return one dataset

    print("Retrieving single dataset")
    print("response code: " + str(response))
    print("response content: ")
    print(response.json())

main()
