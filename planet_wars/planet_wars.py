from abc import abstractmethod
from collections import defaultdict
from math import ceil, sqrt
from sys import stdout
from typing import Union, Iterable, List

import pandas as pd


def list_to_data_frame(lst: List, columns: List[str]):
    """
    Create a data frame from a list of objects.
    The logic is, for each string in columns set
        df[column] = [obj.column for obj in lst]

    :param lst: List of objects
    :param columns: List of string. These strings needs to be members of all the objects in the given list.
                    These strings will be the columns of the returned data frame.
    :return: The created data frame
    """
    data = defaultdict(list)
    for obj in lst:
        for member in columns:
            data[member].append(getattr(obj, member))
    return pd.DataFrame(data)


class Fleet:
    def __init__(
            self, owner: int, num_ships: int, source_planet_id: int, destination_planet_id: int,
            total_trip_length: float, turns_remaining: int
    ):
        """
        :param owner: The owner of the fleet. 1 - you are the owner, 2 - enemy fleet (can not be 0)
        :param num_ships: How many ships in the fleet
        :param source_planet_id: The id of the planet the fleet was sent from
        :param destination_planet_id: The id of the fleet planet destination
        :param total_trip_length: The destination between source_planet and destination_planet
        :param turns_remaining: How many turns left till the fleet will reach its destination (and fight!).
        """
        self.owner = owner
        self.num_ships = num_ships
        self.source_planet_id = source_planet_id
        self.destination_planet_id = destination_planet_id
        self.total_trip_length = total_trip_length
        self.turns_remaining = turns_remaining


class Planet:
    def __init__(self, planet_id: int, owner: int, num_ships: int, growth_rate: int, x: float, y: float):
        """
        :param planet_id: Id of the planet
        :param owner: The owner of the planet. 1 - you are the owner, 2 - enemy planet, 0 - neutral planet
        :param num_ships: How many ships currently in the planet
        :param growth_rate: The planet growth rate. Each turn, if the planet is not neutral 'growth_rate'
                            ships will be added to the planet
        :param x: The x coordinate of the planet location
        :param y: The y coordinate of the planet location
        """
        self.planet_id = planet_id
        self.owner = owner
        self.num_ships = num_ships
        self.growth_rate = growth_rate
        self.x = x
        self.y = y

    @staticmethod
    def distance_between_planets(source_planet: "Planet", destination_planet: "Planet") -> int:
        """
        Returns the distance between the two given planets. Fleet from source_planet will reach destination_planet
        after 'distance' turns. (Fleet speed is 1 distance per turn)
        """
        dx = source_planet.x - destination_planet.x
        dy = source_planet.y - destination_planet.y
        return int(ceil(sqrt(dx * dx + dy * dy)))


class PlanetWars:
    """
    The main object of the game -
    include all the information on the game state, all the planets and all the fleets in the map.
    Also have some useful methods
    """

    NEUTRAL = 0
    ME = 1
    ENEMY = 2

    def __init__(self, planets: List[Planet], fleets: List[Fleet]):
        """
        :param planets: All the planets in the map
        :param fleets: All the fleets in the map
        """
        self.planets = planets
        self.fleets = fleets
        self.turns = 0

    def get_planets_by_owner(self, owner):
        """
        self.get_planets_by_owner(owner=PlanetWars.ME) will return all your planets
        self.get_planets_by_owner(owner=PlanetWars.ENEMY) will return all enemy's plants
        self.get_planets_by_owner(owner=PlanetWars.NEUTRAL) will return all neutral planets
        """
        return [p for p in self.planets if p.owner == owner]

    def get_planet_by_id(self, planet_id):
        for p in self.planets:
            if p.planet_id == planet_id:
                return p

    def get_fleets_by_owner(self, owner):
        """
        self.get_fleets_by_owner(owner=PlanetWars.ME) will return all your fleets
        self.get_fleets_by_owner(owner=PlanetWars.ENEMY) will return all enemy's fleets
        """
        return [f for f in self.fleets if f.owner == owner]

    def total_ships_by_owner(self, owner):
        """
        Return all the ships owned by the given owner.
        This is a good number to use as "score".
        If the game didn't end till turn 200 the winner will be the player with the most ships.
        """
        return (
                sum(p.num_ships for p in self.get_planets_by_owner(owner)) +
                sum(f.num_ships for f in self.get_fleets_by_owner(owner))
        )

    def get_planets_data_frame(self):
        """
        :return: All the planets in the map as data frame
        """
        return list_to_data_frame(
            lst=self.planets, columns=["planet_id", "owner", "num_ships", "growth_rate", "x", "y"]
        )

    def get_fleets_data_frame(self):
        """
        :return: All the fleets in the map as data frame
        """
        return list_to_data_frame(
            lst=self.fleets,
            columns=[
                "owner", "num_ships", "source_planet_id", "destination_planet_id", "total_trip_length", "turns_remaining"
            ]
        )

    def __str__(self):
        planets_str = "\n".join(f"P {p.x} {p.y} {p.owner} {p.num_ships} {p.growth_rate}" for p in self.planets)
        fleets_str = "\n".join(
            f"F {f.owner} {f.num_ships} {f.source_planet_id} "
            f"{f.destination_planet_id} {f.total_trip_length} {f.turns_remaining}"
            for f in self.fleets
        )
        return planets_str + "\n\n" + fleets_str

    @staticmethod
    def parse_game_state(s: str) -> "PlanetWars":
        """
        Parse the PlanetWars object from map string.
        :param s: String representation of the map
        :return: The created PlanetWars object
        """
        planets = []
        fleets = []
        lines = s.split("\n")
        planet_id = 0

        for line in lines:
            line = line.split("#")[0]  # remove comments
            tokens = line.split(" ")
            if len(tokens) == 1:
                continue
            if tokens[0] == "P":
                if len(tokens) != 6:
                    return 0
                p = Planet(planet_id,  # The ID of this planet
                           int(tokens[3]),  # Owner
                           int(tokens[4]),  # Num ships
                           int(tokens[5]),  # Growth rate
                           float(tokens[1]),  # X
                           float(tokens[2]))  # Y
                planet_id += 1
                planets.append(p)
            elif tokens[0] == "F":
                if len(tokens) != 7:
                    return 0
                f = Fleet(int(tokens[1]),  # Owner
                          int(tokens[2]),  # Num ships
                          int(tokens[3]),  # Source
                          int(tokens[4]),  # Destination
                          int(tokens[5]),  # Total trip length
                          int(tokens[6]))  # Turns remaining
                fleets.append(f)
            else:
                return 0

        return PlanetWars(planets, fleets)


class Order:
    """
    Order to send fleet of 'num_ships' ships from source_planet to destination_planet.
    """

    def __init__(self, source_planet: Union[Planet, int], destination_planet: Union[Planet, int], num_ships: int):
        """
        :param source_planet: The planet to send the ships from. You must own this planet.
                              Give Planet object of planet_id.
        :param destination_planet: The planet to send the fleet to. Give Planet object of planet_id.
        :param num_ships: The number of ships in the fleet.
                          The source planet must have enough ships to support the order.
        """
        self.source_planet_id = self._get_planet_id(source_planet)
        self.destination_planet_id = self._get_planet_id(destination_planet)
        self.num_ships = num_ships

    @staticmethod
    def _get_planet_id(planet) -> int:
        """
        Return the planet id, if the input is already the planet id - simpely return the given input
        """
        return planet.planet_id if isinstance(planet, Planet) else planet

    def __str__(self):
        return f"{self.source_planet_id} {self.destination_planet_id} {self.num_ships}"

    def verify_order(self, game: PlanetWars, player: int = 1):
        """
        Verify the order is legal.
        Order is legal if:
        1. The source planet exists and owned by the player issued the order
        2. The destination planet exists and different from the source planet
        3. The source planet have enough ships to support the order
        4. The source planet is not neutral

        :param game: The PlanetWars object representing the map
        :param player: The player sending the order. Can be 1 or 2.
        :return:
        """
        if self.source_planet_id is None or self.destination_planet_id is None:
            return False
        source_planet = game.get_planet_by_id(self.source_planet_id)
        if source_planet is None:
            return False
        if game.get_planet_by_id(self.destination_planet_id) is None:
            return False
        if self.source_planet_id == self.destination_planet_id:
            return False
        if source_planet.owner != player or source_planet.owner == 0:
            return False
        if source_planet.num_ships < self.num_ships:
            return False
        if self.num_ships <= 0:
            return False
        return True


class Player:
    """
    Implement this class to create a bot that player the game!
    You need to:
    1. Change the NAME to your team's name
    2. implement the play_turn function
    """

    NAME = "Give The Player Name Here"

    @abstractmethod
    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        This function will be called in each turn, here you should write the bot logic:
         - Use the game object given to view the map
         - Implement your bot logic and...
         - return a list of orders - issuing fleets to conquer planets and fight the enemy !!!

        :param game: PlanetWars object representing the map
        :return: List of orders - fleet to send in this turns.
        """
        raise NotImplemented("Here is where the fun happens - implement here your bot")

    def new_game_has_started(self, game: PlanetWars):
        """
        This function will be called at the beginning of each game.
        Here is the place to restart the game state.
        for example if you count the number of ships you sent in fleets here is the place to set this counter back to 0
        Note: Exception here will make you lose the game
        :param game: PlanetWars object representing the map initial state
        """
        pass
