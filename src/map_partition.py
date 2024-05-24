import numpy as np
from src import map_image, map_instance, map_data, map_transforms

class LocalePartition():
    def __init__ (self, dataset, region, minutes_per_node, image_folder, flow_direction, n_neighbors=4):
        self.dataset = dataset
        self.region = region
        self.minutes_per_node = minutes_per_node
        self.image_folder = image_folder
        self.flow_direction = flow_direction
        self.n_neighbors = n_neighbors
        
        # Early computation
        self.labels = self.getDirectionSpecificLabels()
        
        # Initialized with other functions
        self.maps = None # computeBaseMaps
        self.nodes_neighbors = None # computeNodeNeighbors
        self.merges = None # computeDivisionMergePoints
        
    def computeStandardDivisionInformation(self, print_stats=False, draw_all_images=False):
        self.computeBaseMaps(display_and_save_image=draw_all_images)
        self.computeNodeNeighbors()
        self.computeDivisionMergePoints(print_stats=print_stats, draw_and_save_image=draw_all_images)
        self.computePaths(draw=draw_all_images)
        if draw_all_images:
            self.drawGlobalPathParentGradient()
        self.computePathInterfaceType(display_image=draw_all_images)
        _locales_adjacency_list = self.getLocaleAdjacencyList(verbose=print_stats)
        
        return self
    
    # These provide a series of names so we can run the same code to compute both mountain ranges and water sheds
    def getDirectionSpecificLabels(self):
        if self.dataset in ['TBI', 'RET', 'BED']:
            if self.flow_direction == 'up':
                return {
                    'value': 'elevation',
                    'direction_adjective': 'high',
                    'extremum': 'peak',
                    'path': 'ridge',
                    'locale': 'mountain',
                    'division': 'mountain_range',
                    'sealevel_division': 'island',
                }
            else: # self.flow_direction == 'down'
                return {
                    'value': 'depth',
                    'direction_adjective': 'low',
                    'extremum': 'sink',
                    'path': 'river',
                    'locale': 'basin',
                    'division': 'watershed',
                    'sealevel_division': 'drainage_basin',
                }
        else: # Population-based POP or PSL
            if self.flow_direction == 'up':
                return {
                    'value': 'population',
                    'direction_adjective': 'populated',
                    'extremum': 'downtown',
                    'path': 'urban_corridor',
                    'locale': 'city',
                    'division': 'urban_area',
                    'sealevel_division': 'contiguous_urban_area',
                }
            else: # self.flow_direction == 'down'
                return {
                    'value': 'remoteness',
                    'direction_adjective': 'deserted',
                    'extremum': 'isolated_point',
                    'path': 'outskirt',
                    'locale': 'desert',
                    'division': 'division',
                    'sealevel_division': 'void',
                }

    # Regenerate Elevation information and prepare many supporting maps
    def getImageBase(self, nodes_bg_value=None, nodes_bg_colormap='hashed', nodes_border=None):
        image = map_image.RasterImage(self.maps['elevation']) \
            .addLayer('base', 1)

        if nodes_bg_value is not None:
            transforms = ['norm']
            nodes_bg_value = nodes_bg_value.copy()
            if nodes_bg_colormap == 'hashed':
                # The values after 'norm' change based on the present maximum value 
                # This makes the hashed values for the same original value (eg. 12356) will be different
                # So we don't norm it will be more consistent
                transforms = []
                # Dividing by the number of nodes helps give us a better spread of colors after hashed
                nodes_bg_value = nodes_bg_value / len(nodes_bg_value)
            image = image.addLayer('node_background', nodes_bg_value,
                                   colormap=nodes_bg_colormap, transforms=transforms, combine='multiply', opacity=0.5)

        if nodes_border is not None:
            image = image.addLayer('border', 0.5, nodes_selected=nodes_border, combine='multiply')

        return image.addLayer('sea', 1.2, nodes_selected=self.maps['sea'].getDataFlat(), combine='add', dissolve=.2) \
                .addLayer('hillshade', self.maps['hillshade'].getDataFlat(), combine='add', opacity=1, dissolve=1) \
                .addLayer('coast', 0.2, nodes_selected=self.maps['coast'].getDataFlat(), combine='multiply')

    # Get the basic maps
    def computeBaseMaps(self, display_and_save_image=True):
        maps = {} # This will collect all map instances
        maps['elevation'] = map_data.loadRegionMap(
            region=self.region, 
            dataset=self.dataset, 
            minutes_per_node=self.minutes_per_node, 
            image_folder=self.image_folder,
        )
        maps['hillshade'] = map_transforms.getHillshade(maps['elevation'], 1)
        maps['sea'] = maps['elevation'].newChildInstance(
            {'values': 'sea'},
            maps['elevation'].getDataFlat() < 0,
        )
        maps['coast'] = map_transforms.getBorder(maps['sea'], 1)
        if self.flow_direction == 'down':
            maps['elevation'] = maps['elevation'].newChildInstance(
                {'values': 'gravity'},
                -maps['elevation'].getDataFlat(),
            )
        self.n_nodes = maps['elevation'].getNumNodes()

        # Locales
        maps['highest_neighbor_index'] = map_transforms.getHighestNeighbor(maps['elevation'])
        maps['locale'] = map_transforms.getLocalPeaks(maps['highest_neighbor_index'])
        maps['locale_border'] = map_transforms.getBorder(maps['locale'], 1)
        self.maps = maps
        
        # Display locales
        if display_and_save_image:
            # Elevation
            data_elevation_sqrt = maps['elevation'].getDataFlat()
            data_elevation_sqrt = np.sign(data_elevation_sqrt) * (np.abs(data_elevation_sqrt) ** 0.5)
            map_image.RasterImage(maps['elevation']) \
                .addLayer('elevation', data_elevation_sqrt, colormap='naturalish') \
                .addLayer('sea', 1.2, nodes_selected=maps['sea'].getDataFlat(), combine='add', dissolve=.2) \
                .addLayer('hillshade', maps['hillshade'].getDataFlat(), combine='add', opacity=1, dissolve=1) \
                .addLayer('coast', 0.2, nodes_selected=maps['coast'].getDataFlat(), combine='multiply') \
                .overrideLayerNames([self.labels['value']]) \
                .display().save().final()
            
            # Locales
            self.getImageBase(
                         nodes_bg_value=maps['locale'].getDataFlat(), 
                         nodes_border = maps['locale_border'].getDataFlat()) \
                .overrideLayerNames([self.labels['locale'] + 's']) \
                .display().save().final()
            
        return self
    
    # While some algorithms work well on linear arithmetic -- some are too hard to handle en masse
    # Rather, we can compute the adjacency list and utilize that in algorithms
    def computeNodeNeighbors(self):
        self.nodes_neighbors = map_transforms.getNodesNeighbors(
            self.maps['elevation'].getNumRows(),
            self.maps['elevation'].getNumCols(),
            self.n_neighbors,
            wrap=False
        )
        return self

    def computeDivisionMergePoints(self, print_stats=False, draw_and_save_image=True):
        nodes_locale = self.maps['locale'].getDataFlat()
        nodes_division = nodes_locale.copy()

        # output data
        merges = []
        nodes_division_snapshot = np.zeros(self.n_nodes, dtype=int)
        nodes_peak_division_parent = np.zeros(self.n_nodes, dtype=int) - 1 # not necessarily used

        def mergeTwoRanges(lo_index, hi_index):
            locale_lo = nodes_locale[lo_index]
            locale_hi = nodes_locale[hi_index]
            division_lo = nodes_division[lo_index]
            division_hi = nodes_division[hi_index]
            nodes_division[nodes_division == division_lo] = division_hi
            nodes_peak_division_parent[division_lo] = division_hi

            return {
                'bridge_lo_index': lo_index,
                'bridge_lo_value': nodes_value[lo_index],
                'bridge_hi_index': hi_index,
                'bridge_hi_value': nodes_value[hi_index],
                'locale_lo': locale_lo,
                'locale_hi': locale_hi,
                'division_lo': division_lo,
                'division_hi': division_hi,
                'landsea_local_interface': # Values are the high-side mountain, the bridge, then the low-side mountain
                    ('L' if nodes_value[locale_hi] > 0 else 'S') + 
                    ('L' if nodes_value[hi_index] > 0 else 'S') + 
                    ('L' if nodes_value[locale_lo] > 0 else 'S'),
                'landsea_division_interface': # Values are the high mountain range, the bridge, then the low mountain range
                    ('L' if nodes_value[division_hi] > 0 else 'S') + 
                    ('L' if nodes_value[hi_index] > 0 else 'S') + 
                    ('L' if nodes_value[division_lo] > 0 else 'S'),
                'distance_between_bridge_and_hi_local_extremum':
                    max(nodes_value[locale_hi], nodes_value[locale_lo]) - nodes_value[hi_index],
                'distance_between_bridge_and_hi_division_extremum': nodes_value[division_hi] - nodes_value[hi_index],
            }

        nodes_value = self.maps['elevation'].getDataFlat()
        nodes_index_hi_to_lo = np.argsort(-nodes_value);
        for i_explorer in np.arange(self.n_nodes):
            explorer_index = nodes_index_hi_to_lo[i_explorer]
            node_value = nodes_value[explorer_index]
            explorer_division = nodes_division[explorer_index]

            if i_explorer == (self.n_nodes // 8):
                nodes_division_snapshot = nodes_division.copy()

            for neighbor_index in self.nodes_neighbors[explorer_index,:]:
                # Exclude not wrapping neighbors and neighbors that are already in the same mountain range
                if (neighbor_index == -1 or nodes_division[neighbor_index] == explorer_division):
                    continue

                # They are different!
                neighbor_division = nodes_division[neighbor_index]

                if (nodes_value[explorer_division] > nodes_value[neighbor_division]):
                    # The node's mountain range is taller, merge into that
                    mergePoint = mergeTwoRanges(neighbor_index, explorer_index)
                else:
                    # The neighbor's mountain peak is taller, merge into that
                    mergePoint = mergeTwoRanges(explorer_index, neighbor_index)

                    # Update the explorers mountain range
                    explorer_division = neighbor_division
                merges.append(mergePoint)


        # Draw the map
        if draw_and_save_image:
            map_division = self.maps['locale'].newChildInstance({'values': 'parent_extremum'}, nodes_division_snapshot)
            map_division_border = map_transforms.getBorder(map_division, 1)

            self.getImageBase(
                   nodes_bg_value=map_division.getDataFlat(),
                   nodes_border=map_division_border.getDataFlat()) \
               .overrideLayerNames([
                   self.labels['division'],
                   'algo2',
                   'snapshot_at_oneeighthdone'
               ]).display().save().final()

        self.merges = merges
        
        if print_stats:
            self.printEarlyDivisionStats()
        return self

    # Some descriptive statistics
    def printEarlyDivisionStats(self): 
        nodes_locale = self.maps['locale'].getDataFlat()
        
        print('How many things do we have?')
        print('{:10d} nodes (pixel), points across the map along a 2-dimensional grid'.format(len(nodes_locale)))
        print('{:10d} {locale:s}s, groupings where all of the nodes in a local area point {direction:s}ward to a single point'.format(
            len(np.unique(nodes_locale)), locale=self.labels['locale'], direction=self.flow_direction))
        print('{:14s} {extremum:s}s are the {direction_adj:s}est point in these {locale:s}s and are used to index them'.format(
            '', extremum=self.labels['extremum'], locale=self.labels['locale'], direction_adj=self.labels['direction_adjective']))
        print('{:10d} merges, times where two {:s}s are combined, based on the {direction_adj:s}est point outward from a {:s}'.format(
            len(self.merges), self.labels['locale'], self.labels['locale'], direction_adj=self.labels['direction_adjective']))
        print('{:14s} bridges or saddles are the name for the specific points where the merge happens'.format(''))
        print('{:14s} {path:s}s are the paths connecting bridges to their {extremum:s} -- following the {direction_adj:s}est local nodes'.format(
            '', path=self.labels['path'], extremum=self.labels['extremum'], direction_adj=self.labels['direction_adjective']))

        print('')
        print('Let\'s now think of how {locale:s}s intersect and are combined along the bridge nodes'.format(locale=self.labels['locale']))
        print('Think of the intersections like V shapes. greater {extremum:s} -> bridge -> lesser {extremum:s} -- are these Vs large? Are they partially underwater?'.format(
            extremum=self.labels['extremum']))

        print('')
        print('Do the {path:s}s in the connections cross the water line / interface? Considering what is above water (L) or below (S)?'.format(path=self.labels['path']))
        landsea_local_interfaces = np.array([x['landsea_local_interface'] for x in self.merges])
        landsea_division_interfaces = np.array([x['landsea_division_interface'] for x in self.merges])
        print('{:18s}: {:6s} {:6s}'.format('Interface Pattern','Local','Divisions'))
        for interface_pattern in sorted(np.unique(landsea_local_interfaces)):
            print('{:18s}: {:6d} {:6d}'.format(
                interface_pattern,
                np.sum(landsea_local_interfaces == interface_pattern),
                np.sum(landsea_division_interfaces == interface_pattern),
            ))

        print('')
        print('What\'s the distance between the bridge & the {extremum:s}?'.format(
            extremum=self.labels['extremum']))
        print('    local = neighboring {locale:s}s, divisions = among the {division:s} it is connected to.'.format(
            locale=self.labels['locale'], division=self.labels['division']))
        log_base = 10 ** 0.5
        local_distances_logged_rounded = np.log(np.array([x['distance_between_bridge_and_hi_local_extremum'] for x in self.merges])+0.001) // np.log(log_base)
        range_distances_logged_rounded = np.log(np.array([x['distance_between_bridge_and_hi_division_extremum'] for x in self.merges])+0.001) // np.log(log_base)
        print('{:16s}: {:6s} {:6s}'.format('Distance','Local','Divisions'))
        for distance_group in sorted(np.unique(range_distances_logged_rounded)):
            group_min = int(np.exp(distance_group * np.log(log_base)))
            group_max = int(np.exp((distance_group + 1) * np.log(log_base)))
            print('{:6d} to {:6d}: {:6d} {:6d}'.format(
                group_min, group_max,
                np.sum(local_distances_logged_rounded == distance_group),
                np.sum(range_distances_logged_rounded == distance_group),
            ))

    def computePaths(self, draw=False):
        HAS_NO_HIGHER_NEIGHBOR = -1 # constant when we are at a local maximum
        nodes_highest_neighbor_index = self.maps['highest_neighbor_index'].getDataFlat()
        nodes_path = np.zeros(self.n_nodes, dtype=bool)
        nodes_lo_bridge = np.zeros(self.n_nodes, dtype=bool)
        nodes_hi_bridge = np.zeros(self.n_nodes, dtype=bool)

        for i_merge in np.arange(len(self.merges)):
            merge = self.merges[i_merge]
            bridge_lo_index = merge['bridge_lo_index']
            bridge_hi_index = merge['bridge_hi_index']
            nodes_lo_bridge[bridge_lo_index] = True
            nodes_hi_bridge[bridge_hi_index] = True

            # Follow the nodes upward from the bridge on both sides, marking those as ridge nodes
            cur_node = bridge_lo_index
            while cur_node != HAS_NO_HIGHER_NEIGHBOR:
                nodes_path[cur_node] = True
                cur_node = nodes_highest_neighbor_index[cur_node]
            cur_node = bridge_hi_index
            while cur_node != HAS_NO_HIGHER_NEIGHBOR:
                nodes_path[cur_node] = True
                cur_node = nodes_highest_neighbor_index[cur_node]
                
        # # Temporarily disabling this until we need the data
        # self.maps['path'] = self.maps['highest_neighbor_index'].newChildInstance(
        #     {'values': 'path'},
        #     nodes_path
        # )

        # Draw the map
        if draw:
            self.getImageBase() \
                .addLayer('path', [0.2,0.5,1], nodes_selected=nodes_path, combine='set') \
                .addLayer('lo_bridge', [1, 1, 0], nodes_selected=nodes_lo_bridge, combine='set') \
                .addLayer('hi_bridge', [0, 1, 0], nodes_selected=nodes_hi_bridge, combine='set') \
                .addLayer('extremum', [1, 0, 1], nodes_selected=(nodes_highest_neighbor_index == HAS_NO_HIGHER_NEIGHBOR), combine='set') \
                .overrideLayerNames([
                    self.labels['division'],
                    'algo2',
                    self.labels['path']+'s1'
                ]).display().final()

        return self

    # Go through all merge lines and compute how far each node is from the node with the largest value
    def drawGlobalPathParentGradient(self):
        nodes_global_path_parent = self.maps['highest_neighbor_index'].getDataFlat()

        for merge in reversed(self.merges):
            node_being_flipped = merge['bridge_lo_index']
            node_new_uphill = merge['bridge_hi_index']

            while node_being_flipped != -1:
                node_old_uphill = nodes_global_path_parent[node_being_flipped]
                nodes_global_path_parent[node_being_flipped] = node_new_uphill
                node_new_uphill = node_being_flipped
                node_being_flipped = node_old_uphill

        # Now we have a new river graph, let's redo the distance
        nodes_distance_from_global_extremum = np.zeros(self.n_nodes, dtype=int)

        # This time we cannot go by the elevations because some low-elevation nodes may be "higher" in this new river graph
        # so we have to iterate through the 
        exploring_nodes = np.where(nodes_global_path_parent == -1)[0]

        for i_node in np.arange(self.n_nodes):
            node_index = exploring_nodes[i_node]

            uphill_node_index = nodes_global_path_parent[node_index]
            node_distance = 0 if uphill_node_index == -1 else nodes_distance_from_global_extremum[uphill_node_index]
            nodes_distance_from_global_extremum[node_index] = node_distance + 1

            # Add next nodes to the queue
            exploring_nodes = np.append(exploring_nodes, np.where(nodes_global_path_parent == node_index)[0])

        # Draw the locales by their distance from the extremums
        nodes_global_distance_normed = -nodes_distance_from_global_extremum
        self.getImageBase(nodes_bg_value=nodes_global_distance_normed, nodes_bg_colormap='rainbow') \
            .overrideLayerNames([
                self.labels['division'],
                'algo2',
                'dist_from_global_'+self.labels['extremum']+'_along_'+self.labels['path']+'s'
            ]).display().save().final()    

    def computePathInterfaceType(self, display_image=False):
        nodes_highest_neighbor_index = self.maps['highest_neighbor_index'].getDataFlat()
        nodes_path_interface = np.full(self.n_nodes, 'UNK')
        nodes_bridge = np.zeros(self.n_nodes, dtype=bool)
        nodes_locale_merge_interface = np.full(self.n_nodes, 'UNK')
        nodes_value = self.maps['elevation'].getDataFlat()

        for merge in self.merges:
            node_lo = merge['bridge_lo_index']
            node_hi = merge['bridge_hi_index']
            merge_interface = merge['landsea_local_interface']

            nodes_bridge[node_lo] = True
            nodes_bridge[node_hi] = True

            # Determine the type of paths from both merge points to their local extremum
            cur_node = node_lo
            while cur_node != -1:
                nodes_path_interface[cur_node] = min(merge_interface, nodes_path_interface[cur_node])
                nodes_locale_merge_interface[cur_node] = min(merge_interface, nodes_locale_merge_interface[cur_node])
                cur_node = nodes_highest_neighbor_index[cur_node]
            cur_node = node_hi
            while cur_node != -1:
                nodes_path_interface[cur_node] = min(merge_interface, nodes_path_interface[cur_node])
                cur_node = nodes_highest_neighbor_index[cur_node]

        # Draw the map
        if display_image:
            self.getImageBase() \
                .addLayer('ridge_merged_LLL', [.75, .75,   0], nodes_selected=(nodes_path_interface == 'LLL'), combine='set') \
                .addLayer('ridge_merged_SSS', [  0,  .5, .75], nodes_selected=(nodes_path_interface == 'SSS'), combine='set') \
                .addLayer('ridge_merged_LSS', [  0, .75,   0], nodes_selected=(nodes_path_interface == 'LSS'), combine='set') \
                .addLayer('ridge_merged_LSL', [.75,   0, .75], nodes_selected=(nodes_path_interface == 'LSL'), combine='set') \
                .addLayer('ridge_merged_LLS', [.75,   0,   0], nodes_selected=(nodes_path_interface == 'LLS'), combine='set') \
                .addLayer('bridge', 2, nodes_selected=nodes_bridge, combine='multiply') \
                .overrideLayerNames([
                    'merge_interfaces'
                ]).display().save().final()

        # # Temporarily disabling this until we need the data
        # self.maps['path_interface'] = self.maps['path'].newChildInstance(
        #     {'values': 'interface'},
        #     nodes_path
        # )

        return self

    def getLocaleAdjacencyList(self, verbose=False):
        locales_adjacency_list = {}

        for merge in self.merges:
            node_lo = merge['bridge_lo_index']
            node_hi = merge['bridge_hi_index']
            m1 = merge['locale_lo']
            m2 = merge['locale_hi']

            if m1 in locales_adjacency_list:
                locales_adjacency_list[m1] = np.append(locales_adjacency_list[m1], m2)
            else:
                locales_adjacency_list[m1] = np.array([m2])
            if m2 in locales_adjacency_list:
                locales_adjacency_list[m2] = np.append(locales_adjacency_list[m2], m1)
            else:
                locales_adjacency_list[m2] = np.array([m1])

        if verbose:
            # Print out descriptive statistics
            locales_adjacency_list_cardinality = np.array([len(locales_adjacency_list[x]) for x in locales_adjacency_list])
            n_locales_1_connection = np.sum(locales_adjacency_list_cardinality == 1)
            n_locales_2_connections = np.sum(locales_adjacency_list_cardinality == 2)
            n_locales_morethan5_connections = np.sum(locales_adjacency_list_cardinality > 5)
            n_locales_3to5_connections = len(locales_adjacency_list) - n_locales_1_connection - n_locales_2_connections - n_locales_morethan5_connections
            print((
                    '{locale:s}s with   1 connection : {:6d}\n' +
                    '{locale:s}s with   2 connections: {:6d}\n' +
                    '{locale:s}s with 3-5 connections: {:6d}\n' +
                    '{locale:s}s with  >5 connections: {:6d}\n'
                  )
                  .format(
                      n_locales_1_connection,
                      n_locales_2_connections,
                      n_locales_3to5_connections,
                      n_locales_morethan5_connections,
                      locale=self.labels['locale'],
                  ))

        return locales_adjacency_list
    
    # Function to split a part of a division (group of locales) to a new division
    def getNodesDivisionAfterPartition(self, nodes_division, dividing_locale, locales_adjacency_list, nodes_value):
        exploring_locales = [dividing_locale];
        extremum = dividing_locale;

        # Assign all recursive neighbors of dividing_locale to its group
        while len(exploring_locales) > 0:
            new_locale = exploring_locales.pop()
            if(nodes_value[new_locale] > nodes_value[extremum]):
                extremum = new_locale # Determine the final maximal point of the new division
            for neighbor_locale in locales_adjacency_list[new_locale]:
                if nodes_division[neighbor_locale] != dividing_locale:
                    nodes_division[neighbor_locale] = dividing_locale
                    exploring_locales.append(neighbor_locale)

        # Reassign that whole new division to the maximum point in that division
        nodes_division[nodes_division == dividing_locale] = extremum

        return nodes_division

    def drawDivisionsAcrossSeaLevel(self, print_filenames=False, display_images=False, final_analysis_filename=False):
        interfaces_to_split = ['LSL'] if self.flow_direction == 'up' else ['LSS', 'SSL']
        compare_across_full_path = self.flow_direction == 'up' 
        
        nodes_locale = self.maps['locale'].getDataFlat() # Use this to color the whole locales by the new division
        nodes_value = self.maps['elevation'].getDataFlat() # Use this to see if a extremum is above or below water
        locales_adjacency_list = self.getLocaleAdjacencyList() # start from scratch because we will actively edit it

        # The data we are computing
        node_global_extremum_index = np.argsort(nodes_value)[0] # This is the parent locale to all others
        nodes_division = np.full(self.n_nodes, node_global_extremum_index) # Start with everything being unified under this peak
        n_locales = len(locales_adjacency_list)

        # Iterate over the merge
        for merge in self.merges:
            # Only split up merges in the list of interfaces to split up
            merge_interface = merge['landsea_division_interface'] \
                if compare_across_full_path else merge['landsea_local_interface']
            if merge_interface not in interfaces_to_split:
                continue

            # Break the adjacency
            m1 = merge['locale_lo']
            m2 = merge['locale_hi']
            locales_adjacency_list[m1] = np.setdiff1d(locales_adjacency_list[m1], [m2])
            locales_adjacency_list[m2] = np.setdiff1d(locales_adjacency_list[m2], [m1])

            # Compute the new groups (using stand-in values for the highest extremum)
            # Note: We are doing double work since we don't know which side the overall extremum is on
            nodes_division = self.getNodesDivisionAfterPartition(nodes_division, m1, locales_adjacency_list, nodes_value)
            nodes_division = self.getNodesDivisionAfterPartition(nodes_division, m2, locales_adjacency_list, nodes_value)

        # Finally expand the division color to all nodes
        for locale_index in np.arange(len(nodes_locale)):
            nodes_division[nodes_locale == locale_index] = nodes_division[locale_index]

        map_division = self.maps['locale'].newChildInstance({'values': 'division'}, nodes_division)
        map_division_border = map_transforms.getBorder(map_division, 1)

        layer_names = [
            self.labels['division'] + 's',
            'separating_{:s}_merges'.format('+'.join(interfaces_to_split)),
        ]
        if compare_across_full_path:
            layer_names.append('compare_across_full_path')
        if final_analysis_filename:
            # For the images at the end of the analysis
            layer_names = [self.labels['sealevel_division'] + 's']

        drawing = self.getImageBase( 
                 nodes_bg_value=nodes_division,
                 nodes_border=map_division_border.getDataFlat()) \
            .overrideLayerNames(layer_names).save()

        if print_filenames:
            print(drawing.getFilename())
        if display_images:
            drawing.display().final()

        return nodes_division
