"""interface.py contains the functions used by the Python interface which is used in the interaction
with the API."""
import hashlib as h
import json
from typing import List
import requests
from fastapi import status
import server.datastructure as d
from variables import API_key
from PIL import Image
import numpy as np
import sys

from server.security import key_manager # import for development. Split security module into two pieces on deployment

# max size variable
#max_size = 16793598 # bytes
max_size = 6478488


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
        
        # dataset is less than maximum size
        print("check object size")
        #print(self.check_object_size(dataset_in))

        if self.check_object_size(dataset_in):
            # dataset within parameters
            # proceed without fragmentation
            requests.post(url=f'{self.path}{project_name}/{experiment_name}/insert_dataset', json=dataset_in.dict())
            return True
        else:
            print("dataset fragmentation")
            # dataset needs fragmentation
            datasets = self.fragment_datasets(dataset_in)
            responses = []
            print("datasets are fragmented now sending")
            for dataset_temp in datasets:
                print("dataset sent")
                print(dataset_temp.name)
                # insert each dataset
                dataset_temp.set_credentials(self.username, self.token)
                response = requests.post(url=f'{self.path}{project_name}/{experiment_name}/insert_dataset', json=dataset_temp.dict())
                print(response)
                responses.append(response)
            if False in responses:
                return False
            else:
                return True

    def return_full_dataset(self, project_name: str, experiment_name: str, dataset_name: str):  # -> d.Dataset | None:
        """ The function responsible for returning a dataset. It authenticates the user and verifies the read permission. """
        user_in = d.User(username=self.username, hash_in=self.token)
        response = requests.post(
            url=f'{self.path}{project_name}/{experiment_name}/{dataset_name}/return_dataset',
            json=user_in.dict())
        temp = json.loads(response.json())
        print(temp)
        if temp.get("message") == None and temp.get("meta").get("fragmented") != True:
            # the database was found and the data wasn't fragmented
            return d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),
                             data_type=temp.get("data_type"), author=temp.get("author"),
                             data_headings=temp.get("data_headings"))
        elif temp.get("message") == False:
            return False
        # if the dataset is fragmented
        # recollect the dataset
        print("temp")
        print(temp)
        front_dataset = d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),
                        data_type=temp.get("data_type"), author=temp.get("author"),
                        data_headings=temp.get("data_headings"))
        front_dataset = self.collect_frag_data(front_dataset=front_dataset, project_name=project_name, experiment_name=experiment_name, user_in=user_in)
        return front_dataset

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
        # TODO: Add signing to the encryption
        # generate public/private keys
        u = key_manager()
        u.generate_keys()
        private_key, public_key = u.read_keys()
        # fetch API public key
        response = requests.post(self.path + "get_public_key")
        #api_public_key = response["public_key"]
        bytes_out = response.json().get("public_key").encode('utf-8')
        # serialize key into object
        public_key = u.serialize_public_key(bytes_out)
        # generate hash
        user_hash = return_hash(password=password_in)
        #encrypt and sign the entries
        username_in = u.encrypt_message(public_key=public_key,message=username_in)
        user_hash = u.encrypt_message(public_key=public_key, message=user_hash)
        if len(email) > 0:
            email = u.encrypt_message(public_key=public_key, message=email)
        if len(full_name) > 0:
            full_name = u.encrypt_message(public_key=public_key, message=full_name)
        # mage the json object to send
        user = d.User(username=username_in, hash_in=user_hash, email=email, full_name=full_name)
        #assign the tunnel key for the API
        user.tunnel_key = return_hash(password=API_key)
        # user_out = json.dumps(user.dict())
        user_out = user.dict()
        # API call to create user
        response = requests.post(self.path + "create_user" +"/"+ str(public_key), json=user_out)
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
        """Appends a user defined author to an existing dataset. Utility function. Doesn't guarantee user's access to this dataset. Use add_author_to_dataset_rec to guarantee access."""
        if not (type(author_name) == type("string") and type(author_permissions) == type("string")):
            raise Exception("Author name and permission have to be strings")
        # doesn't verify whether the dataset exists because it edits datasets that the user doesn't have access to

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
        # add author to the project to allow for top-down access
        self.add_author_to_project(project_id=project_id, author_name=author_name, author_permission=author_permission)
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

    def add_author_to_dataset_rec(self, project_id: str, experiment_id: str, dataset_id: str, author_name: str,
                                  author_permissions: str):
        """Adds an author to the project,experiment and dataset to enable to access. Uses the utility function add_author_to_dataset"""
        if not (type(author_name) == type("string") and type(author_permissions) == type("string")):
             raise Exception("Author name and permission have to be strings")
    
        # appends the author to the path that leads to this dataset to guarantee access
        self.add_author_to_experiment(project_id=project_id, experiment_id=experiment_id, author_name=author_name, author_permission=author_permissions)
        self.add_author_to_project(project_id=project_id, author_name=author_name,author_permission=author_permissions)

        author_in = d.Author(name=author_name, permission=author_permissions)
        response = requests.post(self.path + project_id + "/" + experiment_id + "/" + dataset_id +"/"+ self.username +"/add_author",
                                 json=author_in.dict())
        if response == status.HTTP_200_OK:
            return True
        else:
            return False


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
        if not (type(author_name) == type("string") and type(author_permission) == type("string")):
            raise Exception("Author name and permission have to be strings")
        # check the dataset exists
        # doesn't verify whether the dataset exists because it edits datasets that the user doesn't have access to
        author_in = d.Author(name=author_name, permission=author_permission)
        response = requests.post(self.path + project_id + "/" + experiment_id + "/" + dataset_id +"/"+ group_name +"/add_group_author",
                                 json=author_in.dict())
        return response.json() 
      
    def add_group_to_experiment(self, project_id: str, experiment_id: str, author_name: str, author_permission: str, group_name: str):
        """Adds the author to the experiment config file"""
        # check project exists
        if not self.check_project_exists(project_name=project_id):
            raise Exception("The project doesn't exist")
        return self.add_group_to_dataset(project_id=project_id, experiment_id=experiment_id, dataset_id=experiment_id,
                                          author_name=author_name, author_permission=author_permission,group_name=group_name)


    def add_group_to_experiment_rec(self, project_id:str, experiment_id:str, author_name:str, author_permission:str, group_name:str):
        """Recursively adds authors for all datasets included within the experiment and the experiment config file."""
        status_temp = True
        temp = self.add_group_to_project(project_id=project_id, author_name=author_name, author_permission=author_permission, group_name=group_name)
        # adds path
        if not temp:
            status_temp = False
        names = self.get_dataset_names(project_id=project_id, experiment_id=experiment_id)
        for name in names:
            #if name != experiment_id:
            #    # filter out experiment config names
            temp = self.add_group_to_dataset(project_id=project_id, experiment_id=experiment_id, dataset_id=name,author_name=author_name, author_permission=author_permission,group_name=group_name)
            if not temp:
                status_temp = False
        return status_temp

    def add_group_to_project(self, project_id: str, author_name: str, author_permission: str, group_name: str):
        # TODO: change author_permission to group_permission
        """Updates the project config file and adds an author"""
        return self.add_group_to_dataset(project_id=project_id, experiment_id='config', dataset_id=project_id,
                                          author_name=author_name, author_permission=author_permission,group_name=group_name)
        
    def add_group_to_project_rec(self, project_id: str, author_name: str, author_permission: str, group_name:str):
        """Recursively adds author to all experiments and datasets in the project specified. """
        status_temp = True
        temp = self.add_group_to_project(project_id=project_id, author_name=author_name, author_permission=author_permission, group_name=group_name)
        if temp == False:
            status_temp = False
        names = self.get_experiment_names(project_id=project_id)
        for name in names:
            temp = self.add_group_to_experiment(project_id=project_id, experiment_id=name, author_name=author_name,
                                                  author_permission=author_permission, group_name=group_name)
            # recursively adds groups to all datasets
            if temp == False:
                status_temp = False
            # recursively appends the author to each dataset
            dataset_names = self.get_dataset_names(project_id=project_id, experiment_id=name)
            for name2 in dataset_names:
                if name2 != name: # filters out experiment config files
                    temp = self.add_group_to_dataset(author_name=author_name, author_permission=author_permission, group_name=group_name, project_id=project_id, experiment_id=name, dataset_id=name2 )
                    if temp == False:
                        status_temp = False
        return status_temp
   
    def add_group_to_dataset_rec(self, author_permission:str, author_name:str, group_name:str, project_id:str, experiment_id:str, dataset_id:str):
        """Adds an group to the project,experiment and dataset to enable to access. Uses the utility function add_group_to_dataset"""
        if not (type(author_name) == type("string") and type(author_permission) == type("string")):
             raise Exception("Author name and permission have to be strings")
    
        # appends the author to the path that leads to this dataset to guarantee access
        responses = []
        if not self.check_dataset_exists(project_id=project_id, experiment_id=experiment_id, dataset_id=dataset_id):
            raise Exception("The dataset doesn't exist")
        responses.append(self.add_group_to_dataset(author_permission=author_permission, author_name=author_name, project_id=project_id, experiment_id=experiment_id, dataset_id=dataset_id, group_name=group_name))
        # create path to dataset recursively
        responses.append(self.add_group_to_project(project_id=project_id, author_name=author_name,author_permission=author_permission, group_name=group_name))
        responses.append(self.add_group_to_experiment(project_id=project_id, experiment_id=experiment_id, author_name=author_name, author_permission=author_permission, group_name=group_name))
        if False in responses:
            return False
        else:
            return True

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
        for proj_name in proj_names:
            # loop over the project names
            exp_names = self.get_experiment_names_group(project_id=proj_name,group_name=username)
            temp_exp = []
            for exp_name in exp_names:

                temp_data = []
                dat_names = self.get_dataset_names_group(project_id=proj_name, experiment_id=exp_name, group_name=username)
                for dat_name in dat_names:
                    if exp_name != dat_name:
                        # avoids returning the config dataset for experiment
                        temp_data.append(dat_name)
                    
                temp_exp.append({"experiment_id": exp_name, "dataset_list" : temp_data})            
            temp_proj = {"project_id": proj_name, "experiment_list":temp_exp}
            names_list.append(temp_proj)
        return names_list

        
    def tree_print_group(self, group_name: str):
        structure = self.author_query(group_name)
        for project in structure:
            print(project.get("project_id"))
            for experiment in project.get("experiment_list"):
                print("     -> " + experiment.get("experiment_id"))
                for dataset in experiment.get("dataset_list"):
                    print("         --> " + dataset)

    def convert_img_to_array(self, filename: str):
        # TODO: Add path variable and allow for custom folders
        img = Image.open("images/"+filename)
        arraydata = np.asarray(img)
        arraydata = arraydata.tolist()
        #return np.array(img).tolist() # TODO: Very lazy. Fix this
        #print(arraydata)
        #print("type")
        #print(type(arraydata))
        return arraydata

    def convert_array_to_img(self, array: list, filename: str):
        # converts an array into an image and saves in the script dicrectory
        img = Image.fromarray(np.array(array))
        try:
            img.save("images/"+filename)
            return True
        except:
            return False
    def check_object_size(self, object: d.Dataset):
        # Returns True if the dataset has size that doesn't exceeds max size
        temp = object.json()
        size = sys.getsizeof(json.dumps(temp))
        print(f'size: {size}')
        if size >= max_size:
            return False
        else:
            return True

    def slice_array(self, array: list):
            # split into 2
            half_point = len(array) // 2
            arr1 = array[:half_point]
            arr2 = array[half_point+1:]
            return [arr1, arr2]

    def fragment_datasets(self, dataset: d.Dataset) -> List[d.Dataset]:
        # Fragment the dataset
        # linking by meta_data variable -> "fragmented: True"
        # -> "fragmented_id: int"

        # check the dataset needs to be fragmented
        if not self.check_object_size(object=dataset):
            # modify the metadata by adding the "fragmented" entry
            if dataset.meta != None:
                dataset.meta["fragmented"] = True
            else:
                dataset.meta = {"fragmented" : True}
            # continue with data fragmentation
        else:
            return [dataset]

        # generate first dataset
        front_dataset = d.Dataset(name=dataset.name, data=[0], meta=dataset.meta, data_type=dataset.data_type, username=dataset.username, token=dataset.token, data_headings=dataset.data_headings, author=dataset.author)

        datasets = [dataset]
        # while the object exceeds maximum size split into two. Do as many times as necessary
        while not self.check_object_size(object=datasets[0]):
            fragments = [] # stores the segmented arrays
            datasets_temp = [] # stores the segmented datasets
            for entry in datasets:
                arr1, arr2 = self.slice_array(entry.data)
                fragments.append(arr1)
                # TODO: Check if fragments is needed
                fragments.append(arr2)
                # recombine the datasets
                temp = d.Dataset(name=dataset.name + "- part", data=arr1, meta=None, data_type=dataset.data_type, data_headings=dataset.data_headings, author=[])
                datasets_temp.append(temp)
                temp = d.Dataset(name=dataset.name + "- part", data=arr2, meta=None, data_type=dataset.data_type, data_headings=dataset.data_headings, author=[])
                datasets_temp.append(temp)
                # don't assign author to keep the dataset hidden
            #end for
            datasets = datasets_temp
        # data fragmented enough for storage
        # populate the front dataset
        front_dataset.data = datasets[0].data
        datasets.pop(0)
        if front_dataset.meta == None:
            front_dataset.meta = {"fragmented" : True, "number_of_fragments" : len(datasets)}
        else:
            front_dataset.meta["number_of_fragments"] = len(datasets)
        # add the meta data variable fragmented id number
        i = 0
        for entry in datasets:
            entry.name = front_dataset.name + "-part " + str(i)
            if entry.meta == None:
                entry.meta = {"fragment_id" : i, "parent_dataset" : front_dataset.name}
            else:
                entry.meta["fragment_id"] = i
                entry.meta["parent_dataset"] = front_dataset.name
            i += 1

        # append the front dataset
        datasets.insert(0,front_dataset)
        # return the datasets
        return datasets

    def collect_frag_data(self, front_dataset : d.Dataset,user_in : d.User ,project_name, experiment_name) -> d.Dataset:
        # get the names of the datasets by using meta search
        
        # API call to retrieve the full list of names
        response = requests.post(f'{self.path}{project_name}/{experiment_name}/{front_dataset.name}/collect_fragments_names', json=user_in.dict())
        response = response.json()
        response = requests.get(self.path + "names_group", json=user_in.dict())
        
        names = response.json()
        print(f'names: {names}')
        data_to_append = []
        
        for name in names:
            dataset = self.return_full_dataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name)
            if dataset != None:
                data_to_append.append(dataset.data)
        full_data = []
        # TODO: make sure the fragments are sorted in the right order
        for entry in data_to_append:
            full_data += entry

        # append data 
        front_dataset.data = full_data

        return front_dataset
