import numpy as np
from src.map_instance import *

allowed_minute_input = [1, 5, 10, 60]
allowed_dataset_input = ['TBI', 'POP', 'PSL']

def loadBaseMap(dataset, minutes_per_node, image_folder):
    # Validate Input
    assert (dataset in allowed_dataset_input), 'Dataset must be one of: ' + str(allowed_dataset_input)
    assert (minutes_per_node in allowed_minute_input), 'Number of minutes must be one of: ' + str(allowed_minute_input)
    
    # Load Data
    data_file = open('data/{}_world_{}min.npz'.format(dataset, minutes_per_node), 'rb')
    data_2d = np.load(data_file)
    if not isinstance(data_2d, np.ndarray):
        data_2d = data_2d['data_matrix']
    data_file.close()

    # Set attributes for the map data
    attributes = {
        'minutes_per_node': minutes_per_node,
        'dataset': dataset.lower(),
        'image_folder': image_folder,
        'region': 'world',
    }

    # Build the map instance that keeps metadata
    [n_rows, n_cols] = data_2d.shape
    return MapInstance(attributes, n_rows, n_cols, data_2d.flatten())

def loadRegionMap(region, dataset, minutes_per_node, image_folder):
    world_map = loadBaseMap(dataset, minutes_per_node, image_folder)
    region_bounds = _loadRegionBounds(region, minutes_per_node)
    return world_map.newChildRegionInstance(region, region_bounds)
    
def _loadAllRegionsBounds():
    data_file = open('data/region_coordinates.csv', 'rb')
    data_regions = np.loadtxt(
        data_file, 
        delimiter=',',
        dtype={'names': ('continent', 'region_name', 'ymin', 'ymax', 'xmin', 'xmax', 'area'),
             'formats': ('S10', 'S17', 'i', 'i', 'i', 'i', 'i')},
        skiprows=1,
    )
    data_file.close()

    regions_bounds = {}
    for continent, region_name, ymin, ymax, xmin, xmax, _area in data_regions:
        regions_bounds[region_name.decode().strip()] = {'ymin': ymin, 'ymax': ymax, 'xmin': xmin, 'xmax': xmax}
    return regions_bounds

def _loadRegionBounds(region_name, minutes_per_node=5):
    regions_bounds = _loadAllRegionsBounds()
    
    region_bounds = regions_bounds[region_name]
    for key in region_bounds:
        region_bounds[key] //= minutes_per_node
    return region_bounds