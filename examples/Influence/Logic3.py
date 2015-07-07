#! /usr/bin/env python3
from maps import IslandMap, FriendMap
from matrix import StrictMatrix

################################################################################

class Faction:

    "Faction(info) -> Faction instance"

    __slots__ = 'info', 'active', 'control'

    def __init__(self, info):
        "Initialize the faction structure with starting information."
        self.info = info    # Data that is associated with faction
        self.active = True  # Flag for faction life status (if KO is true)
        self.control = 0    # Total number of islands under influence

################################################################################

class Island:

    "Island(island_map, friend_map, key) -> Island instance"

    __slots__ = '__friends', '__population', '__faction'

    def __init__(self, island_map, friend_map, key):
        "Initialize the island instance variables as needed."
        self.__friends = self.__find_friends(island_map, friend_map, key)
        self.__population = 0
        self.__faction = None

    @staticmethod
    def __find_friends(island_map, friend_map, key):
        "Generate a list of coordinates for neighbors to this island."
        y_offset, x_offset = key
        y_offset -= friend_map.y
        x_offset -= friend_map.x
        friends = []
        for (row, column), value in friend_map:
            if value:
                key = row + y_offset, column + x_offset
                try:
                    if island_map[key]:
                        friends.append(key)
                except (IndexError, AssertionError):
                    pass
        assert friends
        return tuple(friends)

    def grow(self, immigrants, faction, knockout):
        "Increase the island population by immigrants."
        self.__population += immigrants
        if self.faction is not faction:
            if self.faction is not None:
                self.faction.control -= 1
                if knockout and self.faction.control == 0:
                    self.faction.active = False
            self.__faction = faction
            self.faction.control += 1

    def balance(self, tomorrow, key, knockout):
        "Alter self and friends on tomorrow while respecting KO flag."
        assert self.critical
        island = tomorrow[key]
        island.__population -= self.total_friends
        if island.__population == 0:
            island.faction.control -= 1
            island.__faction = None
        for key in self.__friends:
            tomorrow[key].grow(1, self.faction, knockout)

    @property
    def critical(self):
        "Flag indicating if the population on this island is critical."
        return self.__population >= len(self.__friends)

    @property
    def faction(self):
        "The faction (or None) that currently controls this island."
        return self.__faction

    @property
    def friends(self):
        "List of friend coordinates for this island."
        return self.__friends

    @property
    def total_friends(self):
        "Number of friends related to this island."
        return len(self.friends)

    @property
    def population(self):
        "Total number of people on this island."
        return self.__population

################################################################################

class Influence:

    "Influence(islands, friends, factions, knockout) -> Influence instance"

    __slots__ = ('__islands', '__cursor', '__factions', '__knockout',
                 '__current_faction', '__total_moves', '__total_shift')

    def __init__(self, island_map, friend_map, factions, knockout):
        "Initialize scenario with various state-keeping variables."
        assert len(factions) > 1
        self.__create_islands(island_map, friend_map)
        self.__cursor = friend_map
        self.__factions = tuple(Faction(info) for info in factions)
        self.__knockout = knockout
        self.__current_faction = 0
        self.__total_moves = 0
        self.__total_shift = 0

    def __create_islands(self, island_map, friend_map):
        "Generate a matrix of islands with their friends."
        islands = self.__islands = StrictMatrix(island_map.rows,
                                                island_map.columns,
                                                Island)
        for key, value in island_map:
            if value:
                islands[key] = Island(island_map, friend_map, key)
        self.__check_board()

    def __check_board(self):
        "Ensure that any island can get to any other island."
        for position, island in self.__islands:
            if island is not None:
                break
        else:
            raise ValueError('There are no islands!')
        group, search = {position}, [position]
        while search:
            position = search.pop(0)
            for friend in self.__islands[position].friends:
                if friend not in group:
                    group.add(friend)
                    search.append(friend)
        assert len(group) == self.total_islands, 'Maps are not compatible!'

    def bless(self, position, grow_by):
        "Try to grow island population at position via current faction."
        if self.can_continue and self.__may_influence(position):
            self.islands[position].grow(grow_by, self.current_faction, False)
            self.__next_faction()
            self.__total_moves += 1

    def __may_influence(self, position):
        "Determine if present faction may influence island at position."
        island = self.islands[position]
        return island is not None and \
               island.faction in (None, self.current_faction)

    def spread(self):
        "Balance populations in critical islands."
        if self.critical:
            tomorrow = self.islands.copy()
            for key, value in self.islands:
                if value is not None and value.critical:
                    value.balance(tomorrow, key, self.knockout)
            self.__islands = tomorrow
            self.__next_faction()
            self.__total_shift += 1

    def __next_faction(self):
        "Try to select the next faction for a turn."
        if self.can_continue:
            start, factions = self.faction_index, self.factions
            self.__current_faction = (self.faction_index + 1) % factions
            while not self.can_move:
                self.__current_faction = (self.faction_index + 1) % factions
                assert not self.faction_index == start

    # ==================================================================== #

    @property
    def can_continue(self):
        "Flag that allows further operations to be executed."
        return not (self.complete or self.critical)

    @property
    def can_move(self):
        "Flag indicating if current faction may influence any island."
        faction = self.current_faction
        return faction.active and (faction.control > 0 or
                                   self.total_neutral > 0)

    @property
    def total_moves(self):
        "Total number of moves that have been made so far."
        return self.__total_moves

    @property
    def total_shift(self):
        "Total number of balancing actions that have been executed."
        return self.__total_shift

    # ==================================================================== #

    @property
    def islands(self):
        "Matrix having the map of islands in it."
        return self.__islands

    @property
    def friends(self):
        "Cursor used to define island relationships."
        return self.__cursor

    @property
    def factions(self):
        "Number of individual interest groups in scenario."
        return len(self.__factions)

    @property
    def knockout(self):
        "Flag specifying if factions continue after being defeated."
        return self.__knockout

    # ==================================================================== #

    @property
    def faction_index(self):
        "Index for faction that currently may alter the environment."
        return self.__current_faction

    @property
    def current_faction(self):
        "Instance of faction currently available for a move."
        return self.__factions[self.faction_index]

    @property
    def active_factions(self):
        "Numbers for factions still involved in scenario."
        return tuple((i for i, f in enumerate(self.__factions) if f.active))

    @property
    def defeated_factions(self):
        "Number for factions that have been eliminated."
        return tuple((i for i, f in enumerate(self.__factions) if not f.active))

    @property
    def total_active_factions(self):
        "Number of factions still involved in scenario."
        return len(self.active_factions)

    @property
    def controlling_factions(self):
        "Factions that have control of the board."
        return tuple((i for i, f in enumerate(self.__factions)
                      if f.control > 0))

    @property
    def total_controlling_factions(self):
        "Number of factions that have control on the board."
        return len(self.controlling_factions)

    @property
    def complete(self):
        "Flag signifying if scenario has been finished." 
        return self.total_moves >= self.factions and \
               self.total_controlling_factions == 1

    @property
    def critical(self):
        "Flag showing if at least one island is critical."
        return any(island.critical for island in self.island_iter)

    @property
    def ratings(self):
        "Power score given to each faction."
        return tuple(f.control for f in self.__factions)

    # ==================================================================== #

    @property
    def island_iter(self):
        "Iterator over islands that exists and ignores empty spaces."
        return (value for key, value in self.islands if value is not None)

    @property
    def total_islands(self):
        "Count of islands present for influence."
        return len(tuple(self.island_iter))

    @property
    def total_neutral(self):
        "Count of islands not under influence of a faction."
        return sum((island.faction is None for island in self.island_iter))

    @property
    def total_occupied(self):
        "Count of islands under the control of a faction."
        return sum((island.faction is not None for island in self.island_iter))
