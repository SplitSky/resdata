import testing as t
from interface import API_interface
import datastructure as d

path = "http://127.0.0.1:8000/"

# tests to conduct


# 3. returning a project using that user
# 4. tree print
# 5. creating a user and inserting a second project
# 6. giving the second user permissions to one of the datasets + tree print to confirm
# 7. trying to insert nothing
# 8. updating permissions for user 2 -> making it able to edit project belonging to user 1
# 9. User 2 authenting and inserting a dataset in project belonging to user 1
# 10. User 2 insert dataset into experiment with read only permissions # TODO: This feature may not work but should be updated later

class TestClass:
    def test_1(self):
        # 1. creating a user
        username = "test_user"
        password = "some_password123"
        email= "test_user@email.com"
        full_name = "test user"
        ui = API_interface(path)
        assert ui.create_user(username_in=username, password_in=password, email=email, full_name=full_name) == True
        # user created successfully      

    def test_2(self):
        # 2. inserting a project using that user
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        ui.generate_token(username, password)
        
        # generate test_project
        file_name = "test_project.json"
        project_name = "test_project_1"
        t.create_test_file_project(filename_in=file_name, structure=[1,1], project_name=project_name, author_name=username)
        project_in = t.load_file_project(filename_out=file_name)
        assert ui.insert_project(project=project_in) == True


    def test_3(self):
        # 3. insert dataset and return it to compare
        # TODO: Finish making test cells from here 
        a = 1
         

            

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


