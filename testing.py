import datastructure as d
import json
from datetime import date
import random

'''
json file in -> dictionary format
h5 file in -> conversion to json file format
storage is done using classes but file storage is done using nested dicitonaries as json doesn't serialise
lists of objects
'''

def create_test_file_project(filename_in, structure, project_name, author_name):
    '''
    filename_in     string      the name of the json file
    structure       list        a list containing the number of the experiments and datasets [0,0]
    '''

    x = []
    y = []
    y2 = []
    for i in range(0,2):
        x.append(i)
        y.append(random.randint(0,100))
        y2.append(random.randint(0,100))
    test_data_3D = [x,y,y2]
    # dataset1 = mn.Dataset(name="dataset1", data=test_data_2D, meta="test dataset 1", data_type="2D dataset")
    experiments = []
    datasets = []

    meta_temp = str(date.today())
    for j in range(0,structure[1],1):
        dataset = d.Dataset(name="dataset_" + str(j), data=test_data_3D, data_type="3D dataset", meta=meta_temp)
        datasets.append(dataset)

    for i in range(0,structure[0],1):
        experiment = d.Experiment(name="experiment_" + str(i), children=datasets, meta=meta_temp)
        experiments.append(experiment)
    
    project = d.Project(name=project_name, author=author_name, groups=experiments, meta="This is a test")
    with open(filename_in, 'w') as file:
        json.dump(project.convertJSON(),file)
        file.close()
    # project.convertJSON()


def create_test_file_dataset(filename_in, dataset_name):

    meta_temp = str(date.today())
    x = []
    y = []
    y2 = []
    for i in range(0,100):
        x.append(i)
        y.append(random.randint(0,100))
        y2.append(random.randint(0,100))
    test_data_3D = [x,y,y2]
    dataset = d.Dataset(name="dataset_name", data=test_data_3D, data_type="3D dataset", meta=meta_temp)
    with open(filename_in, 'w') as file:
        json.dump(dataset.convertJSON(),file)
        file.close()


def load_file_project(filename_out): # returns a project object from file
    # load files. Initially json files in the correct format
    with open(filename_out, 'r') as file:
        python_dict = json.load(file)
        #python_dict = json.loads(json_string)
        print("The data type is: " + str(type(python_dict)))
        print("contents of the file: ")
        print(python_dict)
        groups_temp = []
        for i, experiment in python_dict.get("groups").items():
            # iterate over datasets
            datasets_temp = []
            for j, dataset in experiment.get("datasets").items():
                datasets_temp.append(d.Dataset(name=dataset.get("name"), data=dataset.get("data") , data_type=dataset.get("data_type"), meta=dataset.get("meta")))
            groups_temp.append(d.Experiment(name= experiment.get("name"),children= datasets_temp,meta=experiment.get("meta")))
        project = d.Project(name=python_dict.get("name"),author=python_dict.get("author"),groups=groups_temp,meta=python_dict.get("meta")) # initialise empty project
        file.close()
    
    return project


def load_file_dataset(filename_out):
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        print("The data type is: " + str(type(json_string)))
        dataset = d.Dataset(name=json_string.get("name") , data=json_string.get("data"), meta= json_string.get("meta"), data_type=json_string.get("data_type"))
        file.close()
    return 
