## World Maps ##
This data comes from third parties and has been transformed to work in the code provided.

**Kinds of Data**
* POP - Population
* TBI - Elevation of Bedrock

Only the coarse 5/10/60 minute resolution files are updated to github since the other files are 
quite large and the data may have limited use agreements.

## Locations ##

### region_coordinates.csv ###

This comma separated values file contains coordinates for different regions.

The number of values in the world map may be too computationally expensive to test out algorithms across the whole map.
Additionally some features may be easier to see at a zoomed in map.
Thereby it's recommend to use regions.

You can load region map data using `src/map_data.py:loadRegionMap()`

**Columns**
* continent
   * The generally group for each region
   * Values: Americas, Europe, MEA, Asia, Oceania, World
* name
   * The name of the region -- often using shorthand so its easier to specify the key when loading it
* ymin & ymax
   * The vertical bounds, measured in number of minutes from the north pole.
   * 0 = North Pole, 90 degrees north
   * 5400 = Equator, 0 degrees
   * 10800 = South Pole, 90 degrees south
* xmin & xmax
   * The horizontal bounds, measured in number of minutes from the opposite of the Greenwich meridian.
   * 0 = Opposite Meridian, 180 degrees west
   * 10800 = Greenwich Meridian, 0 degrees
   * 21600 = Opposite Meridian, 180 degrees east
* area 
   * The total number of square minutes covered by this region
