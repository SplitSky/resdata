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
        temp = ui.insert_project(project_in)
        temp = ui.get_project_names()
        
        temp = ui.return_fullproject(project_name=project_in.get_name())
        assert str(temp.convertJSON()) == str(project_in.convertJSON()) # compares the database project with the one generated

    def test_2(self):
        # check connection
        ui = API_interface(path)
        assert ui.check_connection() == True

    def test_3(self):
        username = "test_user"
        password = "wombat"
        email = "wombatCombat@email.com"
        fullName = "Wombat Smith"

        # creating a user test
        ui = API_interface(path)
        response = ui.create_user(username_in=username, password_in=password,email=email ,full_name= fullName)
        print("response2" + str(response))
        assert response == True

    def test_4(self):
        # authentication of a user and an insertion of database
        username = "test_user"
        password = "wombat"
        email = "wombatCombat@email.com"
        fullName = "Wombat Smith"

        ui = API_interface(path)
        ui.generate_token(username, password)
#
#    def test_5(self):
#        # authentication of a user and an insertion of an experiment
#
#    def test_6(self):
#        # authentication of a usr and an insertion of a project

def main():
    thing = TestClass()
    thing.test_3()


main()

