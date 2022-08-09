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
        temp = ui.get_project_names()
        
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


def main():
    thing = TestClass()
    thing.test_1()
main()

