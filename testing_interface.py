import testing as t
from interface import API_interface

def inserting_project_test():
    project_name = "S_Church"
    author_name = "S.Church"
    filename = "test.json"
    path = "http://127.0.0.1:8000/"

    t.create_test_file_project(filename, [1,1], project_name, author_name)
    project_in = t.load_file_project(filename)
    ui = API_interface(path)

    ui.check_connection()

    print("Inserting Project")
    temp = ui.insert_project(project_in)
    print("Response: ")
    print(temp)

    print("Returning project")
    temp = ui.get_project_names()
    print(temp)
    temp = ui.return_fullproject(project_name=project_in.get_name())

def main():
    #print("Test project is being inserted")
    inserting_project_test()


main()

