import testing as t
from interface import API_interface
import server.datastructure as d
path = "http://127.0.0.1:8000/"
#path = "http://10.99.96.185/"
import time
from os.path import exists
import jupyter_driver as jd
import simple_interface as s
from datetime import datetime, timedelta

# tests to conduct


# 3. returning a project using that user
# 4. tree print
# 5. creating a user and inserting a second project
# 6. giving the second user permissions to one of the datasets + tree print to confirm
# 7. trying to insert nothing
# 8. updating permissions for user 2 -> making it able to edit project belonging to user 1
# 9. User 2 authenting and inserting a dataset in project belonging to user 1
# 10. User 2 insert dataset into experiment with read only permissions # TODO: This feature may not work but should be updated later

cache_status = True

# functions used to simplify the testing
def send_fetch_cycle(dataset_size, structure, array_var_type, cache=False, fast=False):
    # dataset_size - indicates the size of the document that is produced
    # structure - [x,y] -> x = number of experiments; y = number of documents
    # array_var_type - the type of the number within the 
    #print('Fetch cycle')
    username = "test_user"
    password = "some_password123"
    ui = API_interface(path, user_cache=cache)
    ui.purge_everything()
    ui.create_user(username, password, "email", "full_name")
    #create user
    ui.generate_token(username, password) # authenticate the user
    # generate test_project
    file_name = "test_project.json"
    project_name = "test_project_1"
    t.create_test_file_project_time(filename_in=file_name, structure=structure, project_name=project_name, author_name=username, dataset_size=dataset_size ,variable_type=array_var_type)
    project_in = t.load_file_project(filename_out=file_name)
    # insert project
     
    if fast:
        start = time.perf_counter() # start timing the function
        ui.insert_project_fast(project=project_in)
        ui.return_full_project(project_name=project_name)
        end = time.perf_counter()
    else:
        start = time.perf_counter()
        ui.insert_project(project=project_in)
        ui.return_full_project(project_name=project_name)
        end = time.perf_counter()

    difference = (end - start)
    #print("Difference: " + str(difference))
    return difference

class TestClass:
    def test_0(self):
        # check connection
        ui = API_interface(path, user_cache=cache_status)
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
        ui = API_interface(path, user_cache=cache_status)
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
        ui = API_interface(path,user_cache=cache_status)
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
        ui = API_interface(path,user_cache=cache_status)
        ui.create_user(username_in=username, password_in=password, email="test_email", full_name="test_full_name")
        ui.generate_token(username, password)
        assert len(ui.token) > 0

    def test_5(self):
        # user 1 tree print
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path,user_cache=cache_status)
        ui.generate_token(username=username, password=password)
        #ui.tree_print()
        # user 2 tree print
        username = "test_user2"
        password = "wombat"
        ui.generate_token(username=username, password=password) 
        #ui.tree_print()


    def test_6(self):
        # uses the two previously created users to check if authors are added
        ui = API_interface(path,user_cache=cache_status)
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
        #ui.tree_print() # user 1 print
        project_user_1 = ui.return_full_project(project_name=project_name)
        
        ui.generate_token(username=username2, password=password2) # authenticates as user 2
        print("User 2 print")
        #ui.tree_print() # user 2 print
        project_user_2 = ui.return_full_project(project_name=project_name)
        assert project_user_1 == project_user_2

        # TODO: add assert statement once the query by author is working
    
    def test_7(self):
        # test whether generate optics experiment works properly as expected
        ui = API_interface(path,user_cache=cache_status)
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
        ui = API_interface(path,user_cache=cache_status)
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
        ui = API_interface(path,user_cache=cache_status)
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

        #ui.tree_print()
        ui.generate_token(username2,password)
        ui.tree_print()

        temp = ui.author_query(username=username2)
        print(temp)

    def test_10(self):
        # testing the author query function
        ui = API_interface(path,user_cache=cache_status)
        ui.check_connection()
        ui.purge_everything()
        
        full_name = "test user full name"
        email = "email@email.com"
        # initialise users
        username = "user_1"
        password = "some_password123"
        ui.create_user(username, password, email, full_name)
        ui = API_interface(path)
        file_name = "test_project.json"
        
        project_number = 1
        experiment_number = 2
        dataset_number = 3
        project_name = "test_project"

        ui.generate_token(username, password)
        t.create_test_file_project(filename_in=file_name,structure=[experiment_number,dataset_number],project_name=project_name,author_name=username)
        project = t.load_file_project(filename_out=file_name)
        ui.insert_project(project)

        ui.tree_print()

        temp = ui.author_query(username=username)
        print(temp)
        project_count = len(temp)
        experiment_count = 0
        dataset_count = 0
        
        for project in temp:
            for experiment in project.get("experiment_list"):
                experiment_count += 1
                for dataset in experiment.get("dataset_list"):
                    dataset_count += 1

        assert project_count == project_number
        assert experiment_count == experiment_number
        assert dataset_count == dataset_number*experiment_number


    def test_11(self):
        # testing groups
        # create 3 projects
        # append one dataset to group
        # append one experiment and all datasets to group
        # append one project to group and all experiments and datasets
        # fetch names of the group
        # add author to group
        ui = API_interface(path,user_cache=cache_status)
        ui.check_connection()
        ui.purge_everything()
        
        full_name = "test user full name"
        email = "email@email.com"
        # initialise users
        username = "user_1"
        password = "some_password123"
        ui.create_user(username, password, email, full_name)
        ui.generate_token(username, password)
        project_number = 3
        experiment_number = 2
        dataset_number = 2
        filename = "test_file.json"
        project_name = "test_project_"
        for i in range(0,project_number,1):
            t.create_test_file_project(filename_in=filename, structure=[experiment_number,dataset_number],project_name=project_name+str(i), author_name=username)
            project = t.load_file_project(filename_out=filename)
            ui.insert_project(project=project)
            # populate the database with 3 projects

        print("Initial tree print")
        ui.tree_print()
        
        experiment_name = "experiment_0"
        dataset_name = "dataset_0"
        group_name = "test_group"
        
        # counting the entries added to the author
        temp = ui.author_query(username=username)
        print("author query ")
        print(temp)
        project_count = len(temp)
        experiment_count = 0
        dataset_count = 0
        for project in temp:
            for experiment in project.get("experiment_list"):
                experiment_count += 1
                for dataset in experiment.get("dataset_list"):
                    dataset_count += 1

        assert project_count == project_number
        assert experiment_count == experiment_number*project_number
        assert dataset_count == dataset_number*experiment_number*project_number

        # verifies the datasets inserted

        # adding things to the group
        # counting variables for verification
        project_count_group = 0
        experiment_count_group = 0
        dataset_count_group = 0

        # add single dataset to group
        ui.add_group_to_dataset_rec(author_permission="write",author_name=username,group_name=group_name,project_id="test_project_0",experiment_id=experiment_name, dataset_id=dataset_name)
        # dataset_count: +1
        dataset_count_group += 1
        # project_counit: +1
        project_count_group += 1
        # experiment_count: +1
        experiment_count_group += 1

        # add single experiment to group
        temp = ui.add_group_to_experiment_rec("test_project_1", experiment_name, username, "write", group_name)
        # dataset_count: +1
        dataset_count_group += 1*dataset_number
        # experiment_count: +1
        experiment_count_group += 1
        # project_count: +1
        project_count_group += 1

        # add single project to group
        assert ui.add_group_to_project_rec(project_id=project_name+"2",author_name=username,author_permission="write", group_name=group_name) == True
        # project_count_group: +1
        project_count_group += 1
        # experiment_count_group: +experiment_number
        experiment_count_group += experiment_number
        # dataset_count_group: + experiment_number*dataset_number
        dataset_count_group += (experiment_number*dataset_number)

        # verify the number in the group
        temp = []
        temp = ui.author_query(username=group_name)
        print(temp)
        project_count = len(temp)
        experiment_count = 0
        dataset_count = 0
        for project in temp:
            for experiment in project.get("experiment_list"):
                experiment_count += 1
                for dataset in experiment.get("dataset_list"):
                    dataset_count += 1

        print("counting")
        print("project_count: " + str(project_count))
        print("experiment_count: " + str(experiment_count))
        print("dataset_count: " + str(dataset_count))
        print("group counting")
        print("project_count: " + str(project_count_group))
        print("experiment_count: " + str(experiment_count_group))
        print("dataset_count: " + str(dataset_count_group))      


        assert project_count == project_count_group
        assert experiment_count == experiment_count_group
        assert dataset_count == dataset_count_group

    def test_12(self):
        # tests creation and insertion of images
        file_name = "test_cat.jpg"
        ui = API_interface(path,user_cache=cache_status)
        arr, data_type = ui.convert_img_to_array(filename=file_name)
        cat_img = ui.convert_array_to_img(arr, "test_cat2.jpg",str(data_type))
        assert cat_img == True
        assert exists("images/test_cat2.jpg") == True 

    def test_13(self):
        # test the API handling of images
        file_name = "test_cat.jpg"
        ui = API_interface(path,user_cache=cache_status)
        ui.purge_everything()
        #arr, data_type = ui.convert_img_to_array(filename=file_name)

        # create a project and send the dataset
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path)
        ui.create_user(username_in=username, password_in=password, email="a", full_name="a")
        ui.generate_token(username, password)
        # generate test_project
        file_name = "test_project.json"
        project_name = "test_project_1"
        experiment_name = "experiment_0"
        dataset_name = "image_test"
        picture_file_name = "test_cat.jpg"
        final_picture_name = "test_cat2.jpg"
        t.create_test_file_project(filename_in=file_name, structure=[1,1], project_name=project_name, author_name=username)
        project_in = t.load_file_project(filename_out=file_name)
        assert ui.insert_project(project=project_in) == True
        
        # insert an additional dataset
        dataset_in = ui.generate_dataset_for_img(file_name=picture_file_name, dataset_name=dataset_name)
        ui.insert_dataset(project_name, experiment_name,dataset_in)
        ui.tree_print()

        # return previous dataset to confirm return_dataset works
        dataset = ui.return_full_dataset(project_name=project_name, experiment_name=experiment_name, dataset_name="dataset_0")
        if dataset == False:
            print("Failed")
        else:
            print(f'dataset name: {dataset.name}')
        dataset = ui.return_full_dataset(project_name=project_name, experiment_name=experiment_name,dataset_name=dataset_name)
        assert dataset != False

        # confirm the datasets are the same
        temp, data_type = ui.convert_img_to_array(filename=picture_file_name)
        for i in range(0,len(temp)):
            assert temp[i] == dataset.data[i]
        assert dataset.data == temp
        temp2 = ui.generate_img_from_dataset(file_name=final_picture_name, dataset_in=dataset)
        assert temp2 == True

    def test_14(self):
        # load H5 file using custom function and populate the database. Then summarise data quantities.
        username = "test_user1"
        password = 'some_password'
        email = 'email@email.com'
        full_name = 'Test User'
        file_name = "testing_data/json_version.json"
        project_id = "Project_h5_Demo"
        experiment_id = "Experiment_h5_Demo"
        api = API_interface(path,user_cache=cache_status)
        api.purge_everything()
        api.create_user(username_in=username, password_in=password, email=email, full_name=full_name)
        api.generate_token(username, password)
        #unique_keys = ["ring_ID", "sample_ID"]
        max_ring_id = 5
        file_name = jd.unpack_h5_custom_proj(file_name, username, project_id, experiment_id, max_ring_id=max_ring_id)
        project = t.load_file_project(filename_out=file_name)
        #jd.send_datasets(username, password, path, project_id, experiment_id)
        api.insert_project(project=project)
        temp = api.get_dataset_names(project_id=project_id, experiment_id=experiment_id)
        assert len(temp) == (max_ring_id+1)*2 + 1
    
    def test_15(self):
        # return a project to compare with the file
        # 2. inserting a project using that user
        username = "test_user"
        password = "some_password123"
        ui = API_interface(path,user_cache=cache_status)
        ui.purge_everything() 
        ui.create_user(username, password, "aaa", "aaa")
        ui.generate_token(username, password)
        # generate test_project
        file_name = "test_project.json"
        project_name = "test_project_1"
        t.create_test_file_project(filename_in=file_name, structure=[1,1], project_name=project_name, author_name=username)
        project_in = t.load_file_project(filename_out=file_name)
        print(project_in.json())
        assert ui.insert_project_fast(project=project_in) == True

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

            print(file_experiment.author)
            print(db_experiment.author)
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

    def test_16(self):
        # testing the multithreading insertion functions
        ui = API_interface(path,user_cache=cache_status)
        ui.check_connection()
        ui.purge_everything() # clear the database
        no_of_experiments = 1
        no_of_datasets = 1
        ds_size = 100
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
        t.create_test_file_project(filename_in=file_name, structure=[no_of_experiments, no_of_datasets], project_name=project_name, author_name=username)
        project_from_file = t.load_file_project(filename_out=file_name)
        # insert the project
        ui.insert_project_fast(project_from_file) # the project function uses the fast dataset and experiment functions

        # return project
        project_from_db = ui.return_full_project(project_name=project_name)
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
            print(file_experiment.author)
            print(db_experiment.author)
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

    def test_17(self):
        #thing
        ui = API_interface(path,user_cache=True)
        ui.check_connection()
        ui.purge_everything() # clear the database
        username = "thing"
        password = "thing"
        email = "a"
        full_name = "a"
        ui.create_user(username_in=username, password_in=password, email=email, full_name=full_name)
        ui.generate_token(username, password)
        file_name = "test_project.json"
        project_name = "test_project_1"
        # return project
        t.create_test_file_project(filename_in=file_name, structure=[1,1], project_name=project_name, author_name=username)
        project_from_file = t.load_file_project(filename_out=file_name)
        ui.insert_project(project=project_from_file)
        # project_from_db = ui.return_full_project(project_name=project_name)
        # load in the file

    def test_18(self):
        temp = API_interface(path_in=path, user_cache=True)
        temp.purge_everything()
        username = "test_user"
        password = "some_password"

        easy_ui = s.User_Interface(path)
        easy_ui.create_user(username=username, password=password, full_name="name", email="email")
        easy_ui.user_authenticate(username, password)

        # data insertion using simple ui
        project_name = "project_test"
        project_meta = {"project_meta": "project metadata value"}
        experiment_name = "experiment_test"
        experiment_meta = {"experiment_meta": "experiment metadata value"}
        dataset_name = "dataset_test"
        dataset_meta = {"dataset_meta": "dataset metadata value"}
        dataset_payload = [1,2,3,4,5]
        data_type = "testing data"
        data_headings = ["data_heading"]

        dataset_in = easy_ui.insert_dataset(project_name=project_name, experiment_name=experiment_name, dataset_name=dataset_name, payload=dataset_payload, meta=dataset_meta, data_type=data_type, data_headings=data_headings)
        # insert dataset locally without experiment/project path
        # sync the data with the API
        easy_ui.sync_data()
        # verify the data inserted matches
        easy_ui.api.tree_print()
        dataset_out = easy_ui.return_dataset(project_name, experiment_name, dataset_name)
        assert dataset_in.name == dataset_out.name
        assert dataset_in.data == dataset_out.data
        assert dataset_in.data_type == dataset_out.data_type
        assert dataset_in.author == dataset_out.author
        assert dataset_in.data_headings == dataset_out.data_headings

    def test_19(self):
        # test for calculating timing complexity
       # print("size of dataset dependent on time")
       # times = []
       # times2 = []
       # times3 = []
       # x = []
       # for i in range(0,100000,10000):
       #     x.append(i)
       #     times.append(send_fetch_cycle(i, structure=[1,1],array_var_type="int", cache=True, fast=True))
       #     times2.append(send_fetch_cycle(i, structure=[1,1],array_var_type="int", cache=True, fast=False))
       #     times3.append(send_fetch_cycle(i, structure=[1,1],array_var_type="int", cache=False, fast=False))
       # print(x)
       # print(times)
       # print(times2)
       # print(times3)
       # # measure the number of datasets dependence on N

       # x = []
       # times = []
       # times2 = []
       # times3 = []
       # for i in range(0,30,1):
       #     x.append(i)
       #     times.append(send_fetch_cycle(100, structure=[1,i],array_var_type="int", cache=True, fast=True))
       #     times2.append(send_fetch_cycle(100, structure=[1,i],array_var_type="int", cache=True, fast=False))
       #     times3.append(send_fetch_cycle(100, structure=[1,i],array_var_type="int", cache=False, fast=False))           
       # print(x)
       # print(times)
       # print(times2)
       # print(times3)

        x = []
        times = []
        times2 = []
        times3 = []
       # for i in range(1,10,1):
       #     x.append(i)
       #     times.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=True, fast=True))
       #     times2.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=True, fast=False))
       #     times3.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=False, fast=False))           
       # print(x)
       # print(times)
       # print(times2)
       # print(times3)

       # for i in range(10,15,1):
       #     x.append(i)
       #     times.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=True, fast=True))
       #     times2.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=True, fast=False))
       #     times3.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=False, fast=False))           
       # print(x)
       # print(times)
       # print(times2)
       # print(times3)

        for i in range(15,30,6):
            x.append(i)
            times.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=True, fast=True))
            print("sleep")
            time.sleep(2)
            times2.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=True, fast=False))
            print("sleep")
            time.sleep(2)
            times3.append(send_fetch_cycle(100, structure=[i,5],array_var_type="int", cache=False, fast=False))           
            print("sleep")
            time.sleep(2)
        print(x)
        print(times)
        print(times2)
        print(times3)



    def test_20(self):
        i = 10
        send_fetch_cycle(10000, structure=[1,i],array_var_type="int")

        print("gap")
        send_fetch_cycle(10000, structure=[1,i], array_var_type="int", cache=True)
        print("gap")
        send_fetch_cycle(10000, structure=[1,i], array_var_type="int", cache=True, fast=True)

def main():
    test_class = TestClass()
    test_class.test_19()
main()
