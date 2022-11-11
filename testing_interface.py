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
        # uses the two previously created users to check if authors are added
        ui = API_interface(path)
        ui.purge_everything()

        project_name = "shared_project"
        file_name = "test.json"
        # create user 1
        username1 = "test_user"
        password1 = "some_password123"
        ui.create_user(username_in=username1, password_in=password1, email="test", full_name="test_name")
        
        # create user 2
        username2 = "test_user2"
        password2 = "wombat"
        ui.create_user(username_in=username2, password_in=password2, email="test", full_name="test_name")

        # authenticate as user 1
        ui.generate_token(username1, password1)
        # create a test project and insert it into the database using user 1 authentication.
        t.create_test_file_project(file_name,[1,1],project_name, username1)
        project_in = t.load_file_project(filename_out=file_name)
        ui.insert_project(project=project_in)


        # give user 2 access to the inserted project
        response = ui.add_author_to_project_rec(project_id=project_name, author_name=username2, author_permission="read")
        print(response)
        print("User 1 print")
        ui.tree_print() # user 1 print
        
        ui.generate_token(username=username2, password=password2) # authenticates as user 2
        print("User 2 print")
        ui.tree_print() # user 2 print

        # TODO: add assert statement once the query by author is working
    
    def test_7(self):
        # test whether generate optics experiment works properly as expected
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
        t.generate_optics_project(file_name, [1,1], project_name=project_name, experiment_name="test_experiment", author_name=username, size_of_dataset=1000)
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
            raise Exception("Missing groups")
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
        # test to check if a dataset is searched by meta variable
        # 1. Create an optics project with a ring
        # 2. Tree print
        # 3. Add a new dataset to an existing experiment
        # 4. return all datasets attached to the same ring_id
        # 5. verify the number of datasets is one bigger
        # returning dataset with a meta data variable
        ui = API_interface(path)
        ui.check_connection()
        ui.purge_everything()
        no_of_experiments = 1
        no_of_rings = 1
        ds_size = 1
        init_ring_doc_number = no_of_rings*4 # number 4 determined by the testing function
        # each ring generates 4 documents. 1 for dimensions and 3 for spectra
        # convert ring
        # 7. return a project to compare with the file
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        file_name = "test_project.json"
        project_name = "test_project_1"
        # create user
        ui.create_user(username_in=username, password_in=password, email="emai@email.com", full_name="test user")
        experiment_name = "test_experiment"
        # create project
        ui.generate_token(username, password)
        t.generate_optics_project(file_name, [no_of_rings,no_of_experiments], project_name=project_name, experiment_name=experiment_name, author_name=username, size_of_dataset=ds_size)
        project_from_file = t.load_file_project(filename_out=file_name)
        # insert the project
        ui.insert_project(project_from_file)
        # print the names of the structure
        ui.tree_print()
        # insert the additional dataset
        experiment_name = experiment_name + str(" 0") # appends to the first experiment
        dataset_temp = d.Dataset(name="special_spectrum",data=[1,2,3],data_type="special_spectrum",data_headings=["1D variable"],
                                 author=[d.Author(name=username, permission="write").dict()], meta={"ring_id" : int(no_of_rings-1)})
        ui.insert_dataset(project_name=project_name, experiment_name=experiment_name , dataset_in=dataset_temp)
        # appends to the last ring
        ui.tree_print()
        # TODO: modify the check_if_dataset_exists to handle exceptions if the names given are empty
        
        # pull the datasets by ring_id
        datasets = ui.experiment_search_meta(meta_search={"ring_id" : int(no_of_rings-1)} ,experiment_id=experiment_name, project_id=project_name)
        print(" ")
        print("datasets length: " + str(len(datasets)))
        assert len(datasets) == init_ring_doc_number + 1

    def test_9(self):
        # testing the group features and sharing
        # 1. create user_1 & user 2
        # 2. create 1 project for user_2
        # 3. create 3 projects for user_1
        # 4. Add one experiment, one dataset and one project to a group from
        # different projects
        # 5. Add author to group
        # 6. return group names using user_2
        ui = API_interface(path)
        ui.check_connection()
        ui.purge_everything()
        
        full_name = "test user full name"
        email = "email@email.com"
        # initialise users
        username = "user_1"
        password = "some_password123"
        ui.create_user(username, password, email, full_name)
        username2 = "user_2"
        ui.create_user(username2, password, email, full_name)
        ui = API_interface(path)
        file_name = "test_project.json"
        
        project_names = ["test_project_1","test_project_2","test_project_3","test_project_4"]
        ui.generate_token(username, password)
        username_temp = username
        for i in range(0, len(project_names),1):
            if i == 3:
                ui.generate_token(username2, password)
                username_temp = username2
            t.create_test_file_project(filename_in=file_name,structure=[2,2],project_name=project_names[i],author_name=username_temp)
            project = t.load_file_project(filename_out=file_name)
            ui.insert_project(project)

        # re-authenticate user_1
        print("user 2")
        ui.tree_print()
        print("generate token")
        ui.generate_token(username,password)
        print(" ")
        print("user 1")
        ui.tree_print()
        # add author to one project
        print("add author to project")
        
        ui.add_author_to_project_rec("test_project_1", author_name=username2, author_permission="read")
        ui.add_author_to_experiment_rec(project_id="test_project_2",experiment_id="experiment_0",author_name=username2, author_permission="read")
        ui.add_author_to_dataset_rec(project_id="test_project_3",experiment_id="experiment_0",dataset_id="dataset_0", author_name=username2 ,author_permissions="read")

        ui.tree_print()
        ui.generate_token(username2,password)
        ui.tree_print()

        temp = ui.author_query(username=username2)
        print(temp)

    def test_10(self):
        # testing groups
        # create 3 projects
        # append one dataset to group
        # append one experiment and all datasets to group
        # append one project to group and all experiments and datasets
        # fetch names of the group
        # add author to group
        ui = API_interface(path)
        ui.check_connection()
        ui.purge_everything()
        
        full_name = "test user full name"
        email = "email@email.com"
        # initialise users
        username = "user_1"
        password = "some_password123"
        ui.create_user(username, password, email, full_name)
        ui.generate_token(username, password)

        filename = "test_file.json"
        project_name = "test_project_"
        for i in range(0,1,1):
            t.create_test_file_project(filename_in=filename, structure=[1,1],project_name=project_name+str(i), author_name=username)
            project = t.load_file_project(filename_out=filename)
            ui.insert_project(project=project)
            # populate the database with 3 projects

        ui.tree_print()
        
        experiment_name = "experiment_0"
        dataset_name = "dataset_0"

        group_name = "test_group"
        # add single dataset to group
        #ui.add_group_to_dataset(author_permission="read",author_name=username,group_name=group_name,project_id="test_project_0",experiment_id=experiment_name, dataset_id=dataset_name)

        # add single experiment to group
        #ui.add_group_to_experiment(author_permission="read", author_name=username, group_name=group_name, project_id="test_project_1", experiment_id=experiment_name)

        # add single project to group
        #ui.add_group_to_project(author_permission="read", author_name=username, group_name=group_name, project_id="test_project_2")

        print("add_group_to_project_rec")
        print(ui.add_group_to_project_rec(project_id=project_name+"1",author_name=username,author_permission="read", group_name=group_name))

        temp = ui.author_query(username=group_name) # return the group names
        print(temp)

#    def test_9(self):
#        ui = API_interface(path)
#        ui.check_connection()
#        ui.purge_everything()


         
def main():
    test_class = TestClass()
    test_class.test_9()
main()
