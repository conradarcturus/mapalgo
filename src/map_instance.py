##
# MapInstance helps organize the information that's shown in a map.
#
# Previously, it was hard to keep track of data, was it 1d or 2d? What were the dimensions? etc...
# This organizes that information and makes it easy to spin off new instances of data.
#
class MapInstance():
    def __init__(self, attributes={}, n_rows=None, n_cols=None, data=None):
        # Enforce required attributes
        for key in ['dataset', 'region', 'minutes_per_node', 'image_folder']:
            attributes[key] is not None
        # Other good ideas for attributes to describe the map:
        #  * values (what kind, eg. elevation)
        #  * mods (modifications, eg. sqrt, norm)
        
        # Dimension
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.n_nodes = self.n_rows * self.n_cols
        
        # Set the attributes and data if provided
        self.attributes = {}
        self.addToAttributes(attributes)
        self.setData(data)
        
    def setData(self, data):
        if(len(data.shape) > 1):
            # Make all data 1D in storage to keep it standard
            data = data.flatten()
        self.data = data
        return self
    
    def addToAttributes(self, new_attributes):
        self.attributes = _mergeAttributes(self.attributes, new_attributes)
        return self
    
    def getAttribute(self, key):
        return self.attributes[key]
    
    def getNRows(self):
        return self.n_rows
    
    def getNCols(self):
        return self.n_cols
    
    # Gets the 1D version of the data
    def getDataFlat(self):
        return self.data
    
    # Gets the 2D version of the data
    def getDataMatrix(self):
        return self.data.reshape([self.n_rows, self.n_cols])
    
    def getDims(self):
        return [self.n_rows, self.n_cols]
    
    # Copies the old instance into a new form, such as if you add a new specifier to the data
    def newChildInstance(self, new_attributes, new_data):
        attributes = _mergeAttributes(self.attributes, new_attributes)
        return MapInstance(attributes, self.n_rows, self.n_cols, new_data)
    
    # Copies the old data, zoomed in on a smaller section
    # @param bounds should be in the same resolution as the data
    def newChildRegionInstance(self, region_name, bounds):
        new_data = self.getDataMatrix()[bounds['ymin']:bounds['ymax'],bounds['xmin']:bounds['xmax']]
        attributes = _mergeAttributes(self.attributes, {'region': region_name})
        return MapInstance(attributes, bounds['ymax']-bounds['ymin'], bounds['xmax']-bounds['xmin'], new_data)
        
def _mergeAttributes(old_attributes, new_attributes):
    attributes = old_attributes.copy()
    for key in new_attributes:
        attributes[key] = new_attributes[key]
    return attributes