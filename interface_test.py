from interface import API_interface
import datastructure as ds

path = "http://127.0.0.1:8000/"
username, password, email, fullname = 'patrick', 'patrick', 'patrick', 'patrick'

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
project = ds.Project(name='test_project', author='patrick')
try:
    ui.insert_project(project)
except RuntimeError:
    print('Project already exists, continuing')
    pass

# 5) try to insert project again
