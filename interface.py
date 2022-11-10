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

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_in: d.Dataset) -> bool:
        """ The function responsible for an insertion of a dataset. It authenticates the user and verifies the write permission."""

        if self.check_dataset_exists(project_id=project_name, experiment_id=experiment_name,
                                     dataset_id=dataset_in.name):
            raise RuntimeError('Dataset Already exists')  # doesn't allow for duplicate names in datasets
        dataset_in.set_credentials(self.username, self.token)
        dataset_in.author = [d.Author(name=self.username, permission="write").dict()]
        requests.post(url=f'{self.path}{project_name}/{experiment_name}/insert_dataset', json=dataset_in.dict())
        return True

    def return_full_dataset(self, project_name: str, experiment_name: str, dataset_name: str):  # -> d.Dataset | None:
        """ The function responsible for returning a dataset. It authenticates the user and verifies the read permission. """
        user_in = d.User(username=self.username, hash_in=self.token)
        response = requests.post(
            url=self.path + project_name + "/" + experiment_name + "/" + dataset_name + "/return_dataset",
            json=user_in.dict())
        temp = json.loads(response.json())
        if temp.get("message") == None:
            # the database was found
            return d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),
                             data_type=temp.get("data_type"), author=temp.get("author"),
                             data_headings=temp.get("data_headings"))
        else:
            return None

    def insert_experiment(self, project_name: str, experiment: d.Experiment) -> bool:
        """ The function which utilises insert_dataset to recursively insert a full experiment and initialise it if it doesn't exist. """
        experiment_name = experiment.name
        if not self.check_experiment_exists(project_name, experiment_name):
            self.init_experiment(project_name, experiment)
        # init the experiment
        response = []
        for dataset in experiment.children:
            if not self.check_dataset_exists(project_name, experiment_name, dataset.name):
                response.append(self.insert_dataset(project_name, experiment_name, dataset))
        if False in response:
            return False
        else:
            return True

    def return_full_experiment(self, project_name: str, experiment_name: str) -> d.Experiment:
        """ It returns an Experiment object containing the data within the database. """
        names_list = self.get_dataset_names(project_id=project_name, experiment_id=experiment_name)
        datasets = []
        exp_name = "default"
        exp_meta = {"note":"default"}
        exp_author = [{"name": "default", "permission": "none"}]

        for name in names_list:
            temp = self.return_full_dataset(project_name=project_name, experiment_name=experiment_name,
                                            dataset_name=name)
            if temp != None:
                if temp.data_type == "configuration file":
                    # update experiment parameters
                    exp_name = temp.name
                    exp_meta = temp.meta
                    exp_author = temp.author
                else:
                    datasets.append(self.return_full_dataset(project_name=project_name, experiment_name=experiment_name,
                                                             dataset_name=name))
        # call api for each dataset and return the contents -> then add the contents to an object and return the object
        return d.Experiment(name=exp_name, children=datasets, meta=exp_meta, author=exp_author)

    def return_full_project(self, project_name: str):
        """ Utilises the return_experiment function to recursively return the entire project that the user has a permission to view. """
        # check the project exists if not raise error
        if not self.check_project_exists(project_name=project_name):
            raise RuntimeError("The project requested doesn't exist")

        # request a list of all experiments within the project
        exp_names_list = self.get_experiment_names(project_id=project_name)

        experiments = []
        for exp_name in exp_names_list:
            experiments.append(self.return_full_experiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        proj_dict = json.loads(response.json())  # conversion into dict

        return d.Project(name=proj_dict.get("name"), author=proj_dict.get("author"), groups=experiments,
                         meta=proj_dict.get("meta"), creator=proj_dict.get("creator"))

    def check_project_exists(self, project_name: str):
        """ Function which returns True if a project exists and False if it doesn't. """
        if len(project_name) == 0:
            raise Exception("Project name cannot have no size")
        names_list = self.get_project_names()
        return project_name in names_list

    def check_experiment_exists(self, project_name: str, experiment_name: str):
        """ Function which returns True if an experiment exists and False if it doesn't. """
        if len(project_name) == 0 or len(experiment_name) == 0:
            raise Exception("Project or Experiment name have no size")
        names_list = self.get_experiment_names(project_id=project_name)
        return experiment_name in names_list

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

        if False in response_out:
            return False
        else:
            return True
    # initialize project
    def init_project(self, project: d.Project):
        """ Project initialisation function. Assigns the variables to the configuration file in the database. """
        request_body = d.Simple_Request_body(name=project.name, meta=project.meta, creator=project.creator,
                                             author=project.author)
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
                               author=[d.Author(name=self.username, permission="write").dict()],
                               data_headings=["experiment_metadata"])
        # insert special dataset
        self.insert_dataset(project_name=project_id, experiment_name=experiment.name, dataset_in=dataset_in)

    def check_dataset_exists(self, project_id: str, experiment_id: str, dataset_id: str) -> bool:
        """ Checks whether a dataset of a given name exists in the specified location """
        if len(project_id) == 0 or len(experiment_id) == 0 or len(dataset_id) == 0:
            raise Exception("One of the variables has size zero")
        names_list = self.get_dataset_names(project_id=project_id, experiment_id=experiment_id)
        return dataset_id in names_list

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
        dataset = d.Dataset(name="auth_test", data=[1, 2, 3], meta={"note" : "Auth meta"}, data_type="testing",
                            author=[d.Author(name="wombat", permission="write").dict()], data_headings=["test_heading"])
        dataset.set_credentials(username, self.token)
        response = requests.post(self.path + "testing_stuff", json=dataset.dict())
        return response

    def get_experiment_names(self, project_id: str):
        user_in = d.Author(name=self.username, permission="none")
        response = requests.get(self.path + project_id + "/names", json=user_in.dict())
        return response.json().get("names")

    def get_dataset_names(self, project_id: str, experiment_id: str):
        user_in = d.Author(name=self.username, permission="none")
        response = requests.get(self.path + project_id + "/" + experiment_id + "/names", json=user_in.dict())
        return response.json().get("names")

    def get_project_names(self):
        """ Returns the list of project names - Lists databases except admin, local and Authentication. """
        user_in = d.Author(name=self.username, permission="none")
        response = requests.get(self.path + "names", json=user_in.dict())
        project_list = response.json()  # this returns a python dictionary
        return project_list.get("names")

    def tree_print(self):
        """Returns the names of all the projects/experiments/datasets the user has access to."""
        if self.username == "":
            raise Exception("The user needs to be authenticated first")
        print("The data tree:")
        proj_names = self.get_project_names()
        if proj_names == None:
            raise Exception("The user has no projects.")
        for name in proj_names:
            print(name)
            exp_names = self.get_experiment_names(name)
            for name2 in exp_names:
                print("     ->" + name2)
                dat_names = self.get_dataset_names(project_id=name, experiment_id=name2)
                for name3 in dat_names:
                    if name3 != name2:
                        print("         -->" + name3)

    def add_author_to_dataset(self, project_id: str, experiment_id: str, dataset_id: str, author_name: str,
                              author_permissions: str):
        """Appends a user defined author to an existing dataset"""
        # TODO: add authentication of variable types
        if not (type(author_name) == type("string") and type(author_permissions) == type("string")):
            raise Exception("Author name and permission have to be strings")
        # check the dataset exists
        # doesn't verify whether the dataset exists because it edits datasets that the user doesn't have access to
        
        # verify the project and experiment exists
        if self.check_project_exists(project_name=project_id) == False:
            raise Exception("Project with that name doesn't exist")
        if self.check_experiment_exists(project_name=project_id, experiment_name=experiment_id) == False:
            raise Exception("Experiment with that name doesn't exist")

        # add project author
        self.add_author_to_project(project_id=project_id, author_name=author_name, author_permission=author_permissions)
        # add experiment author
        self.add_author_to_experiment(project_id=project_id, experiment_id=experiment_id, author_name=author_name, author_permission=author_permissions)

        author_in = d.Author(name=author_name, permission=author_permissions)
        response = requests.post(self.path + project_id + "/" + experiment_id + "/" + dataset_id +"/"+ self.username +"/add_author",
                                 json=author_in.dict())
        if response == status.HTTP_200_OK:
            return True
        else:
            return False

    def add_author_to_experiment(self, project_id: str, experiment_id: str, author_name: str, author_permission: str):
        """Adds the author to the experiment config file"""
        # check project exists
        if not self.check_project_exists(project_name=project_id):
            raise Exception("The project doesn't exist")
        
        return self.add_author_to_dataset(project_id=project_id, experiment_id=experiment_id, dataset_id=experiment_id,
                                          author_name=author_name, author_permissions=author_permission)

    def add_author_to_experiment_rec(self, project_id, experiment_id, author_name, author_permission):
        """Recursively adds authors for all datasets included within the experiment and the experiment config file."""
        names = self.get_dataset_names(project_id=project_id, experiment_id=experiment_id)
        responses = []
        for name in names:
            responses.append(
                self.add_author_to_dataset(project_id=project_id, experiment_id=experiment_id, dataset_id=name,
                                           author_name=author_name, author_permissions=author_permission))
        if False in responses:
            return False
        else:
            return True

    def add_author_to_project(self, project_id: str, author_name: str, author_permission: str):
        """Updates the project config file and adds an author"""
        return self.add_author_to_dataset(project_id=project_id, experiment_id='config', dataset_id=project_id,
                                          author_name=author_name, author_permissions=author_permission)

    def add_author_to_project_rec(self, project_id: str, author_name: str, author_permission: str):
        """Recursively adds author to all experiments and datasets in the project specified. """
        self.add_author_to_project(project_id=project_id, author_name=author_name, author_permission=author_permission)
        names = self.get_experiment_names(project_id=project_id)
        responses = []
        for name in names:
            responses.append(
                self.add_author_to_experiment_rec(project_id=project_id, experiment_id=name, author_name=author_name,
                                                  author_permission=author_permission))
            # recursively appends the author to each dataset
        if False in responses:
            return False
        else:
            return True

    def purge_everything(self):
        requests.post(self.path +"purge")
        print("purged")

    def experiment_search_meta(self, meta_search : dict, experiment_id : str, project_id : str):
        """Fetches the datasets matching the meta variables"""
        # API call - experiment level - returning the names of datasets that match
        # Check that the project and experiment exist
        if len(experiment_id) == 0 or len(project_id) == 0:
            raise Exception("The variables provided are size zero")
        response = self.check_project_exists(project_name=project_id)
        if response == False:
            raise Exception("The project doesn't exist")
        response = self.check_experiment_exists(project_name=project_id, experiment_name=experiment_id)
        if response == False:
            raise Exception("The experiment doesn't exist")

        author_temp = d.Author(name=self.username ,permission="write")
        dataset = d.Dataset(name="search request body", data=[], meta=meta_search, data_type="search", author=[author_temp.dict()], data_headings=[])
        dataset.set_credentials(self.username, self.token)
        response = requests.get(self.path + project_id + "/" + experiment_id + "/meta_search", json=dataset.dict())
        names = response.json()
        names = names.get("names")
        datasets = []
        for name in names:
            datasets.append(self.return_full_dataset(project_name=project_id, experiment_name=experiment_id, dataset_name=name))
        return datasets

# group management functions to be tested

    # Note: Do not append groups to individual datasets unless you already appended it to the experiment and project. Otherwise it won't be returned
    def add_group_to_dataset(self, author_permission:str, author_name:str, group_name:str, project_id:str, experiment_id:str, dataset_id:str):
        """Appends a group to an existing dataset"""
        # TODO: add authentication of variable types
        if not (type(author_name) == str and type(author_permission) == str and type(group_name) == str):
            raise Exception("Author name and permission have to be strings")
        
        author_in = d.Author(name=author_name, permission=author_permission)
        response = requests.post(self.path + project_id + "/"+experiment_id+"/"+dataset_id+"/"+group_name + "/add_group_author",
                                 json=author_in.dict())
        if response == status.HTTP_200_OK:
            return True
        else:
            return False

    def add_group_to_experiment(self, project_id: str, experiment_id: str, author_name: str, author_permission: str, group_name: str):
        """Adds the author to the experiment config file"""
        return self.add_group_to_dataset(project_id=project_id, experiment_id=experiment_id, dataset_id=experiment_id,
                                          author_name=author_name, author_permission=author_permission, group_name=group_name)

    def add_group_to_experiment_rec(self, project_id:str, experiment_id:str, author_name:str, author_permission:str, group_name:str):
        """Recursively adds authors for all datasets included within the experiment and the experiment config file."""
        names = self.get_dataset_names(project_id=project_id, experiment_id=experiment_id)
        responses = []
        for name in names:
            responses.append(
                self.add_group_to_dataset(project_id=project_id, experiment_id=experiment_id, dataset_id=name,
                                           author_name=author_name, author_permission=author_permission,group_name=group_name))
        if False in responses:
            return False
        else:
            return True

    def add_group_to_project(self, project_id: str, author_name: str, author_permission: str, group_name: str):
        """Updates the project config file and adds an author"""
        return self.add_group_to_dataset(project_id=project_id, experiment_id='config', dataset_id=project_id,
                                          author_name=author_name, author_permission=author_permission, group_name=group_name)

    def add_group_to_project_rec(self, project_id: str, author_name: str, author_permission: str, group_name:str):
        """Recursively adds author to all experiments and datasets in the project specified. """
        names = self.get_experiment_names(project_id=project_id)
        responses = []

        for name in names:
            responses.append(
                self.add_group_to_experiment_rec(project_id=project_id, experiment_id=name, author_name=author_name,
                                                  author_permission=author_permission, group_name=group_name))
            # recursively appends the author to each dataset
        if False in responses:
            return False
        else:
            return True

# group adding functions to be tested

###################################################################################################################################################    406
    # the group functions two



# group /names functions
    def get_experiment_names_group(self, project_id: str, group_name: str):
        """Function returning the names that are part of a group with the specified group_name and the auther has access to"""
        user_in = d.Author(name=self.username, permission="none", group_name=group_name)
        response = requests.get(self.path + project_id + "/names_group", json=user_in.dict())
        return response.json().get("names")

    def get_dataset_names_group(self, project_id: str, experiment_id: str, group_name: str):
        """Function returning the names that are part of a group with the specified group_name and the auther has access to"""
        user_in = d.Author(name=self.username, permission="none", group_name=group_name)
        response = requests.get(self.path + project_id + "/" + experiment_id + "/names_group", json=user_in.dict())
        return response.json().get("names")

    def get_project_names_group(self, group_name: str):
        """ Returns the list of project names belonging to the group with the specified group name - Lists databases except admin, local and Authentication. """
        user_in = d.Author(name=self.username, permission="none", group_name=group_name)
        response = requests.get(self.path + "names_group", json=user_in.dict())
        project_list = response.json()  # this returns a python dictionary
        return project_list.get("names")



# group call function
# employs the /names functions to recall every dataset/experiment/project that is a member of the group
    def author_query(self, username: str):
        """Return the names list with the specified author. Authenticates for the current user.
        Group query. Returns a list of projects within the group
        the return is configured in the following way: 
        [{project_name : str, exp_list: [{exp_name: str, dataset_list: [] }]}]
        """
        names_list = []
        temp_exp = []
        temp_data = []

        if self.username == "":
            raise Exception("The user needs to be authenticated first")
        proj_names = self.get_project_names_group(group_name=username)
        if proj_names == None:
            raise Exception("The user has no projects.")
        for name in proj_names:
            exp_names = self.get_experiment_names_group(name,group_name=username)
            for name2 in exp_names:
                temp_exp = []
                dat_names = self.get_dataset_names_group(project_id=name, experiment_id=name2, group_name=username)
                for name3 in dat_names:
                    temp_data = []
                    if name3 != name2:
                        temp_data.append(name3)
                temp_exp.append({"experiment_id": name2, "dataset_list" : temp_data})            
            temp_proj = {"project_id": name, "experiment_list":[]}
            names_list.append(temp_proj)
        return names_list



