import json
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
        response = requests.post(url=self.path+project_name+"/"+experiment_name+"/"+dataset_in.get_name()+"/insert_dataset", json=dataset_in.convertJSON())
        print("Inserting single dataset")
        # convert to object and return
        temp = response.json()
        temp = json.loads(temp)
        return temp       

    def return_fulldataset(self,project_name: str, experiment_name : str, dataset_name: str):
        print("Retrieving dataset") 
        response = requests.get(url=self.path+project_name+"/"+experiment_name+"/"+dataset_name+"/return_dataset")
        print(response.json())
        temp = response.json()
        temp = temp.get("datasets data") # returns the list of dataset dictionaries
        temp = temp[0] # simplify the return of the variable
        print("temp")
        print(temp)
        print("The dataset returned")
        
        return d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),data_type=temp.get("data_type"))

    def insert_experiment(self, project_name : str, experiment: d.Experiment):
        print("Inserting experiment")
        # takes in the experiment object 
        # perform multiple calls to create an experiment directory and then
        # insert datasets one by one
        experiment_name = experiment.get_name()
        # check if experiment exists:
        if self.check_experiment_exists(project_name,experiment_name) == False:
            # if it doesn't initialise it
            self.init_experiment(project_name, experiment)
        
        # init the experiment
        response = []
        temp = experiment.return_datasets()
        for dataset in temp:
            # for each dataset in experiment call API 
            response.append(self.insert_dataset(project_name, experiment_name, dataset))
        # call to initialise experiment and return structure
        return response

    def return_fullexperiment(self, project_name: str, experiment_name: str):
        # call api to find the names of all datasets in the experiment
        print("Returning experiment")
        # return the list of datasets
        response = requests.get(self.path + project_name +"/"+experiment_name +"/names") # request the names of the datasets connected to experiment
        names_dict = response.json()
        names_list = names_dict.get("names")
        datasets = []
        
        print("Names in return_fullexperiment")
        print("names_list")
        print(names_list)
        print("names_dict")
        print(names_dict)
        exp_name = "default"
        exp_meta = ["default"]


        for name in names_list:
            temp = self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name)
            if temp.get_datatype() == "configuration file":
                # update experiment parameters
                exp_name = temp.name
                exp_meta = temp.meta
            else:
                datasets.append(self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name))
        # call api for each datasets and return the contents -> then add the contents to an object and return the object
        
        print("exp dict")
        exp_dict = response.json()
        print(exp_dict)
        experiment = d.Experiment(name=exp_name,children=datasets, meta=exp_meta)
        return experiment

    def return_fullproject(self, project_name: str):
        # request a list of all experiments within the project
        print("returning project")
        response = requests.get(self.path + project_name +"/names") # returns experiment names including config
        exp_names_list = response.json().get("names")
        print("Experiment names: ")
        print(exp_names_list)
        experiments = []
        for exp_name in exp_names_list: ### return names function returns type none
            experiments.append(self.return_fullexperiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        print("response: " + str(response))
        proj_dict = json.loads(response.json()) # conversion into dict
        
        project = d.Project(name=proj_dict.get("name"),author=proj_dict.get("author") ,groups=experiments ,meta=proj_dict.get("meta") )
        return project

    def check_project_exists(self,project_name : str):
        response = requests.get(self.path+ "names") # returns a list of strings
        names = response.json().get("names")
        if project_name in names:
            return True
        else:
            print("Project with that name is not present in the database")
            return False

    def check_experiment_exists(self, project_name: str, experiment_name : str):
        response = requests.get(self.path + project_name +"/names")
        names = response.json().get("names") # may have to json.dumps()
        if experiment_name in names:
            return True
        else:
            print("Experiment with that name is not present in the database")
            return False

    def insert_project(self, project: d.Project):
        response_out = []
        # set project in database
        # check if project exists. If not initialise it 
        if self.check_project_exists(project_name=project.get_name()) == False:
            self.init_project(project)
        temp = project.return_experiments()
        for experiment in temp:
            response_out.append(self.insert_experiment(project.get_name(),experiment))
        return response_out

    ## two functions to return names of the experiment and the names of the project

    def get_project_names(self):
        response = requests.get(self.path + "names")
        list = response.json() # this returns a python dictionary
        print("project_names : " + str(list))
        return list.get("names")


    ### initialize project
    def init_project(self, project: d.Project):
        request_body = d.Simple_Request_body(name=project.get_name(),meta=project.get_meta(), author=project.get_author())
        response = requests.post(self.path + project.get_name() + "/set_project", json=request_body.convertJSON()) # updates the project variables
        return response

    ### initialize experiment
    def init_experiment(self,project_id ,experiment : d.Experiment):
        #request_body = d.Dataset(name=experiment.get_name(),meta=experiment.get_meta(), data_type="configuration file", data=[])
        print("initialising experiment request body")
        #print(request_body)
        #response = requests.post(self.path + project_id + "/" + experiment.get_name() + "/set_experiment", json=request_body.convertJSON()) # updates the experiment variables
        #return response
        dataset_in = d.Dataset(name=experiment.name,data=[],meta=[],data_type="configuration file")
        # insert special dataset
        self.insert_dataset(project_name=project_id, experiment_name=experiment.name,dataset_in=dataset_in)


