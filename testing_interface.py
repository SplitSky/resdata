import testing as t
from interface import API_interface

path = "http://127.0.0.1:8000/"


class TestClass:
    def test_1(self):
        # to run this test purge the database from test entries otherwise the data generated won't be updated.
        project_name = "S_Church"
        author_name = "S.Church"

        filename = "test.json"
        t.create_test_file_project(filename, [1, 1], project_name, author_name)
        project_in = t.load_file_project(filename)

        ui = API_interface(path)
        #ui.check_connection()
        # authenticate
        username = "wombat"
        password = "marsupial"
        email = "marsupial1@gmail.com"
        full_name = "not_wombat"
        ui.create_user(username_in=username, password_in=password, email=email, full_name=full_name)
        # add credentials to interface
        ui.generate_token(username, password)
        ui.insert_project(project=project_in)
        print("finished authenticating")
        temp = ui.return_full_project(project_name=project_in.name)
        print("Printing the return project")
        print(temp.json())
        # assert str(temp.convertJSON()) == str(project_in.convertJSON()) # compares the database project with the one generated

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
        response = ui.create_user(username_in=username, password_in=password, email=email, full_name=fullName)
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

        t.create_test_file_project(filename, [1, 1], project_name, author_name)
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
        username1 = "user1"
        password1 = "user1_password"
        email = "user1@email.com"
        full_name = "user one"
        ui.create_user(username_in=username1, password_in=password1, email=email, full_name=full_name)

        # user 2 commits
        username2 = "user2"
        password2 = "user2_password"
        email = "user1@email.com"
        full_name = "user one"
        ui.create_user(username_in=username2, password_in=password2, email=email, full_name=full_name)
        project_name1 = "user1_project1"

       # # insert 2 projects
       # ui.generate_token(username1, password1) # authenticate
       # filename = "user1.json"

       # t.create_test_file_project(filename, [1,2], project_name1, username1)
       # project_in = t.load_file_project(filename)
       # ui.insert_project(project_in)

       # project_name = "user1_project2"
       # t.create_test_file_project(filename, [4,5], project_name, username1)
       # project_in = t.load_file_project(filename)
       # ui.insert_project(project_in)



       # # insert 1 project # inserts the datasets with the same name as the previous project
       # # checks whether the user has write priviledges in the project
       # ui.generate_token(username2, password2) # authenticate
       # filename = "user2.json"
       # project_name = "user2_project1"
       # t.create_test_file_project(filename, [1,3], project_name, username2)
       # project_in = t.load_file_project(filename)
       # ui.insert_project(project_in)

       # project_name = "user2_project2"
       # t.create_test_file_project(filename, [5,1], project_name, username2)
       # project_in = t.load_file_project(filename)
       # ui.insert_project(project_in)

        # user 3 commits
        username3 = "user3"
        password3 = "user3_password"
        email = "user1@email.com"
        full_name = "user one"
        ui.create_user(username_in=username3, password_in=password3, email=email, full_name=full_name)

        # assign user 3 to projects commited by user 1
        # authenticate as user 1 and add user 3 as author to the project
        ui.generate_token(username=username1, password=password1)
        ui.add_author_to_project_rec(project_id=project_name1, author_name=username3, author_permission="read")
        
        print("add_author_to_project ran") 
        print("printing user 1 files:")
        ui.generate_token(username=username1, password=password1)
        ui.tree_print()
        print(" ")
        print("printing user 2 files:")
        ui.generate_token(username=username2, password=password2)
        ui.tree_print()
        print(" ")
        print("printing user 3 files:")
        ui.generate_token(username=username3, password=password3)
        ui.tree_print()
        print(" ")

    def test_9(self): # testing of the tree printing function
        print("test 9")
        ui = API_interface(path)
        username = "wombat"
        password = "marsupial"
        ui.generate_token(username, password) # log in
        ui.tree_print() # print the data


def main():
    thing = TestClass()
    thing.test_8()
    #thing.test_9()
main()
