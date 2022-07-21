import json
import main as mn # imports the main for api calls
import requests
from datetime import date
import datastructure as d

import testing as t # this import should be removed for deployment
# storage in database is done using nested dictionaries


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

        print("content of the dataset: ")
        print(response.json())

        return response.json()

    def insert_experiment(self, project_name : str, experiment: d.Experiment):
        # takes in the experiment object 
        # perform multiple calls to create an experiment directory and then
        # insert datasets one by one
        experiment_name = experiment.get_name()
        response = []
        temp = experiment.return_datasets()
        for dataset in temp:
            # for each dataset in experiment call API 
            response.append(self.insert_dataset(project_name, experiment_name, dataset))
        # call to initialise experiment and return structure
        return response

    def return_fullexperiment(self, project_name: str, experiment_name: str):
        # call api to find the names of all datasets in the experiment
        response = requests.get(self.path + project_name + "/" + experiment_name)
        print(type(response.json()))
        names_dict = response.json()
        names_list = names_dict.get("names")
        datasets = []
        for name in names_list:
            datasets.append(self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name))
        # call api for each datasets and return the contents -> then add the contents to an object and return the object
        return datasets

    def return_fullproject(self, project_name: str):
        response = requests.get(self.path + project_name)
        exp_names_dict = response.json()
        exp_names_list = exp_names_dict.get("names")
        experiments = []
        for exp_name in exp_names_list:
            experiments.append(self.return_fullexperiment(project_name, exp_name))

    def check_project_exists(self,project_name : str):
        response = requests.get(self.path) # returns a list of strings
        names = response.json().get("names")
        if project_name in names:
            return True
        else:
            print("Project with that name is not present in the database")
            return False

    def check_experiment_exists(self, project_name: str, experiment_name : str):
        response = requests.get(self.path + project_name)
        names = response.json().get("names") # may have to json.dumps()

        if experiment_name in names:
            return True
        else:
            print("Experiment with that name is not present in the database")
            return False
    #def return_fullproject(self,project_name:  str):
    #    response = requests.get()
        

    def insert_project(self, project: d.Project):
        response = []
        temp = project.return_experiments()
        for experiment in temp:
            response.append(self.insert_experiment(project.get_name(),experiment))
        return response
    

def main():
    project_name = "test2"
    #experiment_name = "experiment 1"
    author_name = "j.smith" 
    filename = "test.json"
    path = "http://127.0.0.1:8000/"
    
    t.create_test_file_project(filename, [2,3], project_name, author_name)
    project_in = t.load_file_project(filename)
    ui = API_interface(path)
    print("file content")
    print(project_in)

    ui.check_connection()
    # insert project
    
    print("Inserting Project")
    temp = ui.insert_project(project=project_in)
    print("Response:")
    print(temp)
    
    print("Returning Project")
    temp = ui.return_fullproject(project_in.get_name())

main()
