import json
import main as mn
import random
from datetime import date

#### this file contains the functions used for generating testing data

def create_test_file_project(filename_id, structure, project_name, author_name):
    '''
    filename_in         string       name of json file
    structure           list         list containing the number of experiments and datasts
    '''

    x = []
    y = []
    y2 = []
    for i in range(0,100):
        x.append(i)
        y.append(random.randint(0,100))
        y2.append(random.randint(0,100))

    test_data_3D = [x,y,y2]
    experiments = []
    datasets = []

    datasets_dict = {}
    experiments_dict = {}
