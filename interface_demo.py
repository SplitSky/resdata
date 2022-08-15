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
project = ds.Project(name=project_name, author=[{"name" : 'patrick', "permission" : "write"}], creator = 'patrick')
try:
    ui.insert_project(project)
except RuntimeError:
    print('Project already exists, continuing')
    pass

# 5) insert experiment
experiment = ds.Experiment(name='PL', children=[])
try:
    ui.init_experiment(project_name, experiment)
except KeyError:
    print("Experiment already exists")
    pass

# 6) Insert a few datasets
for i in range(5):
    data_in = [1,2,3,4,5]
    d = ds.Dataset(name=f"ID{i}", data=data_in, data_type="int", author=[{"name" : 'patrick', "permission" : "write"}])
    print(f'Inserting set {i}')
    ui.insert_dataset(project_name=project_name, experiment_name='PL', dataset_in=d)

# 7) fetch data
d = ui.return_full_experiment(project_name=project_name, experiment_name="PL")

# 8) Create a second user and attempt inserting dataset -> then fetch


# 9) Give the second user permissions and show allowed projects, experiments, datasets


# 10) Remove the second user's permissions and show allowed projects, experiments, datasets
