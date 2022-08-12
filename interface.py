import hashlib as h
import json
import requests
from fastapi import status
import datastructure as d


###############################
# hash function used in the API
def return_hash(password: str):
    # this function only hashes the password for sending purposes
    temp = h.shake_256()
    temp.update(password.encode('utf8'))
    return temp.hexdigest(64)


###############################
class API_interface:

    def __init__(self, path_in: str) -> None:
        self.path: str = path_in
        self.token: str = ""
        self.username: str = ""

    def check_connection(self):
        """Test API connection to the server"""
        response = requests.get(self.path)
        return response.status_code == status.HTTP_200_OK

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_in: d.Dataset):
        # set credentials for authentication
        dataset_in.set_credentials(self.username, self.token)
        dataset_in.author = [d.Author(name=self.username,
                                      permission="write").dict()]
        return requests.post(url=f'{self.path}{project_name}/{experiment_name}/{dataset_in.get_name()}/insert_dataset',
                             json=dataset_in.dict())

    def return_full_dataset(self, project_name: str, experiment_name: str, dataset_name: str):
        user_in = d.User(username=self.username, hash_in=self.token)
        response = requests.post(
            url=self.path + project_name + "/" + experiment_name + "/" + dataset_name + "/return_dataset",
            json=user_in.dict())
        temp = response.json().get("datasets data")[0]
        return d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),
                         data_type=temp.get("data_type"), author=temp.get("author"))

    def insert_experiment(self, project_name: str, experiment: d.Experiment):
        # takes in the experiment object 
        # perform multiple calls to create an experiment directory and then
        # insert datasets one by one
        experiment_name = experiment.get_name()
        # check if experiment exists:
        if not self.check_experiment_exists(project_name, experiment_name):
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

    def return_full_experiment(self, project_name: str, experiment_name: str):
        # call api to find the names of all datasets in the experiment
        # return the list of datasets
        response = requests.get(
            self.path + project_name + "/" + experiment_name + "/names")
        names_dict = response.json()
        names_list = names_dict.get("names")
        datasets = []

        exp_name = "default"
        exp_meta = ["default"]

        for name in names_list:
            temp = self.return_full_dataset(project_name=project_name, experiment_name=experiment_name,
                                            dataset_name=name)
            if temp.get_datatype() == "configuration file":
                # update experiment parameters
                exp_name = temp.name
                exp_meta = temp.meta
            else:
                datasets.append(self.return_full_dataset(project_name=project_name, experiment_name=experiment_name,
                                                         dataset_name=name))
        # call api for each dataset and return the contents -> then add the contents to an object and return the object

        experiment = d.Experiment(name=exp_name, children=datasets, meta=exp_meta)
        return experiment

    def return_full_project(self, project_name: str):
        # request a list of all experiments within the project
        response = requests.get(self.path + project_name + "/names")  # returns experiment names including config
        exp_names_list = response.json().get("names")
        experiments = []
        for exp_name in exp_names_list:
            experiments.append(self.return_full_experiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        proj_dict = json.loads(response.json())  # conversion into dict

        project = d.Project(name=proj_dict.get("name"), author=proj_dict.get("author"), groups=experiments,
                            meta=proj_dict.get("meta"))
        return project

    def check_project_exists(self, project_name: str):
        response = requests.get(self.path + "names")  # returns a list of strings
        names = response.json().get("names")
        if project_name in names:
            return True
        else:
            return False

    def check_experiment_exists(self, project_name: str, experiment_name: str):
        response = requests.get(self.path + project_name + "/names")
        names = response.json().get("names")  # may have to json.dumps()
        if experiment_name in names:
            return True
        else:
            return False

    def insert_project(self, project: d.Project):
        response_out = []
        # set project in database
        # check if project exists. If not initialise it 
        if self.check_project_exists(project_name=project.get_name()):
            raise RuntimeError('Project Already exists')
        self.init_project(project)

        temp = project.return_experiments()
        if temp is not None:
            for experiment in temp:
                response_out.append(self.insert_experiment(project.get_name(), experiment))
        return response_out

    # two functions to return names of the experiment and the names of the project

    def get_project_names(self):
        response = requests.get(self.path + "names")
        project_list = response.json()  # this returns a python dictionary
        return project_list.get("names")

    # initialize project
    def init_project(self, project: d.Project):
        request_body = d.Simple_Request_body(name=project.name, meta=project.meta, author=project.author)
        response = requests.post(self.path + project.get_name() + "/set_project",
                                 json=request_body.convertJSON())  # updates the project variables
        return response

    # initialize experiment
    def init_experiment(self, project_id: str, experiment: d.Experiment) -> None:
        # insert dataset function validates as it is the only function which inserts things into the database.
        # Author data is just the username and the permission of the user entering it
        # TODO: Check if experiment already exists
        dataset_in = d.Dataset(name=experiment.name, data=[],
                               meta=experiment.meta,
                               data_type="configuration file",
                               author=[d.Author(name=self.username, permission="write").dict()])
        # insert special dataset
        self.insert_dataset(project_name=project_id, experiment_name=experiment.name, dataset_in=dataset_in)

    def check_dataset_exists(self, project_id: str, experiment_id: str, dataset_id: str):
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
        user_hash = return_hash(password=password_in)
        user = d.User(username=username_in, hash_in=user_hash, email=email, full_name=full_name)

        # user_out = json.dumps(user.dict())
        user_out = user.dict()

        # API call to create user
        response = requests.post(self.path + "create_user", json=user_out)
        return response.status_code == 200

    def generate_token(self, username, password):
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
        print(dataset.json())

        response = requests.post(self.path + "testing_stuff", json=dataset.dict())
        return response
