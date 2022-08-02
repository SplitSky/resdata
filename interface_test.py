from interface import API_interface
import testing as t

project_name = "S_Church"
author_name = "S.Church"
filename = "test.json"
path = "http://127.0.0.1:8000/"

username = "splitsky"
password = "wombat"
full_name = "Tomasz Neska"
email = "wombat@gmail.com"

# check connection
ui = API_interface(path)
print(ui.check_connection())

# insert user

#ui.create_user(username, password)

# validate user


# insert project using the token


# wait for the token to expire


# try to insert project again





# Create a test project
t.create_test_file_project(filename, [1, 1], project_name, author_name)
# Load the project
project_in = t.load_file_project(filename)
# Connect to API
ui = API_interface(path)
ui.check_connection()
# insert project
print("Inserting Project")
temp = ui.insert_project(project=project_in)
print("Response:")
print(temp)
print("Returning Project")
temp = ui.get_project_names()
print(temp)


