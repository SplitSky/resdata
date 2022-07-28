import json
import requests
from datetime import date
import datastructure as d
from requests.auth import HTTPBasicAuth
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
        print(response.json())
        # convert to object and return
        temp = response.json()
        temp = json.loads(temp)
        return temp       

    def return_fulldataset(self,project_name: str, experiment_name : str, dataset_name: str):
        response = requests.get(url=self.path+project_name+"/"+experiment_name+"/"+dataset_name)
        print("Retrieving single dataset")
        print("response code: + str(response)")
        print("content of the dataset: ")
        print(response.json())
        temp = response.json()
        temp = json.loads(temp)
        dataset = d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"), data_type=temp.get("data_type"))
        return dataset # returns an object of DataSet class

    def insert_experiment(self, project_name : str, experiment: d.Experiment):
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
        print("Printing variables")
        print(self.path)
        print(project_name)
        print(experiment_name)

        response = requests.get(self.path + project_name + "/names") # request the names of the datasets connected to experiment
        print(type(response.json()))
        names_dict = response.json()
        names_list = names_dict.get("names")
        datasets = []
        for name in names_list:
            datasets.append(self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name))
        # call api for each datasets and return the contents -> then add the contents to an object and return the object
        response = requests.get(self.path + project_name + "/" + experiment_name + "/details")
        exp_dict = json.loads(response.json())
        experiment = d.Experiment(name=exp_dict.get("name"),children=datasets, meta=exp_dict.get("meta"))
        return experiment

    def return_fullproject(self, project_name: str):
        response = requests.get(self.path + project_name)
        exp_names_dict = response.json()
        exp_names_list = exp_names_dict.get(self.path + "/names")
        print("Experiment names: ")
        print(exp_names_list)
        experiments = []
        for exp_name in exp_names_list: ### return names function returns type none
            experiments.append(self.return_fullexperiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        proj_dict = response.json()
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
        return list.get("names")


    ### initialize project
    def init_project(self, project: d.Project):
        request_body = d.Simple_Request_body(name=project.get_name(),meta=project.get_meta(), author=project.get_author())
        response = requests.post(self.path + project.get_name() + "/set_project", json=request_body.convertJSON()) # updates the project variables
        return response

    ### initialize experiment
    def init_experiment(self,project_id ,experiment : d.Experiment):
        request_body = d.Simple_Request_body(name=experiment.get_name(),meta=experiment.get_meta(), author="a")
        print("request body")
        print(request_body)
        response = requests.post(self.path + project_id + "/" + experiment.get_name() + "/set_experiment", json=request_body.convertJSON()) # updates the experiment variables
        return response 

    ### groups and managing access to them

    def create_group(self, user : d.User_Request_Body):
        # return names of user's experiments and loose datasets. Print as tree
        
        # take an input of indexes of names to include in the group

        # retrieve user id
        
        # insert document in group
        a = 1
        
    def discard_group(self, user : d.User_Request_Body):
        # return tree of group
        
        # ask for confirmation

        # remove the group entry in the database
        a = 2

    def share_group_read_only(self, user : d.User_Request_Body, username):
        # check if user exists

        # append share to the group

    def share_group_full(self, user : d.User_Request_Body, username):
        # check if user exists

        # append author to the group

    def create_user(self, username, password):
        # insert the user into the database

    def login(username, password):
        basic = HTTPBasicAuth(username, password)
        response = requests.get(self.path + "login", auth=basic)
        return response

def main():
    project_name = "S_Church"
    #experiment_name = "experiment 1"
    author_name = "S.Church" 
    filename = "test.json"
    path = "http://127.0.0.1:8000/"
    
    t.create_test_file_project(filename, [1,1], project_name, author_name)
    project_in = t.load_file_project(filename)
    ui = API_interface(path)

    ui.check_connection()
    # insert project

    print("Inserting Project")
    temp = ui.insert_project(project=project_in)
    print("Response:")
    print(temp)
    
    print("Returning Project")
    temp = ui.get_project_names()
    #temp = ui.return_fullproject(project_in.get_name())
    print(temp)


main()
