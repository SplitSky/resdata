import json
import requests
from datetime import date
import datastructure as d
import hashlib as h
from requests.auth import HTTPBasicAuth

# storage in database is done using nested dictionaries


# hash function used in the API
def return_hash(password : str):
    # this function only hashes the password for sending purposes
    temp = h.shake_256()
    temp.update(password.encode('utf8'))
    return temp.hexdigest(64)

class API_interface():

    def __init__(self, path_in):
        self.path = path_in
        self.token = ""
    def check_connection(self):
        response = requests.get(self.path)
        if response == 200:
            return True
        else:
            return False

    def insert_dataset(self,project_name : str, experiment_name : str, dataset_in: d.Dataset):
        response = requests.post(url=self.path+project_name+"/"+experiment_name+"/"+dataset_in.get_name()+"/insert_dataset", json=dataset_in.convertJSON())
        temp = response.json() # loads the json return
        temp = json.loads(temp) # converts it into python dict
        return temp       

    def return_fulldataset(self,project_name: str, experiment_name : str, dataset_name: str):
        response = requests.get(url=self.path+project_name+"/"+experiment_name+"/"+dataset_name+"/return_dataset")
        temp = response.json()
        temp = temp.get("datasets data") # returns the list of dataset dictionaries
        temp = temp[0] # simplify the return of the variable
        
        return d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),data_type=temp.get("data_type"))

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
            # check if the dataset already exists. If it does don't append
            if not self.check_dataset_exists(project_name, experiment_name, dataset.name):
                response.append(self.insert_dataset(project_name, experiment_name, dataset))
                # skips the insertion of the datasets that already exist
        # call to initialise experiment and return structure
        return response

    def return_fullexperiment(self, project_name: str, experiment_name: str):
        # call api to find the names of all datasets in the experiment
        # return the list of datasets
        response = requests.get(self.path + project_name +"/"+experiment_name +"/names") # request the names of the datasets connected to experiment
        names_dict = response.json()
        names_list = names_dict.get("names")
        datasets = []
        
        exp_name = "default"
        exp_meta = ["default"]


        for name in names_list:
            temp = self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name)
            if temp.get_datatype() == "configuration file":
                # update experiment parameters
                exp_name = temp.name
                exp_meta = temp.meta
                print("THIS FUNCTION IS BEING RUN")
            else:
                datasets.append(self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name))
        # call api for each datasets and return the contents -> then add the contents to an object and return the object
        
        experiment = d.Experiment(name=exp_name,children=datasets, meta=exp_meta)
        return experiment

    def return_fullproject(self, project_name: str):
        # request a list of all experiments within the project
        response = requests.get(self.path + project_name +"/names") # returns experiment names including config
        exp_names_list = response.json().get("names")
        experiments = []
        for exp_name in exp_names_list: ### return names function returns type none
            experiments.append(self.return_fullexperiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        proj_dict = json.loads(response.json()) # conversion into dict
        
        project = d.Project(name=proj_dict.get("name"),author=proj_dict.get("author") ,groups=experiments ,meta=proj_dict.get("meta") )
        return project

    def check_project_exists(self,project_name : str):
        response = requests.get(self.path+ "names") # returns a list of strings
        names = response.json().get("names")
        if project_name in names:
            return True
        else:
            return False

    def check_experiment_exists(self, project_name: str, experiment_name : str):
        response = requests.get(self.path + project_name +"/names")
        names = response.json().get("names") # may have to json.dumps()
        if experiment_name in names:
            return True
        else:
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
        print("initializing")
        request_body = d.Simple_Request_body(name=project.name,meta=project.meta, author=project.author)
        print("Request body")
        print(request_body)
        response = requests.post(self.path + project.get_name() + "/set_project", json=request_body.convertJSON()) # updates the project variables
        return response

    ### initialize experiment
    def init_experiment(self,project_id ,experiment : d.Experiment):
        #request_body = d.Dataset(name=experiment.get_name(),meta=experiment.get_meta(), data_type="configuration file", data=[])
        #response = requests.post(self.path + project_id + "/" + experiment.get_name() + "/set_experiment", json=request_body.convertJSON()) # updates the experiment variables
        #return response
        dataset_in = d.Dataset(name=experiment.name,data=[],meta=experiment.meta,data_type="configuration file")
        # insert special dataset
        self.insert_dataset(project_name=project_id, experiment_name=experiment.name,dataset_in=dataset_in)

    def check_dataset_exists(self, project_id : str, experiment_id : str, dataset_id : str):
        response = requests.get(self.path + project_id + "/" + experiment_id + "/names")
        response = response.json()
        names = response.get("names")
        if dataset_id in names:
            return True
        else:
            return False

# authentication functions
    def create_user(self, username_in, password_in, email, full_name):
        # generate hash
        hash = return_hash(password=password_in)
        user = d.User(username=username_in, hash_in=hash, email=email, full_name=full_name)
        
        #user_out = json.dumps(user.dict())
        user_out = user.dict()

        # API call to create user
        response = requests.post(self.path + "create_user", json=user_out)
        
        print("status code" + str(response.status_code))
        
        if response.status_code == 200:
            # the user already exists
            return True
        else:
            return False

    def generate_token(self, username, password):
        # if the username and password match return true
        hash_in = return_hash(password)
        credentials = HTTPBasicAuth(username=username ,password=hash_in)
        self.token = requests.post("/generate_token", auth=credentials) # generates token
