import testing as t
from interface import API_interface
import pytest


path = "http://127.0.0.1:8000/"

class TestClass:
    def test_1(self):
        # to run this test purge the database from test entries otherwise the data generated won't be updated.
        project_name = "S_Church"
        author_name = "S.Church"
        filename = "test.json"
        t.create_test_file_project(filename, [1,1], project_name, author_name)
        project_in = t.load_file_project(filename)
        
        ui = API_interface(path)
        ui.check_connection()
        # authenticate
        username = "wombat"
        password = "marsupial"
        email = "marsupial1@gmail.com"
        full_name = "not_wombat"
        ui.create_user(username_in=username, password_in=password,email=email, full_name=full_name)
        # add credentials to interface
        ui.generate_token(username, password)
        print("finished authenticating")
        print("token is: ")
        print(ui.token)
        temp = ui.insert_project(project_in)
        # TODO: only return the project and experiment names that the user has permission to access
        #temp = ui.get_project_names()
        
        temp = ui.return_fullproject(project_name=project_in.get_name())
        #assert str(temp.convertJSON()) == str(project_in.convertJSON()) # compares the database project with the one generated

    def test_2(self):
        # check connection
        ui = API_interface(path)
        ui.check_connection()

    def test_3(self):
        username = "string"
        password = "string"
        email = "wombatCombat@email.com"
        fullName = "Wombat Smith"
        # creating a user test
        ui = API_interface(path)
        response = ui.create_user(username_in=username, password_in=password,email=email ,full_name= fullName)
        print("response2" + str(response))

    def test_4(self):
        # authentication of user and returns a token
        username = "test_user"
        password = "wombat"
        ui = API_interface(path)
        ui.generate_token(username, password)

    def test_5(self):
        # authentication of a user using the token
        username = "test_user"
        password = "wombat"
        ui = API_interface(path)
        ui.generate_token(username, password)
        
        # insert a project
        filename = "authenticated_test.json"
        project_name = "T_Neska"
        author_name = "T.Neska"

        t.create_test_file_project(filename, [1,1], project_name, author_name)
        project_in = t.load_file_project(filename) 
        ui.insert_project(project_in)



    def test_6(self):
        # insertion of the project with failed authentication
        username = "test_user"
        password = "not_wombat"
        ui = API_interface(path)
        ui.generate_token(username, password)

    def test_7(self):
        ui = API_interface(path)
        ui.try_authenticate()

    def test_8(self):
        # populate the database with projects belonging to different users
        ui = API_interface(path)
        # user 1 commits
        username = "user1"
        password = "user1_password"
        email = "user1@email.com"
        full_name = "user one"
        ui.create_user(username_in=username, password_in=password, email=email, full_name=full_name)
        
        # insert 2 projects
        ui.generate_token(username, password) # authenticate
        filename = "user1.json"
        project_name = "user1_project1"
        t.create_test_file_project(filename, [2,3], project_name, username)
        project_in = t.load_file_project(filename) 
        ui.insert_project(project_in)

        project_name = "user1_project2"
        t.create_test_file_project(filename, [1,3], project_name, username)
        project_in = t.load_file_project(filename) 
        ui.insert_project(project_in)

        # user 2 commits
        username = "user2"
        password = "user2_password"
        email = "user1@email.com"
        full_name = "user one"
        ui.create_user(username_in=username, password_in=password, email=email, full_name=full_name)

        # insert 1 project # inserts the datasets with the same name as the previous project
        # checks whether the user has write priviledges in the project
        ui.generate_token(username, password) # authenticate
        filename = "user2.json"
        project_name = "user2_project1"
        t.create_test_file_project(filename, [2,3], project_name, username)
        project_in = t.load_file_project(filename) 
        ui.insert_project(project_in)

        project_name = "user2_project2"
        t.create_test_file_project(filename, [1,3], project_name, username)
        project_in = t.load_file_project(filename) 
        ui.insert_project(project_in)

        # user 3 commits
        username = "user3"
        password = "user3_password"
        email = "user1@email.com"
        full_name = "user one"
        ui.create_user(username_in=username, password_in=password, email=email, full_name=full_name)



        # assign user 3 to projects commited by user 1
    def test_8(self):
        ui = API_interface(path)
        ui.username = "wombat"
        print(ui.get_project_names())


def main():
    thing = TestClass()
    thing.test_8()
main()

