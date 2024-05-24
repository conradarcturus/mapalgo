# mapalgo
This library contains many python methods to process maps for interesting analyses -- usually about cities and mountain ranges.

## Images ##

### Elevation

| Dataset | Elevation | Mountains | Islands | Drainage Basins |
| -- | -- | -- | -- | -- |
| Hawaii (1 minute resolution) | ![hawaii elevation](img/02/tbi_1min_hawaii_elevation.png) | ![hawaii mountains](img/02/tbi_1min_hawaii_mountains.png) | ![hawaii islands](img/03/tbi_1min_hawaii_mountain_ranges-separating_LSL_merges-compare_across_full_path.png) | ![hawaii drainage basins](img/03/tbi_1min_hawaii_watersheds-separating_LSS_merges-compare_across_full_path.png) |
| Pacific Northwest (1 minute resolution) | ![cascadia elevation](img/02/tbi_1min_cascadia_elevation.png) | ![cascadia mountains](img/02/tbi_1min_cascadia_mountains.png) | ![cascadia islands](img/03/tbi_1min_cascadia_islands.png) | ![cascadia drainage basins](img/03/tbi_1min_cascadia_drainage_basins.png) |
| Australia (5 minute resolution) | ![australia elevation](img/05/tbi_5min_australia_elevation.png) | ![australia mountains](img/05/tbi_5min_australia_mountains.png) | ![australia islands](img/05/tbi_5min_australia_islands.png) | ![australia drainage basins](img/05/tbi_5min_australia_drainage_basins.png) |
| World (10 minute resolution) | ![world elevation](img/02/tbi_10min_world_elevation.png) | ![world mountains](img/02/tbi_10min_world_mountains.png) | ![world islands](img/03/tbi_10min_world_islands.png) | ![world drainage basins](img/03/tbi_10min_world_drainage_basins.png) |

### Population

Note: For areas with no people, it counts the elevation relative to sea level. This favors grouping remote areas that are more easily accessible to areas with people.

At this moment, the 1 minute resolution data is using a slightly different algorithm -- to be updated.

| Dataset | Population | Cities | Urban Areas | Voids (Poorly Defined) |
| -- | -- | -- | -- | -- |
| Hawaii (1 minute resolution) | ![hawaii population](img/05/psl_1min_hawaii_population.png) | ![hawaii cities](img/05/psl_1min_hawaii_citys.png) | ![hawaii islands](img/05/psl_1min_hawaii_contiguous_urban_areas.png) | ![hawaii drainage basins](img/05/psl_1min_hawaii_voids.png) |
| Pacific Northwest (1 minute resolution) | ![cascadia population](img/05/psl_1min_cascadia_population.png) | ![cascadia cities](img/05/psl_1min_cascadia_citys.png) | ![cascadia islands](img/05/psl_1min_cascadia_contiguous_urban_areas.png) | ![cascadia voids](img/05/psl_1min_cascadia_voids.png) |
| Australia (5 minute resolution) | ![australia population](img/05/psl_5min_australia_population.png) | ![australia cities](img/05/psl_5min_australia_citys.png) | ![australia contiguous_urban_areas](img/05/psl_5min_australia_contiguous_urban_areas.png) | ![australia voids](img/05/psl_5min_australia_voids.png) |
| World (10 minute resolution) | ![world population](img/05/psl_10min_world_population.png) | ![world cities](img/05/psl_10min_world_citys.png) | ![world contiguous_urban_areas](img/05/psl_60min_world_contiguous_urban_areas.png) The 10 minute version takes too long to generate | ![world voids](img/05/psl_60min_world_voids.png) The 10 minute version takes too long to generate |
