import json
import os
import testing as t
import jupyter_driver as d
import testing as t
import interface as ui

## Sing in and Authentication
username = "S_Church"
password = 'some_password'
email = 'email@test_email.com'
full_name = 'Tomasz Neska'
path = 'http://127.0.0.1:8000/'
file_name = "json_version.json"
# declaration of variables used

def clean_up():
    dir_name = "/home/splitsky/Desktop/code_repositories/resdata/"
    test = os.listdir(dir_name)
    for item in test:
        if item.endswith(".json") and item != "json_version.json":
            os.remove(os.path.join(dir_name, item))
api = ui.API_interface(path)
api.purge_everything()
api.create_user(username_in=username, password_in=password, email=email, full_name=full_name)
api.generate_token(username=username, password=password)
names = d.unpack_h5_custom(file_name, username)


#print(f'number of files: {len(names)}')
## save names for future use
#file_name_temp = "names.txt"
#with open(file_name_temp, "w+") as f:
#    for name in names:
#        f.write(name)
#        f.write('\n')
#    f.close()
#
## API bits
## initialisation cell
#import sys
#sys.path.insert(0, "/home/splitsky/Desktop/code_repositories/resdata/")
#import interface as ui
#api = ui.API_interface(path)
#api.check_connection()
#api.purge_everything() ## clean up
##purge call - comment out if necessary -> just for development
#api.purge_everything()
## make user
#result = api.create_user(username_in=username, password_in=password,email=email,full_name=full_name)
#print("User created "  + str(result))
#api.generate_token(username=username, password=password)
#
#project_name = "h5_demo_proj"
#experiment_name ="h5_demo_exp"
#
## read in the names
#with open("names.txt", "r") as f:
#    names = f.readlines()
#    print("names: ")
#    print(names)
#    f.close()
## insert the billion datasets
#counter = 0
#for name in names:
#    name_temp = name[:len(name)-1]
#    dataset_in = t.load_file_dataset(name_temp)
#    print(dataset_in)
#    api.insert_dataset(project_name=project_name, experiment_name=experiment_name, dataset_in=dataset_in)
#    counter+=1
#    if counter > 100:
#        clean_up()
#        api.tree_print()
#        raise Exception("Stop before it crashes")
#
## clean up

