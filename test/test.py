import h5py
import io
import numpy as np

f = h5py.File("myfile.h5", 'w')
#dset = f.create_dataset("dataset1", (100,), dtype="i")
grp = f.create_group("info")
arr = np.arange(100)
dataset1 = grp.create_dataset("dataset1", data=arr)
dataset2 = grp.create_dataset("dataset2", data=arr)

grp2 = f.create_group("nanowires")
arr = np.arange(100)
dataset3 = grp2.create_dataset("dataset3", data=arr)
dataset4 = grp2.create_dataset("dataset4", data=arr)

f.close()
