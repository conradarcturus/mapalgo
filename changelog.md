## Changelog ##

### Setting up the maps, images, basic transforms ###

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

### Algorithms to determine peaks, mountain ranges ###

#### Mountains
Examples in notebook `02_Mountains.ipynb`

2022-10-13
* Started new notebook with functions to get information from the map (node index, map edge, highest neighbor)
* Function to show the local mountain peaks each node points up to

2022-10-14
* Added border functions to make better images of regions
* Added more low-resolution datasets, generated mountain ranges & basins for them.
   * Also ran the mountain/basin algorithm on populations but the data is too sparse right now for it to be really
     meaningful until we smooth it out or merge "mountains" aka cities.
     
#### Mountain Ranges & Watersheds
Examples in notebook `03_Mountain_Ranges.ipynb`

2022-10-17
* Early attempts in determining mountain ranges -- need more analysis though before things look right, and cutting the commit with early results

2023-05-18
* Explored different approaches to visualize ridge lines

2023-05-19
* Drew some mountain groupings by looking at stopping merges along ridges that connect peaks where 1 is overwater and 1 is underwater.

2023-05-21
* Refactored the mountain range experimental code
  * Collected the re-used maps (elevation, mountains, ...) into an object collection
  * Added 'params' object to make it easier to recall the number of nodes and organize the params a bit cleaner.
  * Organized most blocks of code to use function definitions -- this makes it easier to manage locale v global variables to prevent using too much memory
  * Added a few more descriptive statistics. In hindsight I should do this more so I make better algorithmic choices earlier
* Generated more iterations on the mountain groupings on Hawaii and found the perfect combination of merging seamounts & mountains for at least this region

2023-05-26
* Adapted the mountain range code for water sheds
* And while I was at it, generated the images for lots of other regions

2023-06-04
* Fixed problem with some local files not being changed from the last update (the .mds).
* Re-generated all of the images, removing the locale borders (since tbh it was too much noise on the large images).
* Updated local python libraries, fixed a few incompatible code issues.

#### Splitting Locales
Examples in notebook `04_Splitting_Locales.ipynb`

2023-06-04
* Consolidated the mountain range division work-in-progress codes into the python class `src\map_partition` and started a new notebook to explore new algorithms


Planned work
* Iterate on different group algorithms
   * Splitting at different thresholds
   * Having "plains" or plateaus treated differently
   * Try to capture "interrupted" mountain chains that we see a visual pattern to even though in the fine detail they are separated (eg. a the Columbia river cutting the Cascades in two)
* Try different ways to visualize 
   * Rivers with color & width corresponding to flow down it
* Try the algorithms on population data and see urban catchment areas
* Improve algorithm efficiency so we can scale better to larger datasets / make finer images
* Clean up data
  * Lakes often have the same elevation and don't work well in the algorithms
  * Potentially 