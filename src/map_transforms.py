import numpy as np

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
        np.array(map_hillshade, dtype=int) / 100
    )
