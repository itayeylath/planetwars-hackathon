from math import gamma
from typing import Iterable

import pandas as pd

from baseline_bot import AttackWeakestPlanetFromStrongestBot, AttackEnemyWeakestPlanetFromStrongestBot, \
    AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot, get_random_map
from planet_wars.battles.tournament import run_and_view_battle, TestBot
from planet_wars.planet_wars import Player, PlanetWars, Order, Planet


class awasomeBot(Player):
    """
    Implement here your smart logic.
    Rename the class and the module to your team name
    """
    def __init__(self) -> None:
        super().__init__()
    def get_all_non_mine_planets(self,game:PlanetWars):
        all_planets = game.get_planets_by_owner(PlanetWars.NEUTRAL)
        enemy_planets = game.get_planets_by_owner(PlanetWars.ENEMY)
        for p in enemy_planets:
            all_planets.append(p)
        return all_planets
            
    def get_closest_planet(self,game:PlanetWars,my_planet:Planet):
        all_planets = self.get_all_non_mine_planets(game)
        if(len(all_planets) == 0):
            return []
        closest_planet = all_planets[0]
        for p in all_planets:
            distance = Planet.distance_between_planets(p,my_planet)
            closest_planet_distance = Planet.distance_between_planets(my_planet,closest_planet)
            if(distance < closest_planet_distance):
                closest_planet = p
        return closest_planet
        

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """ 
        orders = []
        my_planets = game.get_planets_by_owner(game.ME)
        if(len(my_planets) == 0):
            return []

        for mp in my_planets:
            closest_planet = self.get_closest_planet(game,mp)
            if(closest_planet != []):
                orders.append(Order(mp,closest_planet,closest_planet.num_ships + 30))
        return orders


def view_bots_battle():
    """
    Runs a battle and show the results in the Java viewer

    Note: The viewer can only open one battle at a time - so before viewing new battle close the window of the
    previous one.
    Requirements: Java should be installed on your device.
    """
    map_str = get_random_map()
    run_and_view_battle(AttackWeakestPlanetFromStrongestBot(), awasomeBot(), map_str)


def check_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = AttackWeakestPlanetFromStrongestBot()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            AttackEnemyWeakestPlanetFromStrongestBot(), AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot()
        ],
        maps=maps
    )
    tester.run_tournament()

    # for a nicer df printing
    pd.set_option('display.max_columns', 30)
    pd.set_option('expand_frame_repr', False)

    print(tester.get_testing_results_data_frame())
    print("\n\n")
    print(tester.get_score_object())

    # To view battle number 4 uncomment the line below
    # tester.view_battle(4)


if __name__ == "__main__":
    # check_bot()
    view_bots_battle()
