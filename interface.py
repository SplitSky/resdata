"""interface.py contains the functions used by the Python interface which is used in the interaction
with the API."""
import hashlib as h
import json
from typing import List
import requests
from fastapi import status
import datastructure as d

def return_hash(password: str):
    """ Hash function used by the interface. It is used to only send hashes and not plain passwords."""

    temp = h.shake_256()
    temp.update(password.encode('utf8'))
    return temp.hexdigest(64)


class API_interface:
    """ The Class containing the interface functions and variables. """
    def __init__(self, path_in: str) -> None:
        self.path: str = path_in
        self.token: str = ""
        self.username: str = ""

    def check_connection(self) -> bool:
        """Test API connection to the server"""

        response = requests.get(self.path)
        return response.status_code == status.HTTP_200_OK

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_in: d.Dataset) -> None:
        """ The function responsible for an insertion of a dataset. It authenticates the user and verifies the write permission."""
        if self.check_dataset_exists(project_id=project_name, experiment_id=experiment_name, dataset_id=dataset_in.name):
            raise RuntimeError('Project Already exists') # doesn't allow for duplicate names in datasets
        dataset_in.set_credentials(self.username, self.token)
        dataset_in.author = [d.Author(name=self.username,permission="write").dict()]
        requests.post(url=f'{self.path}{project_name}/{experiment_name}/insert_dataset', json=dataset_in.dict())

    def return_full_dataset(self, project_name: str, experiment_name: str, dataset_name: str): #-> d.Dataset | None:
        """ The function responsible for returning a dataset. It authenticates the user and verifies the read permission. """
        user_in = d.User(username=self.username, hash_in=self.token)
        response = requests.post(
            url=self.path + project_name + "/" + experiment_name + "/" + dataset_name + "/return_dataset",
            json=user_in.dict())
        # TODO: Add handling of empty return. -> remember that it will never be empty -> probably just remove the comment
        temp = json.loads(response.json())
        if temp.get("message") == None:
            # the database was found
            return d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),
                         data_type=temp.get("data_type"), author=temp.get("author"))
        else:
            return None

    def insert_experiment(self, project_name: str, experiment: d.Experiment) -> List:
        """ The function which utilises insert_dataset to recursively insert a full experiment and initialise it if it doesn't exist. """
        experiment_name = experiment.name
        if not self.check_experiment_exists(project_name, experiment_name):
            self.init_experiment(project_name, experiment)
        # init the experiment
        response = []
        
        for dataset in experiment.children:
            if not self.check_dataset_exists(project_name, experiment_name, dataset.name):
                response.append(self.insert_dataset(project_name, experiment_name, dataset))
        
        return response

    def return_full_experiment(self, project_name: str, experiment_name: str) -> d.Experiment:
        """ It returns an Experiment object containing the data within the database. """
        response = requests.get(
            self.path + project_name + "/" + experiment_name + "/names")
        names_list = response.json().get("names")
        datasets = []

        exp_name = "default"
        exp_meta = ["default"]
        print("names list")
        print(names_list)
        for name in names_list:
            temp = self.return_full_dataset(project_name=project_name, experiment_name=experiment_name,
                                            dataset_name=name)
            print("Response from return_full_dataset ")
            print(temp)
            if temp != None:
                if temp.data_type == "configuration file":
                    # update experiment parameters
                    exp_name = temp.name
                    exp_meta = temp.meta
                else:
                    datasets.append(self.return_full_dataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name))
        # call api for each dataset and return the contents -> then add the contents to an object and return the object
        return d.Experiment(name=exp_name, children=datasets, meta=exp_meta)


    def return_full_project(self, project_name: str):
        """ Utilises the return_experiment function to recursively return the entire project that the user has a permission to view. """
        # check the project exists if not raise error
        if not self.check_project_exists(project_name=project_name):
            raise RuntimeError("The project requested doesn't exist")

        # request a list of all experiments within the project
        response = requests.get(self.path + project_name + "/names")  # returns experiment names including config
        exp_names_list = response.json()
        experiments = []
        for exp_name in exp_names_list:
            experiments.append(self.return_full_experiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        proj_dict = json.loads(response.json())  # conversion into dict

        return d.Project(name=proj_dict.get("name"), author=proj_dict.get("author"), groups=experiments,
                            meta=proj_dict.get("meta"), creator=proj_dict.get("creator"))

    def check_project_exists(self, project_name: str):
        """ Function which returns True if a project exists and False if it doesn't. """
        user_in = d.Author(name=self.username ,permission="none")
        response = requests.get(self.path + "names", json=user_in.dict())  # returns a list of strings
        names = response.json().get("names")
        if names is not None and project_name in names:
            return True
        else:
            return False

    def check_experiment_exists(self, project_name: str, experiment_name: str):
        """ Function which returns True if an experiment exists and False if it doesn't. """
        response = requests.get(self.path + project_name + "/names")
        names = response.json()
        return experiment_name in names

    def insert_project(self, project: d.Project):
        """ Function which inserts project recursively using the insert_experiment function. """
        response_out = []
        # set project in database
        # check if project exists. If not initialise it 
        if self.check_project_exists(project_name=project.name):
            raise RuntimeError('Project Already exists')
        self.init_project(project)

        temp = project.groups
        if temp is not None:
            for experiment in temp:
                response_out.append(self.insert_experiment(project.name, experiment))
        return response_out


    def get_project_names(self):
        """ Returns the list of project names - Lists databases except admin, local and Authentication. """
        response = requests.get(self.path + "names")
        project_list = response.json()  # this returns a python dictionary
        return project_list.get("names")

    # initialize project
    def init_project(self, project: d.Project):
        """ Project initialisation function. Assigns the variables to the configuration file in the database. """
        request_body = d.Simple_Request_body(name=project.name, meta=project.meta,creator=project.creator, author=project.author)
        response = requests.post(self.path + project.name + "/set_project",
                                 json=request_body.dict())  # updates the project variables
        return response

    # initialize experiment
    def init_experiment(self, project_id: str, experiment: d.Experiment) -> None:
        """Initialize a new experiment. Append a configuration file to the experiment collection. """
        if self.check_experiment_exists(project_id, experiment.name):
            raise KeyError(f"Experiment '{project_id}/{experiment.name}' exists")
        dataset_in = d.Dataset(name=experiment.name, data=[],
                               meta=experiment.meta,
                               data_type="configuration file",
                               author=[d.Author(name=self.username, permission="write").dict()])
        # insert special dataset
        self.insert_dataset(project_name=project_id, experiment_name=experiment.name, dataset_in=dataset_in)

    def check_dataset_exists(self, project_id: str, experiment_id: str, dataset_id: str) -> bool:
        """ Checks whether a dataset of a given name exists in the specified location """
        response = requests.get(self.path + project_id + "/" + experiment_id + "/names")
        return dataset_id in response.json().get("names")

    # authentication functions
    def create_user(self, username_in, password_in, email, full_name):
        """ Creates a user and adds the user's entries to the Authentication database. """
        # generate hash
        user_hash = return_hash(password=password_in)
        user = d.User(username=username_in, hash_in=user_hash, email=email, full_name=full_name)
        # user_out = json.dumps(user.dict())
        user_out = user.dict()
        # API call to create user
        response = requests.post(self.path + "create_user", json=user_out)
        if response.status_code == 200:
            # the user already exists
            return True
        else:
            return False

    def generate_token(self, username, password):
        """ Generates the authentication jwt token used for interacting with the database. """
        # generates the token for the session and allows for further interaction with the database
        hash_in = return_hash(password)
        self.username = username
        credentials = d.User(username=username, hash_in=hash_in)
        response = requests.post(self.path + "generate_token", json=credentials.dict())  # generates token
        temp = response.json()  # loads json into dict
        self.token = temp.get("access_token")


    def try_authenticate(self):
        # test function
        # send empty database and extract the username and password and give results of authenticate user password
        username = "shmek_the_legend"
        password = "i_like_wombat"
        email = "adwknjhd"
        full_name = "Shmek Johnson"
        self.create_user(username, password, email, full_name)
        self.generate_token(username, password)
        dataset = d.Dataset(name="auth_test", data=[1, 2, 3], meta=["Auth meta"], data_type="testing",
                            author=[d.Author(name="wombat", permission="write").dict()])
        dataset.set_credentials(username, self.token)

        response = requests.post(self.path + "testing_stuff", json=dataset.dict())
        return response
