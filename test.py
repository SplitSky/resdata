import json
import os
import testing as t
import jupyter_driver as jd
import testing as t
import interface as ui

path = "http://127.0.0.1:8000/"
username = "test_user1"
password = 'some_password'
email = 'email@email.com'
full_name = 'Test User'
file_name = "testing_data/json_version.json"
project_id = "Project_h5_Demo"
experiment_id = "Experiment_h5_Demo"
api = ui.API_interface(path)
api.purge_everything()
api.create_user(username_in=username, password_in=password, email=email, full_name=full_name)
api.generate_token(username, password)
#unique_keys = ["ring_ID", "sample_ID"]
max_ring_id = 20


file_name = jd.unpack_h5_custom_proj(file_name, username, project_id, experiment_id,max_ring_id)
project = t.load_file_project(filename_out=file_name)
#jd.send_datasets(username, password, path, project_id, experiment_id)
api.insert_project(project=project)
api.tree_print()



