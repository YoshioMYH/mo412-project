import glob
import pickle

from main import ExtendedPublication

path_to_publications = "./data/publications/*.pkl"

files = glob.glob(path_to_publications)

for file in files:
    with open(file, 'rb') as f:
        pub = pickle.load(f)
        print(pub)
