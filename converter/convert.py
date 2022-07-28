import datastructure as d
import h5py as h








def main():
    filename = "nanowire_data.h5"
    f = h.File(filename, 'r')
    # print keys
    print(list(f.keys()))

    # access experiments by f[experiment_id]


main()
