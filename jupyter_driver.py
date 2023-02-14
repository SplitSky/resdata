# this file is used by Jupyter to run commands used in analysis and streamlines the interface
import server.datastructure as d
import matplotlib.pyplot as plt
import numpy as np

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
        
