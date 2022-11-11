# this file is used by Jupyter to run commands used in analysis and streamlines the interface
import datastructure as d
import matplotlib.pyplot as plt
import numpy as np

def plot_from_dataset(dataset : d.Dataset):
    # check dimensionality
    dims = len(dataset.data)

    if dataset.data_type in ["dimensions"]:
        # print out dimensions
        for i in range(0,len(dataset.data_headings),1):
            print(dataset.data_headings[i] + " : " + dataset.data[i])
    else:
        # plot out spectra
        if dims == 1:
            # 1D spectrum
            y = dataset.data
            x = np.arange(0,len(y))
            print("printing 1D spectrum")
            plt.plot(x,y)

        elif dims == 2:
            # 2D plot 
            x,y = dataset.data
            print("printing 2D spectrum")
            plt.plot(x,y)

        elif dims == 3:
            x, y, z = dataset.data
            print("Printing 3D specturm")
            plt.plot(x,y,z)

        else:
            raise Exception("the dimensionality too high")
