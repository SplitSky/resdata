import server.datastructure as d
import json
from datetime import date
import random
import numpy as np
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
    for i in range(0, 100):
        x.append(i)
        y.append(random.randint(0, 100))
        y2.append(random.randint(0, 100))
    test_data_3D = [x, y, y2]
    # dataset1 = mn.Dataset(name="dataset1", data=test_data_2D, meta="test dataset 1", data_type="2D dataset")
    experiments = []
    datasets = []
    template_author = d.Author(name=author_name, permission="write")
    meta_temp = [str(date.today())]
    for j in range(0, structure[1], 1):
        dataset = d.Dataset(name="dataset_" + str(j), data=test_data_3D, data_type="3D dataset",
                            meta={"note": "dataset metadata", "date": meta_temp[0]},
                            author=[template_author.dict()], data_headings=["x", "y", "z"])
        datasets.append(dataset)

    for i in range(0, structure[0], 1):
        experiment = d.Experiment(name="experiment_" + str(i), children=datasets,
                                  meta={"note": "experiment metadata","date": meta_temp[0]},
                                  author=[template_author.dict()])
        experiments.append(experiment)

    project = d.Project(name=project_name, creator=author_name, groups=experiments,
                        meta={"note": "project metadata", "date": meta_temp[0]}, author=[template_author.dict()])
    with open(filename_in, 'w') as file:
        json.dump(project.dict(), file)
        file.close()
    # project.convertJSON()


def create_test_file_dataset(filename_in, dataset_name):
    meta_temp = {"date" : str(date.today())}
    x = []
    y = []
    y2 = []
    for i in range(0, 100):
        x.append(i)
        y.append(random.randint(0, 100))
        y2.append(random.randint(0, 1))
    test_data_3D = [x, y, y2]
    template_author = d.Author(name="wombat", permission="write")
    dataset = d.Dataset(name=dataset_name, data=test_data_3D, data_type="3D dataset", meta=meta_temp,
                        author=[template_author.dict()], data_headings=["testing_heading"])
    with open(filename_in, 'w') as file:
        json.dump(dataset.convertJSON(), file)
        file.close()


def load_file_project(filename_out):  # returns a project object from file
    # load files. Initially json files in the correct format
    with open(filename_out, 'r') as file:
        python_dict = json.load(file)
        # python_dict = json.loads(json_string)
        groups_temp = []
        for experiment in python_dict.get("groups"):
            # iterate over datasets
            datasets_temp = []
            for dataset in experiment.get("children"):
                datasets_temp.append(
                    d.Dataset(name=dataset.get("name"), data=dataset.get("data"), data_type=dataset.get("data_type"),
                              meta=dataset.get("meta"), author=dataset.get("author"),
                              data_headings=dataset.get("data_headings")))
            groups_temp.append(
                d.Experiment(name=experiment.get("name"), children=datasets_temp, meta=experiment.get("meta"),
                             author=experiment.get("author")))
        project = d.Project(name=python_dict.get("name"), author=python_dict.get("author"), groups=groups_temp,
                            meta=python_dict.get("meta"),
                            creator=python_dict.get("creator"))  # initialise empty project
        file.close()

    return project


def load_file_dataset(filename_out):
    with open(filename_out, 'r') as file:
        json_string = json.load(file)
        dataset = d.Dataset(name=json_string.get("name"), data=json_string.get("data"), meta=json_string.get("meta"),
                            data_type=json_string.get("data_type"), author=json_string.get("author"),
                            data_headings=json_string.get("data_headings"))
        file.close()
    return dataset


def create_ring_object(ring_id : int, author_in : d.Author, size : int):
    x, y, y2 = [], [], []
    for i in range(0, size):
        x.append(i)
        y.append(random.randint(0, 100))
        y2.append(random.randint(0, 2))
    test_data_3D = [x, y, y2]

    ring_dio = random.random()
    quality = random.randint(0, 10)
    pitch = random.random()
    threshold = random.random()
    spectrum_headings = [["Frequency", "intensity", "Intensity error"],["Frequency", "intensity", "Intensity error"],["Frequency", "intensity", "Intensity error"]]
    return d.Ring(ring_id=ring_id, ring_dio=ring_dio, quality=quality, pitch=pitch,
                  threshold=threshold,spectrum_dataset=[test_data_3D, test_data_3D, test_data_3D],
                  spectrum_data_types=["PL spectrum", "TRPL spectrum", "Lasing spectrum"] ,
                  spectrum_headings= spectrum_headings,
                  spectrum_names= ["PL spectrum","TRPL spectrum", "Lasing spectrum"],
                  author=[author_in.dict()], datasets=[])


def generate_optics_project(filename_in, structure, project_name, experiment_name, author_name, size_of_dataset):
    '''
    Returns a ring object
    filename_in     string      the name of the json file
    structure       list        a list containing the number of the experiments and datasets [0,0]
    '''
    template_author = d.Author(name=author_name, permission="write")
    # generate rings
    datasets = []
    for i in range(0, structure[0], 1):
        # generate rings
        ring_temp = create_ring_object(i, template_author, size_of_dataset)
        temp = ring_temp.convert_to_document_list()
        for entry in temp:
            datasets.append(entry)

    experiments = []
    for j in range(0, structure[1], 1):
        # generate experiements
        experiments.append(
            d.Experiment(name=experiment_name + " " + str(j), children=datasets, meta={"date": str(date.today())},
                         author=[template_author.dict()]))
    project = d.Project(name=project_name, creator=template_author.name, groups=experiments,
                        meta={"date": str(date.today()),"note": "Test project"}, author=[template_author.dict()])

    with open(filename_in, 'w') as file:
        json.dump(project.dict(), file)
        file.close()

def betterGenerateArray(N):
    random_set = np.random.uniform(0, 1, N)
    return random_set

def generate_model_data(list_size : int, lambda_temp : float):
    # generates a 2D dimensional array of an exponential function
   step = 0.1
   N = list_size
   #bins = np.arange(0, 1, step)
   temp = betterGenerateArray(N)
   expDist = -1 * lambda_temp * np.log(temp)
   histogram = np.histogram(expDist)
   y = histogram[0]
   x = histogram[1][:len(histogram[1]) - 1] + step / 2
   y = np.log(y)
   # eliminate zeroes
   temp = []
   for counter in range(0, len(y), 1):
       if y[counter] == -np.inf:
           temp.append(counter)
   y = np.delete(y, temp)
   x = np.delete(x, temp)
   return [list(x), list(y)]


def create_ring_object_2(ring_id : int, author_in : d.Author, size : int, dataset_size: int, value: int):
    x, y, y2 = [], [], []
    for i in range(0, size):
        #x.append(i)
        #y.append(random.randint(0, 100))
        y2.append(random.randint(0, 2))
    x,y = generate_model_data(list_size=dataset_size, lambda_temp=value)
    test_data_3D = [x, y, y2]

    ring_dio = random.random()
    quality = random.randint(0, 10)
    pitch = random.random()
    threshold = random.random()
    spectrum_headings = [["Frequency", "intensity", "Intensity error"],["Frequency", "intensity", "Intensity error"],["Frequency", "intensity", "Intensity error"]]
    return d.Ring(ring_id=ring_id, ring_dio=ring_dio, quality=quality, pitch=pitch,
                  threshold=threshold,spectrum_dataset=[test_data_3D, test_data_3D, test_data_3D],
                  spectrum_data_types=["PL spectrum", "TRPL spectrum", "Lasing spectrum"] ,
                  spectrum_headings= spectrum_headings,
                  spectrum_names= ["PL spectrum","TRPL spectrum", "Lasing spectrum"],
                  author=[author_in.dict()], datasets=[])

def generate_optics_project_2(filename_in, structure, project_name, experiment_name, author_name, size_of_dataset, value):
    '''
    Returns a ring object
    filename_in     string      the name of the json file
    structure       list        a list containing the number of the experiments and datasets [0,0]
    '''
    template_author = d.Author(name=author_name, permission="write")
    # generate rings
    datasets = []
    for i in range(0, structure[0], 1):
        # generate rings
        ring_temp = create_ring_object_2(i, template_author, size_of_dataset, dataset_size=size_of_dataset, value=value)
        temp = ring_temp.convert_to_document_list()
        for entry in temp:
            datasets.append(entry)

    experiments = []
    for j in range(0, structure[1], 1):
        # generate experiements
        experiments.append(
            d.Experiment(name=experiment_name + " " + str(j), children=datasets, meta={"date": str(date.today())},
                         author=[template_author.dict()]))
    project = d.Project(name=project_name, creator=template_author.name, groups=experiments,
                        meta={"date": str(date.today()),"note": "Test project"}, author=[template_author.dict()])
    with open(filename_in, 'w') as file:
        json.dump(project.dict(), file)
        file.close()

def create_test_file_project_time(filename_in, structure, project_name, author_name, variable_type, dataset_size):
    '''
    filename_in     string      the name of the json file
    structure       list        a list containing the number of the experiments and datasets [0,0]
    '''

    x = []
    y = []
    y2 = []

    if variable_type == "int":
        for i in range(0, dataset_size):
            x.append(i)
            y.append(random.randint(0, 1000))
            y2.append(random.randint(0, 1000))
        test_data_3D = [x, y, y2]
    elif variable_type == "float":
        for i in range(0, dataset_size):
            x.append(random.SystemRandom().uniform(5,10))
            y.append(random.SystemRandom().uniform(5,10))
            y2.append(random.SystemRandom().uniform(5,10))
        test_data_3D = [x, y, y2]
    elif variable_type == "bytes":
        for i in range(0, dataset_size):
            x.append(random.randbytes(64))
            y.append(random.randbytes(64))
            y2.append(random.randbytes(64))
        test_data_3D = [x, y, y2] 
    else:
        for i in range(0, dataset_size):
            x.append(random.random())
            y.append(random.random())
            y2.append(random.random())
        test_data_3D = [x, y, y2]

    # dataset1 = mn.Dataset(name="dataset1", data=test_data_2D, meta="test dataset 1", data_type="2D dataset")
    experiments = []
    datasets = []
    template_author = d.Author(name=author_name, permission="write")
    meta_temp = [str(date.today())]
    for j in range(0, structure[1], 1):
        dataset = d.Dataset(name="dataset_" + str(j), data=test_data_3D, data_type="3D dataset",
                            meta={"note": "dataset metadata", "date": meta_temp[0]},
                            author=[template_author.dict()], data_headings=["x", "y", "z"])
        datasets.append(dataset)

    for i in range(0, structure[0], 1):
        experiment = d.Experiment(name="experiment_" + str(i), children=datasets,
                                  meta={"note": "experiment metadata","date": meta_temp[0]},
                                  author=[template_author.dict()])
        experiments.append(experiment)

    project = d.Project(name=project_name, creator=author_name, groups=experiments,
                        meta={"note": "project metadata", "date": meta_temp[0]}, author=[template_author.dict()])
    with open(filename_in, 'w') as file:
        json.dump(project.dict(), file)
        file.close()
    # project.convertJSON()

def save_file_project(file_name: str, project: d.Project):
    with open(file_name, 'w') as file:
        json.dump(project.dict(), file)
        file.close()
