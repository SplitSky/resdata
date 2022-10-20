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
    def test_0(self):
        # check connection
        ui = API_interface(path)
        ui.check_connection()
    def test_1(self):
        # 1. creating a user
        username = "test_user"
        password = "some_password123"
        email= "test_user@email.com"
        full_name = "test user"
        ui = API_interface(path)
        # purge everything
        ui.purge_everything()

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
        print(project_in.json())
        assert ui.insert_project(project=project_in) == True

    def test_3(self):
        # 3. return a project to compare with the file
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        ui.generate_token(username, password)
        file_name = "test_project.json"
        project_name = "test_project_1"
        # return project
        project_from_db = ui.return_full_project(project_name=project_name)
        # load in the file
        project_from_file = t.load_file_project(filename_out=file_name)
        # compare assertions
        assert project_from_db.name == project_from_file.name
        assert project_from_db.meta == project_from_file.meta
        assert project_from_db.creator == project_from_file.creator
        assert project_from_db.author == project_from_file.author

        # compare experiments
        if project_from_file.groups == None or project_from_db.groups == None:
            raise Exception("")
        for i in range(0, len(project_from_file.groups)):
            file_experiment = project_from_file.groups[i]
            db_experiment = project_from_db.groups[i]
            
            # compare the experiment variables
            assert file_experiment.name == db_experiment.name
            assert file_experiment.author == db_experiment.author
            assert file_experiment.meta == db_experiment.meta
            for j in range(0, len(file_experiment.children)): # iterate over datasets
                file_dataset = file_experiment.children[j]
                db_dataset = db_experiment.children[j]
                assert file_dataset.name == db_dataset.name
                assert file_dataset.data == db_dataset.data
                assert file_dataset.data_type == db_dataset.data_type
                assert file_dataset.author == db_dataset.author
                assert file_dataset.data_headings == db_dataset.data_headings

    def test_4(self):
        # authentication of user and returns a token
        username = "test_user2"
        password = "wombat"
        ui = API_interface(path)
        ui.create_user(username_in=username, password_in=password, email="test_email", full_name="test_full_name")
        ui.generate_token(username, password)
        assert len(ui.token) > 0

    def test_5(self):
        # user 1 tree print
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        ui.generate_token(username=username, password=password)
        ui.tree_print()
        # user 2 tree print
        username = "test_user2"
        password = "wombat"
        ui.generate_token(username=username, password=password)
        ui.tree_print()


    def test_6(self):
        # uses the two previously created users to 
        ui = API_interface(path)
        project_name = "shared_project"
        file_name = "test.json"
        # user 1 variables
        username1 = "test_user"
        password1 = "some_password123"
        # authenticate
        ui.generate_token(username1, password1)
        # create a test project and insert it into the database using user 1 authentication.
        t.create_test_file_project(file_name,[2,3],project_name, username1)
        project_in = t.load_file_project(filename_out=file_name)
        ui.insert_project(project=project_in)

        # user 2 variables
        username2 = "test_user2"
        password2 = "wombat"
        # give user 2 access to the inserted project
        ui.add_author_to_project_rec(project_id=username2, author_name=username2, author_permission="read")
        print("User 1 print")
        ui.tree_print() # user 1 print
        
        ui.generate_token(username=username2, password=password2) # authenticates as user 2
        print("User 2 print")
        ui.tree_print() # user 2 print
    
    def test_7(self):
        ui = API_interface(path)
        ui.check_connection()
        ui.purge_everything()
        # convert ring
        # 7. return a project to compare with the file
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        file_name = "test_project.json"
        project_name = "test_project_1"
        # create user
        ui.create_user(username_in=username, password_in=password, email="emai@email.com", full_name="test user")
        ui.generate_token(username, password)
        # create project
        t.generate_optics_project(file_name, [1,1], project_name=project_name, experiment_name="test_experiment", author_name=username)
        project_from_file = t.load_file_project(filename_out=file_name)
        ui.insert_project(project_from_file)
        # return project
        project_from_db = ui.return_full_project(project_name=project_name)
        # load in the file
        project_from_file = t.load_file_project(filename_out=file_name)
        # compare assertions
        assert project_from_db.name == project_from_file.name
        assert project_from_db.meta == project_from_file.meta
        assert project_from_db.creator == project_from_file.creator
        assert project_from_db.author == project_from_file.author
        # compare experiments
        if project_from_file.groups == None or project_from_db.groups == None:
            raise Exception("")
        for i in range(0, len(project_from_file.groups)):
            file_experiment = project_from_file.groups[i]
            db_experiment = project_from_db.groups[i]
            # compare the experiment variables
            assert file_experiment.name == db_experiment.name
            assert file_experiment.author == db_experiment.author
            assert file_experiment.meta == db_experiment.meta
            for j in range(0, len(file_experiment.children)): # iterate over datasets
                file_dataset = file_experiment.children[j]
                db_dataset = db_experiment.children[j]
                assert file_dataset.name == db_dataset.name
                assert file_dataset.data == db_dataset.data
                assert file_dataset.data_type == db_dataset.data_type
                assert file_dataset.author == db_dataset.author
                assert file_dataset.data_headings == db_dataset.data_headings
        
    def test_8(self):
        # returning dataset with a meta data variable
        ui = API_interface(path)
        ui.check_connection()
        ui.purge_everything()
        # convert ring
        # 7. return a project to compare with the file
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        file_name = "test_project.json"
        project_name = "test_project_1"
        # create user
        ui.create_user(username_in=username, password_in=password, email="emai@email.com", full_name="test user")
        ui.generate_token(username, password)
        # create project
        t.generate_optics_project(file_name, [1,4], project_name=project_name, experiment_name="test_experiment", author_name=username)
        project_from_file = t.load_file_project(filename_out=file_name)
        # pull the datasets by ring_id
        ui.experiment_search_meta(meta_search={"ring_id" : 0} ,experiment_id="test_experiment", project_id=project_name)
        





#def test_9(self):
        # returning multiple datasets with meta variable

   # def test_10(self):
   #     # returning a ring from 

         
def main():
    test_class = TestClass()
    test_class.test_7()
main()
