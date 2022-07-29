# interface - to connect to the remote API

import json  # Required to pass data
import requests  # Base for REST communications
import datastructure as d  # defined datastructures for communication
import logging

import testing as t  # this import should be removed for deployment

# Connect to logger
log = logging.getLogger()


class API_interface:
    def __init__(self, path_in: str) -> None:
        """Base http path for API"""
        self.path = path_in

    def check_connection(self) -> bool:
        """Simple test of connectivity against endpoint"""
        return requests.get(self.path) == 200

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_in: d.Dataset) -> bool:
        """Build a REST request using project name, experiment name etc and insert a dataset"""

        # Try-except for conversion
        try:
            json_payload = dataset_in.convertJSON()
        except BaseException as E:
            raise E

        # Try-except for request
        try:
            response = requests.post(url=self.path + project_name + "/" + experiment_name + "/" + dataset_in.get_name(),
                                     json=json_payload)
        except BaseException as E:
            raise E
        # Log request
        log.info(f"Inserting single dataset- response code: {response}")
        log.info(response.json())
        # Return response code
        return response == 200

    def get_dataset(self, project_name: str, experiment_name: str, dataset_name: str) -> d.Dataset:
        """Retrieve a dataset specified by a project and experiment name"""
        # Build path and make request
        try:
            response = requests.get(url=self.path + project_name + "/" + experiment_name + "/" + dataset_name)
        except BaseException as E:
            raise E
        # Log outcome
        log.info(f"Retrieving single dataset, response code: {response}")
        log.info("content of the dataset: ")
        log.info(response.json())
        # Convert back to a dictionary
        return_data = json.loads(response.json())
        # Create a dataset from dictionary
        dataset = d.Dataset(name=return_data.get("name"), data=return_data.get("data"), meta=return_data.get("meta"),
                            data_type=return_data.get("data_type"))
        return dataset  # returns an object of DataSet class

    def insert_experiment(self, project_name: str, experiment: d.Experiment) -> bool:
        """Insert a whole experiment, defined as multiple datasets"""
        experiment_name = experiment.get_name()
        # check if experiment exists:
        if not self.check_experiment_exists(project_name, experiment_name):
            # if it doesn't initialise it
            log.info(f'{experiment_name} does not exist, creating it')
            self.init_experiment(project_name, experiment)

        # init the experiment
        response = []
        for dataset in experiment.return_datasets():
            # for each dataset in experiment call API 
            response.append(self.insert_dataset(project_name, experiment_name, dataset))
        # Check response
        return False not in response

    def get_fullExperiment(self, project_name: str, experiment_name: str) -> d.Experiment:
        """Return a full experimental dataset. No filtering"""
        log.info(f"Requesting {self.path}/{project_name}/{experiment_name}")

        # Make request
        try:
            response = requests.get(self.path + project_name + "/names")
        except BaseException as E:
            raise E

        log.info(f'Return type is {type(response.json())}')
        names_list = response.json().get("names")
        # Get datasets via comprehension
        datasets = [self.get_dataset(
            project_name=project_name, experiment_name=experiment_name, dataset_name=name)
            for name in names_list]
        # Fetch project details
        exp_dict = json.loads(requests.get(self.path + project_name + "/" + experiment_name + "/details").json())
        experiment = d.Experiment(name=exp_dict.get("name"), children=datasets, meta=exp_dict.get("meta"))

        return experiment

    def get_fullProject(self, project_name: str) -> d.Project:
        """Return a full project"""
        response = requests.get(self.path + project_name)
        exp_names_list = response.json().get(self.path + "/names")
        log.info(f"Experiment names: {exp_names_list}")
        experiments = [self.get_fullExperiment(project_name, exp_name) for exp_name in exp_names_list]

        response = requests.get(self.path + project_name + "/details")
        proj_dict = response.json()
        project = d.Project(name=proj_dict.get("name"), author=proj_dict.get("author"), groups=experiments,
                            meta=proj_dict.get("meta"))
        return project

    def check_project_exists(self, project_name: str) -> bool:
        response = requests.get(self.path + "names")  # returns a list of strings
        names = response.json().get("names")
        if project_name in names:
            return True
        else:
            log.warning(f"Project {project_name} is not present in the database")
            return False

    def check_experiment_exists(self, project_name: str, experiment_name: str) -> bool:
        response = requests.get(self.path + project_name + "/names")
        names = response.json().get("names")
        if experiment_name in names:
            return True
        else:
            log.warning(f"Experiment {experiment_name} not present in the database")
            return False

    def insert_project(self, project: d.Project):
        response_out = []
        # set project in database
        # check if project exists. If not initialise it 
        if not self.check_project_exists(project_name=project.get_name()):
            self.init_project(project)
        for experiment in project.return_experiments():
            response_out.append(self.insert_experiment(project.get_name(), experiment))
        return response_out

    # two functions to return names of the experiment and the names of the project

    def get_project_names(self):
        return requests.get(self.path + "names").json().get("names")

    # initialize project
    def init_project(self, project: d.Project):
        request_body = d.simpleRequestBody(name=project.get_name(), meta=project.get_meta(),
                                           author=project.get_author())
        response = requests.post(self.path + project.get_name() + "/set_project",
                                 json=request_body.convertJSON())  # updates the project variables
        return response

    # initialize experiment
    def init_experiment(self, project_id, experiment: d.Experiment):
        request_body = d.simpleRequestBody(name=experiment.get_name(), meta=experiment.get_meta(), author="a")
        log.info(f"Request body {request_body}")
        response = requests.post(self.path + project_id + "/" + experiment.get_name() + "/set_experiment",
                                 json=request_body.convertJSON())  # updates the experiment variables
        return response
