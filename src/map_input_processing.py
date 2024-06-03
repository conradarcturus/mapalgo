##
# This contains many methods that help generate processed data from input data
#

import numpy as np
from src import map_instance, map_image, map_transforms, map_data

def drawBasicValueMap(
    map_elevation, # type map_instance
):
    maps = {}
    maps['elevation'] = map_elevation
    maps['hillshade'] = map_transforms.getHillshade(maps['elevation'], 1)
    maps['sea']  = maps['elevation'].newChildInstance(
        {'values': 'zero_pop'},
        maps['elevation'].getDataFlat() < 0,
    )
    maps['coast'] = map_transforms.getBorder(maps['sea'], 1)

    data_elevation_sqrt = maps['elevation'].getDataFlat()
    data_elevation_sqrt = np.sign(data_elevation_sqrt) * (np.abs(data_elevation_sqrt) ** 0.5)

    map_image.RasterImage(maps['elevation']) \
        .addLayer('elevation', data_elevation_sqrt, colormap='naturalish') \
        .addLayer('sea', 1.2, nodes_selected=maps['sea'].getDataFlat(), combine='add', dissolve=.2) \
        .addLayer('hillshade', maps['hillshade'].getDataFlat(), combine='add', opacity=1, dissolve=1) \
        .addLayer('coast', 0.2, nodes_selected=maps['coast'].getDataFlat(), combine='multiply') \
        .overrideLayerNames(['value']) \
        .display().save().final()
    

def processBinaryDataFileToNPZ( 
    input_folder,
    image_folder, # eg. img/##/
    dataset = 'TBI', # The original data from https://ddfe.curtin.edu.au/models/ has forms BED, ICE, RET, SUR, and TBI
    minutes_per_node = 1, # only 1 and 5 minutes available to download -- other data will have to be computed
):
    # Load the file
    filename='{}/Earth2014.{}2014.{}min.geod.bin'.format(input_folder, dataset, minutes_per_node)
    input_file = open(filename, 'rb')
    input_matrix = np.fromfile(input_file, dtype='>i2') # int16 but big-endian (ieee-be)

    # Some light transforms to go from this input data to the format expected
    input_matrix = input_matrix.reshape((180 * 60 // minutes_per_node, 360 * 60 // minutes_per_node))
    input_matrix = np.flipud(input_matrix)
    input_file.close()

    # Build a map instance and generate an image
    input_map = map_instance.MapInstance({
        'minutes_per_node': minutes_per_node,
        'dataset': dataset.lower(),
        'image_folder': image_folder,
        'region': 'world',
    }, 
        180 * 60 // minutes_per_node, # n_rows
        360 * 60 // minutes_per_node, # n_cols 
        input_matrix.flatten())
    drawBasicValueMap(input_map)

    # Save the data to a compressed file
    output_file = open('data/{}_world_{}min.npz'.format(dataset, minutes_per_node), 'wb')
    np.savez_compressed(output_file, data_matrix=input_matrix)
    output_file.close()


def visualizeNewRegion( 
    # Give the region a name
    # Due to rigidity of the CSV file import it has to be no more than 10 characters long
    region_name, 
    
    # Coordinates bounding the region
    # They should be simple arrays of 2 values each
    # The 2 values don't need to be ordered (since it may be easy to mix up) -- it will automatically be converted to teh right order
    # Values should be measured by degrees as used in global coordinations (-90 to 90 and -180 to 180)
    # Values can be fractional
    lats, 
    longs,
    
    # Specific an image folder to save images
    image_folder = None, # eg. img/##/
):
    # Convert to coordinates
    minutes_per_degree = 60
    region_bounds = { # Convert it from degrees on a globe to it to minutes from the NW corner
        'ymin': int(( 90 - max(lats )) * minutes_per_degree),
        'ymax': int(( 90 - min(lats )) * minutes_per_degree),
        'xmin': int((180 - max(longs)) * minutes_per_degree),
        'xmax': int((180 - min(longs)) * minutes_per_degree),
    }

    # Printable values to add to the region_coordinates.csv
    area = (region_bounds['ymax'] - region_bounds['ymin']) * (region_bounds['xmax'] - region_bounds['xmin'])
    print('region,     ymin,  ymax,  xmin,  xmax,      area')
    print("{:s},{:s}{:6d},{:6d},{:6d},{:6d},{:10d}".format(
        region_name, " "*(9-len(region_name)), 
        region_bounds['ymin'], region_bounds['ymax'],
        region_bounds['xmin'], region_bounds['xmax'],
        area))

    # Generate preview images
    if image_folder is not None:
        map_elevation = map_data.loadBaseMap('PSL', 1, image_folder)
        map_elevation = map_elevation.newChildRegionInstance(region_name, region_bounds)
        drawBasicValueMap(map_elevation)

        map_elevation = map_data.loadBaseMap('TBI', 1, image_folder)
        map_elevation = map_elevation.newChildRegionInstance(region_name, region_bounds)
        drawBasicValueMap(map_elevation)
        
def createPopulationAndSeaLevelMap(
    image_folder, # eg. img/##/
    minutes_per_node = 1,
    dataset_elevation = 'TBI',
    dataset_population = 'POP',
    dataset_output = 'PSL',  # can use off-versions like PSL2 trying a different algorithim
):
    region = 'world' # Generally its recommended to do this for the whole world at once rather than per-region
    
    # Load the 2 input data maps to be combined
    data_file = open('data/{}_world_{}min.npz'.format(dataset_population.lower(), minutes_per_node), 'rb')
    data_population = np.load(data_file)
    if not isinstance(data_population, np.ndarray):
        data_population = data_population['data_matrix']
    data_file.close()
    data_file = open('data/{}_world_{}min.npz'.format(dataset_elevation.lower(), minutes_per_node), 'rb')
    data_elevation = np.load(data_file)
    if not isinstance(data_elevation, np.ndarray):
        data_elevation = data_elevation['data_matrix']
    data_file.close()

    # Combine the data
    data_2d = data_population
    # Add negative gradient based on elevation from coast
    data_2d[data_population <= 0] = -np.abs(data_elevation)[data_population <= 0]
    # Add subtle positive gradient to distinguish areas with uniform population values
    data_2d[data_population > 0] = data_2d[data_population > 0] + 1/(0.01+np.abs(data_elevation)[data_population > 0])

    # Save compressed output files
    if region == 'world':
        data_file = open('data/{}_world_{}min.npz'.format(dataset_output, minutes_per_node), 'wb')
        np.savez_compressed(data_file, data_matrix=data_2d)
        data_file.close()

    # Make diagrams of the data
    [n_rows, n_cols] = data_2d.shape
    elevation_map = map_instance.MapInstance({
        'minutes_per_node': minutes_per_node,
        'dataset': dataset_output.lower(),
        'image_folder': image_folder,
        'region': region,
    }, n_rows, n_cols, data_2d.flatten())
    
    drawBasicValueMap(elevation_map)