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
names = d.unpack_h5_custom(file_name, username) # unpacks the rings
d.send_datasets() # sends the rings to the database

