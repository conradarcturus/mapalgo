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
* Changed the existing map_partition functions into an object-based class because of all of the repeat code (and the terribly named variable `params`)
* Added some exploratory code to the nodebook to attempt to partition based on large valleys, included some analysis but it needs more work

2023-06-06
* Tried out some code to visualize the ruggedness of terrain -- may be useful for determining true mountain ranges versus plateaus

#### Looking at other Data
Examples in notebook `05_Data_Cleanup.ipynb`

2024-05-17
* Getting back into the groove of this work (A year later?!)
* Added support for Population maps -- but will need to iterate on the underlying data since the zeros don't cooperate well

2024-05-24
* Added new PSL (Population + Sea Level) data

2024-05-27
* Compress the new data, start iterating on importing new data
* Travelling to new areas -- adding locale region maps so I could play around with them. Gosh I need the higher resolution elevation data
* With that, added better utilities to generate regions based on degrees

2024-06-03
* Moved input data processing into a different source file, `map_input_processing.py`
* Revived the script to read in the binary elevation data from the Curtin University source
* Re-generated the PSL data with the new PSL algorithm (previously it added up sea level + population, so it looked like places near sea level had population, inventing land bridges that don't exist in modern times.

### Planned work
* Iterate on different group algorithms
   * Splitting at different thresholds
   * Having "plains" or plateaus treated differently
   * Try to capture "interrupted" mountain chains that we see a visual pattern to even though in the fine detail they are separated (eg. a the Columbia river cutting the Cascades in two)
* Try different ways to visualize 
   * Rivers with color & width corresponding to flow down it
* Try the algorithms on population data and see urban catchment areas
  * Clean up population data to make it work better
* Improve algorithm efficiency so we can scale better to larger datasets / make finer images
* Clean up data
  * Lakes often have the same elevation and don't work well in the algorithms