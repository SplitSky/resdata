# this file is used by Jupyter to run commands used in analysis and streamlines the interface
import server.datastructure as d
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from typing import List
import testing as t

def plot_from_dataset(dataset : d.Dataset, label: str, title: str):
    # check dimensionality
    dims = len(dataset.data)

    if dataset.data_type in ["dimensions"]:
        # print out dimensions
        for i in range(0,len(dataset.data_headings),1):
            print(str(dataset.data_headings[i]) + " : " + str(dataset.data[i]))
    else:
        # plot out spectra
        if dims == 1:
            # 1D spectrum
            y = dataset.data
            x = np.arange(0,len(y))
            print("printing 1D spectrum")
            plt.xlabel = "number"
            plt.ylabel = dataset.data_headings[0]
            plt.title(title)
            plt.plot(x,y, label=label)
            plt.legend()

        elif dims == 2:
            # 2D plot 
            x,y = dataset.data
            print("printing 2D spectrum")
            plt.xlabel = dataset.data_headings[0]
            plt.ylabel = dataset.data_headings[1]
            plt.title(title)
            plt.plot(x,y, label=label)
            plt.legend()

        elif dims == 3:
            x, y, z = dataset.data
            print("Printing 2D spectrum with error bars")
            plt.xlabel = dataset.data_headings[0]
            plt.ylabel = dataset.data_headings[1]
            plt.plot(x,y)
            plt.title(title)
            plt.errorbar(x,y,z, label=label)
            plt.legend()

        else:
            raise Exception("the dimensionality too high")
        plt.show()

def summarise_dimensions(datasets: list[d.Dataset]):
    # generate the temp variable
    variable_keys = datasets[0].data_headings

    var_temp = []
    for entry in variable_keys:
        var_temp.append([])

    for dataset in datasets:
        for i in range(0,len(dataset.data_headings),1):
            var_temp[i].append(dataset.data[i])

    # calculate means and errors
    print("Average values for dimensions: ")
    i = 0
    for array in var_temp:
        mean = np.array(array).mean()
        std = np.array(array).std()
        print(f"{datasets[0].data_headings[i]} : {mean} +/- {std}")
        i += 1
       
def unpack_h5_custom_ds(json_file_name : str, username: str):
    max_ring_id = 12 # loads in 10 rings

    with open(json_file_name, "r") as file:
        data = file.readlines()
        file.close()
    data = data[0]
    json_data = json.loads(data)
    # NOTE: This data has badly labelled ring_ids. They are non-unique hence they are relabelled
    # TODO: bad way of doing it. to improve change to detect single values and arrays of 3D coordinates and add them to dimensions -> rest separate to spectra
    # dimension variables
    dimensions_keys = ['ring_ID', 'sample_ID', 'position', 'fluence', 'abs_position', 'thresh_est' ,'threshold', 'lasing_wavelength', 'mode_spacing', 'lasing_spacing_error', 'lasing_amplitude', 'field_ID', 'pos_rot', 'array_ID']
    spectra_keys = ['PL_screen', 'pdep', 'p', 'pint' ,'images', 'wl']
    
    author_temp = d.Author(name=username, permission="write")
    datasets = []
    # loop over ring_id and append the variables
    names = []

    ring_ID = 0
    for entry in json_data.get("ring_ID"):
        # unpack single ring
        print(f'ring_ID: {entry}')
        print(f'new_ring_ID: {ring_ID}')
        data_temp = []
        for heading in dimensions_keys:
            data_temp.append(json_data.get(heading)[ring_ID])
        #sample ID
        temp = json_data.get("sample_ID")
        dataset_temp = d.Dataset(name="ring_id " + str(ring_ID) + " dimensions", data=data_temp, meta={"old_ring_id" : entry, "ring_id" : ring_ID, "sample_id" : temp}, data_type="dimensions",author=[author_temp.dict()], data_headings=dimensions_keys)
        #datasets.append(dataset_temp)
        names.append(save_dataset(dataset_temp))
        append_name(names[len(names)-1])
        #send_datasets(dataset_temp)
        
        
        # append the spectra
        for spectrum_name in spectra_keys:
            data_temp = json_data.get(spectrum_name)[ring_ID]

            # TODO: check entry dimensionality
            temp = "spectrum"
            dataset_temp = d.Dataset(name="ring_id " + str(ring_ID) + " - " + spectrum_name, data=data_temp, meta={"old_ring_id" : entry, "ring_id" : ring_ID}, author=[author_temp.dict()], 
                                     data_headings=[spectrum_name], data_type=temp)
            #datasets.append(dataset_temp)
            names.append(save_dataset(dataset_temp))
            append_name(names[len(names)-1])
            #send_datasets(dataset_temp)
        ring_ID += 1
        if ring_ID > max_ring_id:
            return names
    return names

def unpack_h5_custom_ex(json_file_name : str, username: str):
    # instead of saving individual datasets saves each ring as experiment
    max_ring_id = 12 # loads in 10 rings

    with open(json_file_name, "r") as file:
        data = file.readlines()
        file.close()
    data = data[0]
    json_data = json.loads(data)
    # NOTE: This data has badly labelled ring_ids. They are non-unique hence they are relabelled

    dimensions_keys = ['ring_ID', 'sample_ID', 'position', 'fluence', 'abs_position', 'thresh_est' ,'threshold', 'lasing_wavelength', 'mode_spacing', 'lasing_spacing_error', 'lasing_amplitude', 'field_ID', 'pos_rot', 'array_ID']
    spectra_keys = ['PL_screen', 'pdep', 'p', 'pint' ,'images', 'wl']
    
    author_temp = d.Author(name=username, permission="write")
    datasets = []
    # loop over ring_id and append the variables
    names = []
    print(f'ring_id: {len(json_data.get("ring_ID"))}')

    for key in json_data.keys():
        print(f'{key} : {len(json_data.get(key))}')

    ring_ID = 0
    for entry in json_data.get("ring_ID"):
        # unpack single ring
        print(f'ring_ID: {entry}')
        print(f'new_ring_ID: {ring_ID}')
        data_temp = []
        for heading in dimensions_keys:
            data_temp.append(json_data.get(heading)[ring_ID])
        #sample ID
        temp = json_data.get("sample_ID")
        dataset_temp = d.Dataset(name="ring_id " + str(ring_ID) + " dimensions", data=data_temp, meta={"old_ring_id" : entry, "ring_id" : ring_ID, "sample_id" : temp}, data_type="dimensions",author=[author_temp.dict()], data_headings=dimensions_keys)
        #datasets.append(dataset_temp)
        names.append(save_dataset(dataset_temp))
        append_name(names[len(names)-1])
        #send_datasets(dataset_temp)
        
        
        # append the spectra
        for spectrum_name in spectra_keys:
            data_temp = json_data.get(spectrum_name)[ring_ID]

            # TODO: check entry dimensionality
            temp = "spectrum"
            dataset_temp = d.Dataset(name="ring_id " + str(ring_ID) + " - " + spectrum_name, data=data_temp, meta={"old_ring_id" : entry, "ring_id" : ring_ID}, author=[author_temp.dict()], 
                                     data_headings=[spectrum_name], data_type=temp)
            #datasets.append(dataset_temp)
            names.append(save_dataset(dataset_temp))
            append_name(names[len(names)-1])
            #send_datasets(dataset_temp)
        ring_ID += 1
        if ring_ID > max_ring_id:
            return names
    return names


def unpack_h5_custom_proj(json_file_name : str, username: str, project_name : str, experiment_name : str, max_ring_id : int):
    # instead of saving individual datasets saves the data fully into one project

    with open(json_file_name, "r") as file:
        data = file.readlines()
        file.close()
    data = data[0]
    json_data = json.loads(data)
    # NOTE: This data has badly labelled ring_ids. They are non-unique hence they are relabelled

    dimensions_keys = ['ring_ID', 'sample_ID', 'position', 'fluence', 'abs_position', 'thresh_est' ,'threshold', 'lasing_wavelength', 'mode_spacing', 'lasing_spacing_error', 'lasing_amplitude', 'field_ID', 'pos_rot', 'array_ID']
    spectra_keys = ['PL_screen', 'pdep', 'p', 'pint' ,'images', 'wl']
    
    author_temp = [d.Author(name=username, permission="write").dict()]
    experiment = d.Experiment(name=experiment_name, children=[], author=author_temp)
    project = d.Project(name=project_name, creator=username,groups=[],author=author_temp)
    # loop over ring_id and append the variables
    names = []
    print(f'ring_id: {len(json_data.get("ring_ID"))}')

    for key in json_data.keys():
        print(f'{key} : {len(json_data.get(key))}')

    ring_ID = 0
    for entry in json_data.get("ring_ID"):
        # unpack single ring
        print(f'ring_ID: {entry}')
        print(f'new_ring_ID: {ring_ID}')
        data_temp = []
        for heading in dimensions_keys:
            data_temp.append(json_data.get(heading)[ring_ID])
        #sample ID
        temp = json_data.get("sample_ID")
        dataset_temp = d.Dataset(name="ring_id " + str(ring_ID) + " dimensions", data=data_temp, meta={"old_ring_id" : entry, "ring_id" : ring_ID, "sample_id" : temp}, data_type="dimensions",author=author_temp, data_headings=dimensions_keys)
        
        experiment.children.append(dataset_temp) 

        # append the spectra
        for spectrum_name in spectra_keys:
            data_temp = json_data.get(spectrum_name)[ring_ID]
            temp = "spectrum"
            dataset_temp = d.Dataset(name="ring_id " + str(ring_ID) + " - " + spectrum_name, data=data_temp, meta={"old_ring_id" : entry, "ring_id" : ring_ID}, author=author_temp, 
                                     data_headings=[spectrum_name], data_type=temp)
            #datasets.append(dataset_temp)
            experiment.children.append(dataset_temp)
        ring_ID += 1
        if ring_ID > max_ring_id:
            # wrap the experiment in a project
            project.groups=[experiment]
            t.save_file_project(file_name=project_name+".json", project=project)
            return project_name+".json"


def unpack_h5(json_file_name: str, username: str, unique_keys: List[str]):
    # attempt to load data into json variable
    names = []
    max_ring_id = 10
    try:
        with open(json_file_name, "r") as file:
            data = file.readlines()
            file.close()
        data = data[0]
        json_data = json.loads(data)
    except:
        raise Exception("The file couldn't be opened.")
    # verify that the keys in the unique keys are unique
    if len(unique_keys) > 1:
        # combination of two keys is unique
        # re-label the names
        # check the length of the unique_keys is the same
        temp = len(json_data.get(unique_keys[0]))
        for i in range(1,len(unique_keys)):
            if temp != len(json_data.get(unique_keys[i])):
                raise Exception("The size arrays of the unique keys do not match")
    relabel = False
    unique_ids = []
    for i in range(0,len(json_data.get(unique_keys[0])),1):
        temp_string = ""
        for key in unique_keys:
            temp_string += str(json_data.get(key))
        unique_ids.append(temp_string)

    if not len(set(unique_ids)) == len(unique_ids):
        # the unique keys are not unique. Relabel
        #print("The keys given are not unique. Relabelling. The keys provided will be appended to meta data.")
        relabel = True
        # still add them to meta data
            

    # unpack and save the datasets into a series of documents.
    # while relabelling the names to keep them unique
    # purge the working directory
    def clean_up():
        try:
            my_dir = "cache"
            file_list = [f for f in os.listdir(my_dir) if f.endswith(".json") or f.endswith(".txt")]
            for f in file_list:
                os.remove(os.path.join(my_dir, f))
        except:
            raise Exception("cache directory is missing")
    clean_up()

    ring_ID = 0
    author_temp = [d.Author(name=username, permission="write").dict()]
    keys_list = json_data.keys()

    for item_id in json_data.get(unique_keys[0]):
        # loop over the unique key
        unique_name = ""
        meta = {}
        if relabel==False:
            unique_name = f'{unique_keys[0]} : {unique_ids[ring_ID]}'
            for key in unique_keys:
                meta[key]=json_data.get(key)
        else:
            unique_name = unique_keys[0] + str(ring_ID)
            meta["relabelled"]=True # append a flag to the meta data
        # create dimensions dataset
        dimensions_dataset = d.Dataset(name=unique_name, data=[], meta=meta, author=author_temp,data_headings=[], data_type="dimensions")
        #spectrum_datasets = []
        for dataset_key in keys_list: 
            # loop over each key of the data except the unique ones
            data_temp = json_data.get(dataset_key)[ring_ID] # extract the data from json
            if type(data_temp) != list or (type(data_temp) == list and len(data_temp)<3):
                # append as a separte dataset
                meta_temp = meta 
                meta_temp["parent_dataset" : unique_name]
                #spectrum_datasets.append(
                temp = d.Dataset(name=unique_name + " - " +str(dataset_key), data=data_temp, author=author_temp, data_headings=[dataset_key], data_type="spectrum", meta=meta_temp)
                # save spectrum dataset
                names.append(save_dataset(temp))
                append_name(names[len(names)-1])
            else:
                # append to dimensions
                dimensions_dataset.data.append(data_temp)
                dimensions_dataset.data_headings.append(dataset_key)
        #save dimensions dataset as all data has been processed
        names.append(save_dataset(dimensions_dataset))
        append_name(names[len(names)-1])
        
        if ring_ID > max_ring_id:
            break # breaks the loop to prevent crashing for development
        ring_ID += 1
        #end for
    return names

# save datasets unpacked into individual .json files
def save_dataset(dataset_in: d.Dataset):
    filename = dataset_in.name + ".json"
    with open(filename, "w") as f:
        json.dump(dataset_in.convertJSON(), f)
        f.close()
    return filename

def append_name(name: str):
    file_name_temp = "names.txt"
    with open(file_name_temp, "w+") as f:
        f.write(name)
        f.write('\n')
        f.close()


def send_datasets(username: str, password: str, path:str, project_id: str, experiment_id: str):
    import testing as t
    # declaration of variables used
    import interface as ui
    api = ui.API_interface(path)
    api.generate_token(username=username, password=password)
    # read in the names
    print("Reading names in")
    with open("names.txt", "r") as f:
        names = f.readlines()
        f.close()
    # insert the datasets
    counter = 0
    for name in names:
        name_temp = name[:len(name)-1] # cut off \n
        dataset_in = t.load_file_dataset(name_temp)
        print(f'dataset_name: {dataset_in.name}')
        api.insert_dataset_safe(project_name=project_id, experiment_name=experiment_id, dataset_in=dataset_in)
        counter+=1
        if counter > 100:
            api.tree_print()
            raise Exception("Stop before it crashes")


