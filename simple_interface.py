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
        self.projects: List[d.Project] = []
        self.api = i.API_interface(path_in=path, user_cache=True)
        self.exp_index = 0

    def create_user(self, username:str, password:str, email:str, full_name: str):
        if self.api.create_user(username_in=username, password_in=password, email=email, full_name=full_name):
            print("User created successfully")
        else:
            raise Exception("The user couldn't be created")

    def user_authenticate(self,username, password):
        self.username = username
        self.password = password
        if self.api.generate_token(username, password):
            print("User authenticated successfully")
        else:
            raise Exception("Authentication failed")

    def check_user_authenticated(self):
        if len(self.username) == 0 and len(self.password) == 0:
            raise Exception("User wasn't authenticated")

    def insert_empty_project(self, project_name: str, meta: Union[Dict, None]=None) -> d.Project:
        self.check_user_authenticated()
        temp = d.Author(name=self.username, permission="write")
        project = d.Project(name=project_name, meta=meta, creator=self.username, author=[temp.dict()])
        self.projects.append(project)
        print("Project created")
        return project

    def check_project_exists(self, project_name):
        for project in self.projects:
            if project.name == project_name:
                return True
        return False

    def get_project(self, project_name: str) -> d.Project:
        for project in self.projects:
            if project.name == project_name:
                return project
        raise Exception("The project wasn't found")

    def get_experiment(self, project_name: str, experiment_name) -> d.Experiment:
        for project in self.projects:
            if project.name == project_name:
                if project.groups == None:
                    raise Exception("The project specified doesn't have any experiments")
                for experiment in project.groups:
                    if experiment.name == experiment_name:
                        return experiment
        raise Exception("The experiment doesn't exist")

    def pop_project(self, project_name: str):
        try:
            i = 0
            for project in self.projects:
                if project_name == project.name:
                    self.projects.pop(i) 
                    print("Project removed")
                i += 1
            raise Exception("The project doesn't exist")
        except:
            raise Exception("The project couldn't be deleted")
    
    def insert_empty_experiment(self, project_name: str, experiment_name: str, experiment_meta: Union[Dict, None]=None,project_meta: Union[Dict, None]=None) -> d.Experiment:
        self.check_user_authenticated()
        temp_author = d.Author(name=self.username, permission="write").dict()
        if not self.check_project_exists(project_name):
            print("The project doesn't exist. Initialising...")
            self.insert_empty_project(project_name, meta=project_meta)
        temp = d.Experiment(name=experiment_name, meta=experiment_meta,children=[], author=[temp_author])
        temp_project = self.get_project(project_name)
        if temp_project.groups != None:
            temp_project.groups.append(temp)
        else:
            temp_project.groups = [temp]
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

    def check_experiment_exists(self,experiment_name: str, project_name: str):
        i = 0
        project = self.get_project(project_name)
        if project.groups == None:
            return False
        for experiment in project.groups:
            if experiment_name == experiment.name:
                self.exp_index = i
                return True
            i += 1
        return False

    def check_dataset_exists(self, project_name: str, experiment_name: str, dataset_name: str):
        if self.check_project_exists(project_name):
            if self.check_experiment_exists(project_name=project_name, experiment_name=experiment_name):
                experiment = self.get_experiment(project_name, experiment_name)
                for dataset in experiment.children:
                    if dataset.name == dataset_name:
                        return True
        return False

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_name: str, payload: List, meta: Union[Dict, None], data_type: str, data_headings: List) -> d.Dataset:
        self.check_user_authenticated()
        # check if project or experiment exists locally
        if not self.check_project_exists(project_name) or not self.check_experiment_exists(experiment_name=experiment_name, project_name=project_name):
            # initialise the experiement and project
            self.insert_empty_experiment(project_name=project_name, experiment_name=experiment_name)
        # add dataset
        author_temp = [d.Author(name=self.username, permission="write").dict()]
        temp = d.Dataset(name=dataset_name,data=payload,meta=meta,data_type=data_type,data_headings=data_headings, author=author_temp)
        i = 0
        project = self.get_project(project_name)
        if project.groups == None:
            raise Exception("The project is empty. Initialising the experiment failed.")
        for experiment in project.groups:
            if experiment.name == experiment_name:
                experiment.children.append(temp)
                return temp
            i += 1
        return temp

    def pop_dataset(self, project_name: str, experiment_name: str, dataset_name: str):
        if not self.check_project_exists(project_name):    
            raise Exception("The project doesn't exist")
        if not self.check_experiment_exists(experiment_name=experiment_name, project_name=project_name):
            raise Exception("The experiment doesn't exist")
        project = self.get_project(project_name)
        if project.groups == None:
            raise Exception("The project specified is empty")
        for experiment in project.groups:
            if experiment_name == experiment.name:
                if experiment.children == None:
                    raise Exception("The experiment contains no datasets")
                j = 0
                for dataset in experiment.children:
                    if dataset.name == dataset_name:
                        experiment.children.pop(j)
                        return True
                    j += 1
                print("The dataset popped")
        raise Exception("The dataset doesn't exist")

    def get_dataset(self, project_name: str, experiment_name:str, dataset_name:str) -> d.Dataset:
        experiment = self.get_experiment(project_name, experiment_name)
        for dataset in experiment.children:
            if dataset.name == dataset_name:
                return dataset
        raise Exception("The dataset doesn't exist")

    def sync_dataset(self, project_name:str, experiment_name: str, dataset_name: str):
        if self.check_dataset_exists(project_name, experiment_name, dataset_name):
            print(f'The dataset - {dataset_name} exists. Skipping ...')
        else:
            dataset = self.get_dataset(project_name, experiment_name, dataset_name)
            self.api.insert_dataset(project_name, experiment_name, dataset)
       
    def sync_data(self):
        """Updates the database with local files"""
        self.user_authenticate(self.username, self.password)
        self.api.update_cache() # update cache to speed up the process
        for project in self.projects:
            if self.api.check_project_exists(project.name):
                print(f'The local project - {project.name} - exists on the database. Checking experiments ...')
                if project.groups == None:
                    print(f'The project - {project.name} - is empty. Skipping ...')
                else:
                    for exp in project.groups:
                        # iterate over experiments
                        if self.api.check_experiment_exists(project_name=project.name, experiment_name=exp.name):
                            print(f'The local experiment {exp.name} exists - checking datasets ...')
                            if exp.children == None or len(exp.children) == 0:
                                print("The experiment has no datasets. Skipping ...")
                            else:
                                for dat in exp.children:
                                    if self.api.check_dataset_exists(project_id=project.name, experiment_id=exp.name, dataset_id=dat.name):
                                        print(f'The dataset {dat.name} exists. Skipping ...')
                                    else:
                                        self.api.insert_dataset(project_name=project.name, experiment_name=exp.name, dataset_in=dat)
                        else:
                            print(f'Inserting the experiment {exp.name}')
                            self.api.insert_experiment(project_name=project.name, experiment=exp)
            else:
                # insert the project
                #
                self.api.insert_project(project=project)
                print(f'Project {project.name} inserted')

    def return_project(self, project_name: str):
        return self.api.return_full_project(project_name)

    def return_experiment(self, project_name:str, experiment_name:str):
        return self.api.return_full_experiment(project_name, experiment_name)

    def return_dataset(self, project_name: str, experiment_name:str, dataset_name:str):
        return self.api.return_full_dataset(project_name, experiment_name, dataset_name)


class Tree(object):
    def __init__(self, nodes):
        # data is a list[dict["project_name" : "", "experiment_data" : dict[{"experiment_name" : dataset_names_list}] ]]
        self.tree = {}
        self.node_names = set()
        if nodes != None:
            self.insert_node("root", None)
            for proj_dict in nodes:
                self.insert_node(proj_dict.get("project_id"), "root")
                for exp_dict in proj_dict.get("experiment_list"):
                    self.insert_node(exp_dict.get("experiment_id"),proj_dict.get("project_id"))
                    for dataset_name in exp_dict.get("dataset_list"):
                        self.insert_node(dataset_name, exp_dict.get("experiment_name"))

    def insert_node(self, node_name, parent_name):
        parent_node = self.tree.get(parent_name)
        if parent_node is None:
            parent_node = {}
            self.tree[parent_name] = parent_node
        node = parent_node.get(node_name)
        if node is None:
            node = {}
            parent_node[node_name] = node
            self.node_names.add(node_name)

    def check_node_exists(self, node_name):
        return node_name in self.node_names

    def clear_tree(self):
        self.tree = {}
        self.node_names = set()

    def delete_node(self, node_name):
        if node_name not in self.node_names:
            return
        del self.tree[node_name]
        self.node_names.remove(node_name)
        for parent_name, parent_node in self.tree.items():
            if node_name in parent_node:
                del parent_node[node_name]
                break



