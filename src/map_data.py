import numpy as np
from src.map_instance import *

def loadBaseMap(dataset, minutes_per_node, image_folder):
    data_file = open('data/{}_world_{}min.npz'.format(dataset, minutes_per_node), 'rb')
    data_2d = np.load(data_file)['data_matrix']
    data_file.close()
    
    attributes = {
        'minutes_per_node': minutes_per_node,
        'dataset': dataset.lower(),
        'image_folder': image_folder,
        'region': 'world',
    }
    [n_rows, n_cols] = data_2d.shape
    return MapInstance(attributes, n_rows, n_cols, data_2d.flatten())
    