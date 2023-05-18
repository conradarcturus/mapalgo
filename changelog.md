## Changelog ##

### Phase 1, Setting up the maps, images, basic transforms ###

Examples in notebook `01_Initial_Loading_Examples.ipynb`

2022-09-26
* Added initial data files & an inital notebook loading the data.

2022-09-29
* Added image displaying functions, copied from older environment.
  
2022-10-05
* Added the MapInstance class to help organize metadata.
* Made `map_data.py` file to collection functions loading in datasets.

2022-10-11
* Added regional data file `data/region_coordinates.csv` and accessor to regional data to `map_data.py`.

2022-10-13
* Added hillshade algorithm & file for similar transforms, `map_transforms`.
* Added naturalish colormap option to images

### Phase 2, Algorithms to determine peaks, mountain ranges ###

Examples in notebook `02_Mountains.ipynb`

2022-10-13
* Started new notebook with functions to get information from the map (node index, map edge, highest neighbor)
* Function to show the local mountain peaks each node points up to

2022-10-14
* Added border functions to make better images of regions
* Added more low-resolution datasets, generated mountain ranges & basins for them.
   * Also ran the mountain/basin algorithm on populations but the data is too sparse right now for it to be really
     meaningful until we smooth it out or merge "mountains" aka cities.
     
Examples in notebook `03_Mountain_Ranges.ipynb`

2022-10-17
* Early attempts in determining mountain ranges -- need more analysis though before things look right, and cutting the commit with early results

2023-05-18
* Exploring different approaches to visualize ridge lines

Planned work
* Improve mountain range algo2 to visualize better what it looks like without merge everything