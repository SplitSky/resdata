from interface import API_interface
import datastructure as ds

path = "http://127.0.0.1:8000/"
username, password, email, fullname = 'patrick', 'patrick', 'patrick', 'patrick'
project_name = 'test_project'

# 0) Connect to API
ui = API_interface(path)

# 1) Check connection
print(f"Testing connection: {ui.check_connection()}")

# 2) insert user
if ui.create_user(username, password, email, fullname):
    print('Created user')
else:
    print('User already exists, continuing')

# 3) Create token
ui.generate_token(username, password)

# 4) insert project using the token
project = ds.Project(name=project_name, author='patrick')
try:
    ui.insert_project(project)
except RuntimeError:
    print('Project already exists, continuing')
    pass

# 5) insert experiment
experiment = ds.Experiment(name='PL')
try:
    ui.init_experiment(project_name, experiment)
except KeyError:
    print("Experiment already exists")
    pass

# 6) Insert a few dataset
for i in range(5):
    d = ds.Dataset(name=f"ID{i}", data=i, data_type="int")
    print(f'Inserting set {i}')
    ui.insert_dataset(project_name=project_name, experiment_name='PL', dataset_in=d)

# 7) fetch data
ui.return_full_experiment(project_name=project_name,experiment_name="PL")