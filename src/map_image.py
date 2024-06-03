import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as img
from matplotlib.colors import LinearSegmentedColormap

class RasterImage():
    ## baseMapInstance should contain all of the basic image of the map, eg. number of rows and cols
    def __init__ (self, baseMapInstance, map_transforms=None, n_neighbors=None):
        # transforms should be of type MapTransforms
        
        # Names of different aspects -- important for saving the filename
        self.folder = baseMapInstance.getAttribute('image_folder');
        self.dataset = baseMapInstance.getAttribute('dataset');
        self.resolution = str(baseMapInstance.getAttribute('minutes_per_node')) + 'min';
        self.region = baseMapInstance.getAttribute('region');
        
        # Dimension
        self.n_rows = baseMapInstance.getNumRows()
        self.n_cols = baseMapInstance.getNumCols()
        self.n_nodes = self.n_rows * self.n_cols
        self.n_neighbors = n_neighbors if n_neighbors else 0
        
        # Other
        self.map_transforms = map_transforms
         
        # Initialize empty data
        self.nodes_colors = np.ones([self.n_nodes,1], dtype=float) * np.array([0, 0, 0, 1]).reshape([1,4])
        self.layer_names = []
        self.fig = None
        self.background = None
        
    def setData(self, data):
        self.data = data
        return self
    
    def addLayer(self, name, values, nodes_selected=None, 
                 combine='set', transforms=[], colormap=None,
                 color_channel=None, opacity=None, dissolve=None):
        self.addToFilename(name)
        
        # values is expected to be 1 int, 3 length array (3 colors), n_nodes length array or 2D array that's n_nodes x 4
        #   factor: float
        #   color: 3/4 length array
        #    
        value_format = 'unknown'
        n_nodes_provided = 1
        n_color_channels = 3 # or 4
        if (isinstance(values, (int, float))):
            value_format = 'factor'
        else:
            values = np.array(values)
            shape = values.shape
            n_dims = len(shape)
            if(n_dims == 1 and shape[0] <= 4):
                value_format = 'color'
                n_color_channels = shape[0]
            elif(n_dims == 1):
                value_format = 'nodes_factor'
                n_nodes_provided = shape[0]
            else: # n_dims = 2
                value_format = 'nodes_color'
                n_nodes_provided = shape[0]
                n_color_channels = shape[1]
                
        # Nodes Colored / Mask processing
        # Mask should be either n_nodes bool array or array of nodes_index that's colored
        n_nodes_selected = self.n_nodes
        if (nodes_selected is None): # If not specified, change all nodes
            nodes_selected = np.arange(self.n_nodes)
        else:
            if(nodes_selected.dtype is np.dtype('bool')):
                n_nodes_selected = np.count_nonzero(nodes_selected)
            else:
                n_nodes_selected = len(nodes_selected)
            
            # If the values also has the dimension of n_nodes, but we are coloring less, extract the colored ones
            if (n_nodes_provided != 1 and n_nodes_provided != n_nodes_selected):
                assert(n_nodes_provided == self.n_nodes)
                values = values[nodes_selected]

        # Transforms
        if ('border' in transforms):
            assert (value_format == 'nodes_factor')
            values = self.map_transforms.getNodesBorder(values)
        if ('prandom' in transforms):
            values = values * 1619 % 251
        if ('norm' in transforms): # puts them in range 0 to 1
            values = plt.Normalize()(values)
        if (colormap is not None): # Apply Color
            assert (value_format == 'nodes_factor')
            
            if (colormap == 'prism'):
                values = plt.cm.prism(values)
            elif (colormap == 'diverge'): # diverge
                values = plt.cm.RdYlBu(values)
            elif (colormap == 'qual'): # qualitiative
                values = plt.cm.Paired(values)
            elif (colormap == 'naturalish'):
                values = _applyNaturalishColormap(values)
            elif (colormap == 'hashed'):
                values = _applyHashedColormap(values)
            else: # rainbow
                values = plt.cm.rainbow(values)
            value_format = 'nodes_color'
            n_color_channels = 4
            
        # Expand the values to full color (nodes x channels) or keep as single number
        if (value_format == 'color'):
            values = values.reshape([1, n_color_channels]).repeat(n_nodes_selected, axis=0)
        elif (value_format == 'nodes_factor' and color_channel is None):
            values = values.reshape([n_nodes_selected, 1]).repeat(n_color_channels, axis=1)
        else: # factor (returns 1) or nodes_color returns (n_nodes_colored x n_color_channels)
            values = values
        
        # Apply to pixel colors
        if (color_channel is not None): # 0 to 3: red, green, blue, opacity
            self.nodes_colors[nodes_selected, color_channel] = values
        elif (combine == 'set'): # value doesn't matter
            self.nodes_colors[nodes_selected, :n_color_channels] = values
        elif (combine == 'add'): # factor [0-1] used in formula original * (1 - value) + new * value
            #self.nodes_colors = self.nodes_colors * (1 - factor) + data * factor
            opacity = opacity if opacity is not None else 0.5 # make custom
            dissolve = dissolve if dissolve is not None else 1 - opacity
            self.nodes_colors[nodes_selected, :n_color_channels] *= dissolve
            self.nodes_colors[nodes_selected, :n_color_channels] += values * opacity
        elif (combine == 'multiply'):
            self.nodes_colors[nodes_selected, :n_color_channels] *= values
        else:
            raise Exception('Invalid way to combine, must set color_channel [0-3] or set combine [set, add, multiply]')
            
        # Ensures no node is too big or too small
        self.nodes_colors = np.fmax(np.fmin(self.nodes_colors, 1), 0)
        return self
    
    def addToFilename(self, name=''):
        if(name is not None and name != ''):
            self.layer_names.append(name)
        return self
    
    # Some complex images may have too many layers than its useful to add to the filename
    # This function can be used to override them to simplify it
    def overrideLayerNames(self, layer_names):
        self.layer_names = layer_names
        return self
    
    def getFilename(self):
        n_nei = 'nei' + str(self.n_neighbors) if self.n_neighbors > 0 else ''
        layers = '-'.join(self.layer_names)
        file_attributes = [self.dataset, self.resolution, self.region, n_nei, layers]
        file_attributes = filter(lambda x: x is not None and x != '', file_attributes)
        
        filename = '_'.join(file_attributes) + '.png'
        self.filename = self.folder + filename
        return filename
    
    def save(self, save_fig = False):
        filename = self.getFilename()
        img.imsave(self.filename, self.nodes_colors.reshape([self.n_rows, self.n_cols, 4]))
        if(save_fig and self.fig is not None):
            self.fig.savefig(self.folder + 'fig_' + filename, bbox_inches='tight')
        return self
        
    def display(self):
        self.fig = plt.figure(figsize=(12,8))
        plt.imshow(self.nodes_colors.reshape([self.n_rows, self.n_cols, 4]))
        plt.show()
        
        ## TODO change axes to show global degrees rather than pixel values
        return self
    
    def final(self):
        # So output of self doesn't appear if you don't want it
        return
    
# Get natural coloring
land_colors = ['beige', 'yellowgreen', 'forestgreen', 'darkolivegreen', 'slategrey', 'snow']
sea_colors = ['deepskyblue', 'mediumblue', 'darkblue']
colormap_land = LinearSegmentedColormap.from_list("colormap_land", land_colors)
colormap_sea = LinearSegmentedColormap.from_list("colormap_sea", sea_colors)

def _applyNaturalishColormap(data_flat, normalize=True):
    # First lets divide the data into land and sea
    land = data_flat.astype(float) # makes sure it is float typed, & makes a new copy of the matrix
    sea = -data_flat.astype(float) # makes sure it is float typed, & makes a new copy of the matrix
    land[land < 0] = 0
    sea[sea < 0] = 0
    
    # Divide by the maximum if we want to normalize it
    if(normalize):
        land /= np.max(land)
        sea /= np.max(sea)
    
    # Apply the colors. This should give us an n*4 matrix
    land = colormap_land(land)
    sea = colormap_sea(sea)
        
    # Combine
    land[data_flat < 0, :] = sea[data_flat < 0, :]
    return land


def _applyHashedColormap(nodes_value):
    nodes_color = np.zeros([len(nodes_value), 4])
    nodes_value = np.expand_dims(nodes_value, 0)
    nodes_color[:, 0] = (nodes_value * 1000 * 221 % 255) / 255.0
    nodes_color[:, 1] = (nodes_value * 1000 * 251 % 255) / 255.0
    nodes_color[:, 2] = (nodes_value * 1000 * 373 % 255) / 255.0
    nodes_color[:, 3] = 1.0
    return nodes_color