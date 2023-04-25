import interface as i
import testing as t
import datastructure as d
from typing import Union, List, Dict
import data_handle as dh

"""This class allows the user to compose datasets and then sync them with the online database"""

class User_Interface:
    def __init__(self, path):
        self.username = ""
        self.password = ""
        self.projects = {}
        self.api = i.API_interface(path_in=path, user_cache=True)
        self.exp_index = 0

    def user_authenticate(self,username, password):
        self.username = username
        self.password = password
        if self.api.generate_token(username, password):
            print("User authenticated successfully")
        else:
            raise Exception("Authentication failed")

    def check_user_authenticated(self):
        if len(self.username) != 0 and len(self.password) != 0:
            raise Exception("User wasn't authenticated")

    def insert_empty_project(self, project_name: str, meta: Union[Dict, None]=None) -> d.Project:
        self.check_user_authenticated()
        temp = d.Author(name=self.username, permission="write")
        self.projects[project_name] = d.Project(name=project_name, meta=meta, creator=self.username, author=[temp.dict()])
        print("Project created")
        return self.projects[project_name]

    def pop_project(self, project_name: str):
        try:
            self.projects.pop(project_name)
            print("Project removed")
        except:
            raise Exception("The project couldn't be deleted")
    
    def insert_empty_experiment(self, project_name: str, experiment_name: str, experiment_meta: Union[Dict, None]=None,project_meta: Union[Dict, None]=None) -> d.Experiment:
        self.check_user_authenticated()
        temp_author = d.Author(name=self.username, permission="write").dict()
        if self.projects[project_name] == None:
            print("The project doesn't exist. Initialising...")
            self.insert_empty_project(project_name, meta=project_meta)
        temp = d.Experiment(name=experiment_name, meta=experiment_meta,children=[], author=[temp_author])
        self.projects[project_name].groups.append(temp)
        return temp

    def pop_experiment(self, project_name, experiment_name):
        if self.projects[project_name] == None:
            raise Exception("Project doesn't exist")
        i = 0
        for experiment in self.projects[project_name].groups:
            # iterates over the experiments
            if experiment_name == experiment.name:
                # found
                self.projects[project_name].groups.pop(i)
                return True
            i += 1
        raise Exception("The experiment doesn't exist")

    def experiment_in_project(self,experiment_name: str, project_name: str):
        i = 0
        for experiment in self.projects[project_name].groups:
            if experiment_name == experiment.name:
                self.exp_index = i
                return True
            i += 1
        return False

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_name: str, payload: List, meta: Union[Dict, None], data_type: str, data_headings: List) -> d.Dataset:
        self.check_user_authenticated()
        # check if project or experiment exists locally
        if self.projects[project_name] == None or not self.experiment_in_project(experiment_name=experiment_name, project_name=project_name):
            # initialise the experiement and project
            self.insert_empty_experiment(project_name=project_name, experiment_name=experiment_name)
        # add dataset
        author_temp = [d.Author(name=self.username, permission="write").dict()]
        temp = d.Dataset(name=dataset_name,data=payload,meta=meta,data_type=data_type,data_headings=data_headings, author=author_temp)
        i = 0
        for experiment in self.projects[project_name].groups:
            if experiment.name == experiment_name:
                self.projects[project_name].groups[i].children.append(temp)
                return temp
            i += 1
        return temp

    def pop_dataset(self, project_name: str, experiment_name: str, dataset_name: str):
        if self.projects[project_name] == None:
            raise Exception("The project doesn't exist")
        if not self.experiment_in_project(experiment_name=experiment_name, project_name=project_name):
            raise Exception("The experiment doesn't exist")

        i = 0
        for dataset in self.projects[project_name].groups[self.exp_index].children:
            if dataset.name == dataset_name:
                self.projects[project_name].groups[self.exp_index].children.pop(i)
                print("The dataset popped")
            i += 1
        raise Exception("The dataset doesn't exist")
       
    def sync_data(self):
        """Updates the database with local files"""
        self.user_authenticate(self.username, self.password)
        self.api.update_cache() # update cache to speed up the process
        for project_name, project in self.projects:
            if self.api.check_project_exists(project_name=project_name):
                print(f'The local project - {project_name} - exists on the database. Checking experiments ...')
                experiments_temp = self.projects[project_name].groups
                for exp in experiments_temp:
                    if self.api.check_experiment_exists(project_name=project_name, experiment_name=exp.name):
                        print(f'The local experiment - {exp.name} - exists on the database. Checking datasets ...')
                        for dat in experiments_temp.children:
                            if self.api.check_dataset_exists(project_id=project_name, experiment_id=exp.name, dataset_id=dat.name):
                                print(f'The local dataset - {dat.name} - exists on the database. Skipping ...')
                            else:
                                # insert dataset
                                self.api.insert_dataset(project_name=project_name, experiment_name=exp.name, dataset_in=dat)
                                print(f'Dataset {dat.name} inserted')
                    else:
                        # insert experiment
                        self.api.insert_experiment(project_name=project_name, experiment=exp)
                        print(f'Experiment {exp.name} inserted')
            else:
                self.api.insert_project(project=self.projects[project_name])
                print(f'Project {project_name} inserted')





