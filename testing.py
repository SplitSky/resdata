import datastructure as d
import json
from datetime import date
import random

def create_test_file_project(filename_in, structure, project_name, author_name):
    '''
    filename_in     string      the name of the json file
    structure       list        a list containing the number of the experiments and datasets [0,0]
    '''

    x = []
    y = []
    y2 = []
    for i in range(0,100):
        x.append(i)
        y.append(random.randint(0,100))
        y2.append(random.randint(0,100))
    test_data_3D = [x,y,y2]
    # dataset1 = mn.Dataset(name="dataset1", data=test_data_2D, meta="test dataset 1", data_type="2D dataset")
    experiments = []
    datasets = []

    datasets_dict = {}
    experiments_dict = {}

    meta_temp = str(date.today())
    for j in range(0,structure[1],1):
        dataset = d.Dataset(name="dataset " + str(j), data=test_data_3D, data_type="3D dataset", meta=meta_temp)
        datasets.append(dataset)
        datasets_dict[j] = dataset.convertJSON() # appends a dictionary using the convert function

    for i in range(0,structure[0],1):
        experiment = d.Experiment(name="experiment " + str(i), children=datasets_dict, meta=meta_temp)
        experiments.append(experiment)
        experiments_dict[i] = experiment.convertJSON() # appends a dictionary using the conversion function
    
    project = d.Project(name=project_name, author=author_name, groups=experiments_dict, meta="This is a test")
    with open(filename_in, 'w') as file:
        json.dump(project.convertJSON(),file)
        file.close()
    # project.convertJSON()


def create_test_file_dataset(filename_in):

    meta_temp = str(date.today())
    x = []
    y = []
    y2 = []
    for i in range(0,100):
        x.append(i)
        y.append(random.randint(0,100))
        y2.append(random.randint(0,100))
    test_data_3D = [x,y,y2]
    dataset = d.Dataset(name="dataset 0", data=test_data_3D, data_type="3D dataset", meta=meta_temp)
    with open(filename_in, 'w') as file:
        json.dump(dataset.convertJSON(),file)
        file.close()


def load_file_project(filename_out): # returns a project object
    # load files. Initially json files in the correct format
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        #python_dict = json.loads(json_string)
        print("The data type is: " + str(type(json_string)))

        project = d.Project(groups={}) # initialise empty project
        project.convertDictionary(json_string)
        file.close()
    return project


def load_file_dataset(filename_out):
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        print("The data type is: " + str(type(json_string)))
        dataset = d.Dataset(name=json_string.get("name") , data=json_string.get("data"), meta= json_string.get("meta"), data_type=json_string.get("data_type"))
        file.close()
    return dataset
