import numpy as np
import math

##
# This computes the hillshade of an elevation map. The hillshade algorithm
# approximates the shadow caused by a uniform light source coming from the northwest
#
# Scaling by 100 seems to produce good, consistent shading
#
# Add to image with .addLayer('hillshade', hillshade_render, transforms=[], combine='add', opacity=1, dissolve=1) \
#
def getHillshade(map_instance, radius=1):
    map_values = np.array(map_instance.getDataMatrix(), dtype=float)
    map_values = np.power(np.abs(map_values * 1.0), 0.5) * np.sign(map_values)
    map_values /= np.max(map_values) / 100
    map_hillshade = np.zeros(map_values.shape, dtype=float)

    for x in range(-radius, radius+1):
        for y in range(-radius, radius+1):
            if(x + y == 0):
                continue
            map_hillshade += (map_values - np.roll(np.roll(map_values, x, 0), y, 1)) / (x+y)
            
    return map_instance.newChildInstance(
        {'values': 'hillshade'}, 
        np.array(map_hillshade, dtype=int) / 100,
    )
##
# Method to get the index of each node
# Simple function but it will be used often
#
def getNodesIndex(map_instance):
    return np.arange(map_instance.getNumNodes())

# Method to determine which nodes are at the edge of the map
# It is useful for ignoring "neighboring" nodes that shouldn't be counted in algorithms
def getNodesOnMapEdge(map_instance):
    nodes_index = getNodesIndex(map_instance)
    num_cols = map_instance.getNumCols()
    num_rows = map_instance.getNumRows()
    
    nodes_edge = nodes_index % num_cols == 0
    nodes_edge |= (nodes_index % num_cols) == num_cols - 1
    nodes_edge |= nodes_index < num_cols
    nodes_edge |= nodes_index >= ((num_rows - 1) * num_cols)
    return nodes_edge
    
##
# This function determines which neighboring node is the highest
# Nodes with a value -1 have no higher neighbor.
#
# Default radius is 1.5, allowing for orthogonally and diagonally adjacent nodes
#
def getHighestNeighbor(map_instance, radius=1.5, wrap=False):
    nodes_highest_neighbor_value_so_far = map_instance.getDataFlat()
    nodes_highest_neighbor_index = np.full(map_instance.getNumNodes(), -1)
    gridded_node_index = getNodesIndex(map_instance).reshape(map_instance.getDims())
    gridded_value = map_instance.getDataMatrix()
    nodes_on_map_edge = None
    if (not wrap):
        nodes_on_map_edge = getNodesOnMapEdge(map_instance)

    rounded_radius = math.floor(radius)
    for x in range(-rounded_radius, rounded_radius+1):
        for y in range(-rounded_radius, rounded_radius+1):
            # Only compute for neighboring edges under the radius
            if((x == 0 and y == 0) or (x**2+y**2)**0.5 > radius):
                continue
                
            # For neighboring nodes, find out if they are higher than the node
            nodes_neighbor_value = np.roll(np.roll(gridded_value, x, 0), y, 1).flatten()
            nodes_neighbor_is_higher = nodes_neighbor_value > nodes_highest_neighbor_value_so_far 

            # Remove higher node designations for neighbors that are on the edge
            if (not wrap):
                nodes_neighbor_on_map_edge = np.roll(np.roll(nodes_on_map_edge.reshape(map_instance.getDims()), x, 0), y, 1).flatten()
                nodes_neighbor_is_higher[nodes_neighbor_on_map_edge] = False

            # Record the index of the higher neighboring node
            nodes_neighbor_index = np.roll(np.roll(gridded_node_index, x, 0), y, 1).flatten()
            nodes_highest_neighbor_index[nodes_neighbor_is_higher] = nodes_neighbor_index[nodes_neighbor_is_higher]
            nodes_highest_neighbor_value_so_far[nodes_neighbor_is_higher] = nodes_neighbor_value[nodes_neighbor_is_higher]
            
    return map_instance.newChildInstance(
        {'values': 'highest_neighbor'},
        nodes_highest_neighbor_index,
    )

##
# Figures out the maximum point that a node points to along the curvature of the map
#
# You can think about among a mountain range, determining which peak each point
# rolls up to or which mountain each point is on.
#
# Nodes are labeled by the index of their corresponding peak node
#
def getLocalPeaks(map_highest_neighbor_index, verbose=False):
    nodes_local_peak = map_highest_neighbor_index.getDataFlat()
    
    # Nodes without a higher neighbor are set to -1, but for this algorithm we want
    # to set them to the peak index
    nodes_index = getNodesIndex(map_highest_neighbor_index)
    nodes_local_peak[nodes_local_peak == -1] = nodes_index[nodes_local_peak == -1]

    if(verbose):
        print(np.count_nonzero(nodes_local_peak == nodes_index), 'already peaks')

    # A basic iterative approach but straightforward and simple and
    # expected to run no more than O(nlogn) time because each iteration takes n time
    # and the longest path is from the longest dimension of the map -- but since
    # each iteration builds on the prior data, it should double the length of the 
    # covered path each time
    for i in range(map_highest_neighbor_index.getNumRows()):
        nodes_local_peak_cand = nodes_local_peak[nodes_local_peak]
        n_diff = np.count_nonzero(nodes_local_peak != nodes_local_peak_cand)
        if(n_diff == 0):
            continue
        if(verbose):
            print(n_diff, 'updated')
        nodes_local_peak = nodes_local_peak_cand
        
    return map_highest_neighbor_index.newChildInstance(
        {'values': 'local_peak'}, 
        nodes_local_peak
    )

##
# Determine which nodes have different values from their neighbors
#
# Usually, adjacent (radius=1) is sufficient
#
def getBorder(map_instance, radius=1, wrap=False):
    nodes_value = map_instance.getDataFlat()
    gridded_value = map_instance.getDataMatrix()
    nodes_border = np.full(map_instance.getNumNodes(), False)
    nodes_on_map_edge = None
    if (not wrap):
        nodes_on_map_edge = getNodesOnMapEdge(map_instance) 
    
    rounded_radius = math.floor(radius)
    for x in range(-rounded_radius, rounded_radius+1):
        for y in range(-rounded_radius, rounded_radius+1):
            # Only compute for neighboring edges under the radius
            if((x == 0 and y == 0) or (x**2+y**2)**0.5 > radius):
                continue
            
            nodes_neighbor_value = np.roll(np.roll(gridded_value, x, 0), y, 1).flatten()
            nodes_neighbor_is_different = nodes_neighbor_value != nodes_value 

            # Remove higher node designations for neighbors that are on the edge
            if (not wrap):
                nodes_neighbor_on_map_edge = np.roll(np.roll(nodes_on_map_edge.reshape(map_instance.getDims()), x, 0), y, 1).flatten()
                nodes_neighbor_is_different[nodes_neighbor_on_map_edge] = False
            
            nodes_border[nodes_neighbor_is_different] = True
            
    return map_instance.newChildInstance(
        {'mods': 'border'},
        nodes_border,
    )

def getNodesNeighbors(n_rows, n_cols, n_nei, wrap=False):
    rc2index = lambda r, c: int(r * n_cols + c)
    index2rc = lambda index: [int(index / n_cols), int(index % n_cols)]
    nodes_neighbors = np.zeros([n_rows*n_cols, n_nei], dtype=int)
    for row in np.arange(n_rows):
        for col in np.arange(n_cols):
            index = rc2index(row, col)
            nodes_neighbors[index, 0] = rc2index(row - 1, col) if row > 0 else -1
            nodes_neighbors[index, 1] = rc2index(row + 1, col) if row < n_rows-1 else -1
            nodes_neighbors[index, 2] = rc2index(row, col - 1) if col > 0 else -1
            nodes_neighbors[index, 3] = rc2index(row, col + 1) if col < n_cols-1 else -1
            if(n_nei >= 8):
                nodes_neighbors[index, 4] = rc2index(row - 1, col - 1) if row > 0   and col > 0   else -1
                nodes_neighbors[index, 5] = rc2index(row + 1, col - 1) if row < n_rows-1 and col > 0   else -1
                nodes_neighbors[index, 6] = rc2index(row - 1, col + 1) if row > 0   and col < n_cols-1 else -1
                nodes_neighbors[index, 7] = rc2index(row + 1, col + 1) if row < n_rows-1 and col < n_cols-1 else -1
            if(n_nei >= 20):
                nodes_neighbors[index,  8] = rc2index(row - 2, col + 1) if row >= 0+2 and col <  n_cols-1 else -1
                nodes_neighbors[index,  9] = rc2index(row - 2, col + 0) if row >= 0+2 and col >= 0+0 else -1
                nodes_neighbors[index, 10] = rc2index(row - 2, col - 1) if row >= 0+2 and col >= 0+1 else -1
                nodes_neighbors[index, 11] = rc2index(row - 1, col + 2) if row >= 0+1 and col <  n_cols-2 else -1
                nodes_neighbors[index, 12] = rc2index(row - 1, col - 2) if row >= 0+1 and col >= 0+2 else -1
                nodes_neighbors[index, 13] = rc2index(row + 0, col + 2) if row >= 0+0 and col <  n_cols-2 else -1
                nodes_neighbors[index, 14] = rc2index(row + 0, col - 2) if row >= 0+0 and col >= 0+2 else -1
                nodes_neighbors[index, 15] = rc2index(row + 1, col + 2) if row <  n_rows-1 and col <  n_cols-2 else -1
                nodes_neighbors[index, 16] = rc2index(row + 1, col - 2) if row <  n_rows-1 and col >= 0+2 else -1
                nodes_neighbors[index, 17] = rc2index(row + 2, col + 1) if row <  n_rows-2 and col <  n_cols-1 else -1
                nodes_neighbors[index, 18] = rc2index(row + 2, col + 0) if row <  n_rows-2 and col >= 0+0 else -1
                nodes_neighbors[index, 19] = rc2index(row + 2, col - 1) if row <  n_rows-2 and col >= 0+1 else -1

            # Go over the edge of the world if appropriate
            if(wrap):
                if(col == 0):
                    nodes_neighbors[index, 2] = rc2index(row, n_cols-1)
                if(col == n_cols-1):
                    nodes_neighbors[index, 3] = rc2index(row,   0)
                if(n_nei >= 8):
                    if(col == 0):
                        nodes_neighbors[index, 4] = rc2index(row - 1, n_cols-1) if row > 0   else -1
                        nodes_neighbors[index, 5] = rc2index(row + 1, n_cols-1) if row < n_rows-1 else -1
                    if(col == n_cols-1):
                        nodes_neighbors[index, 6] = rc2index(row - 1,   0) if row > 0   else -1
                        nodes_neighbors[index, 7] = rc2index(row + 1,   0) if row < n_rows-1 else -1
                if(n_nei >= 20):
                    if(col == 0):
                        nodes_neighbors[index, 10] = rc2index(row - 2, col + n_cols-1) if row >= 0+2 else -1
                        nodes_neighbors[index, 19] = rc2index(row + 2, col + n_cols-1) if row <  n_rows-2 else -1
                    if(col <= 1):
                        nodes_neighbors[index, 12] = rc2index(row - 1, col + n_cols-2) if row >= 0+1 else -1
                        nodes_neighbors[index, 14] = rc2index(row + 0, col + n_cols-2) if row >= 0+0 else -1
                        nodes_neighbors[index, 16] = rc2index(row + 1, col + n_cols-2) if row <  n_rows-1 else -1
                    if(col >= n_cols-2):
                        nodes_neighbors[index, 11] = rc2index(row - 1, col - n_cols+2) if row >= 0+1 else -1
                        nodes_neighbors[index, 13] = rc2index(row + 0, col - n_cols+2) if row >= 0+0 else -1
                        nodes_neighbors[index, 15] = rc2index(row + 1, col - n_cols+2) if row <  n_rows-1 else -1
                    if(col == n_cols-1):
                        nodes_neighbors[index,  8] = rc2index(row - 2, col - n_cols+1) if row >= 0+2 else -1
                        nodes_neighbors[index, 17] = rc2index(row + 2, col - n_cols+1) if row <  n_rows-2 else -1
    return nodes_neighbors
