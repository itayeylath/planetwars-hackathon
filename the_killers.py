from operator import index
from typing import Iterable
from typing import Iterable, List
import pandas as pd
import awasomeBot
from baseline_bot import AttackWeakestPlanetFromStrongestBot, AttackEnemyWeakestPlanetFromStrongestBot, \
    AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot, get_random_map
from planet_wars.battles.tournament import run_and_view_battle, TestBot
from planet_wars.planet_wars import Player, PlanetWars, Order, Planet


class the_killers(Player):
    """
    Example of very simple bot - it send flee from its strongest planet to the weakest enemy/neutral planet
    """
# the killers
    def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner != PlanetWars.ME]

    def ships_to_send_in_a_flee(self, source_planet: Planet, dest_planet: Planet) -> int:
        return source_planet.num_ships // 2

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # (1) If we currently have a fleet in flight, just do nothing.
        if len(game.get_fleets_by_owner(owner=PlanetWars.ME)) >= 1:
            return []
        # make each of my planets to attack the closest neutral planet
        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        if len(my_planets) == 0:
            return []
        order_list =[]
        neutral_planets = game.get_planets_by_owner(owner=PlanetWars.NEUTRAL)
        if len(neutral_planets) > 0:
            
            for planet in my_planets:
                close_neutral = self.get_closest_planet_that_can_kill(planet,neutral_planets)
                if planet.num_ships // 2 > close_neutral.num_ships:
                    order_list.append(self.get_order(planet, close_neutral))
            return order_list
        else:
            enemy_planets = game.get_planets_by_owner(owner=PlanetWars.ENEMY)
            for planet in my_planets:
                close_enemy = self.get_closest_planet(planet,enemy_planets)
                order_list.append(self.get_order(planet, close_enemy))
            return order_list    

    def get_closest_planet(self,source: Planet, planets: List[Planet]):
        sorted_p = planets.copy()
        sorted_p.sort(key = lambda x: Planet.distance_between_planets(source, x))         
        return sorted_p[0]

    def get_order(self,source:Planet, dest):
        return Order(source,dest,source.num_ships//2)

    def get_closest_planet_that_can_kill(self,source: Planet, planets: List[Planet]):
        sorted_p = planets.copy()
        sorted_p.sort(key = lambda x: Planet.distance_between_planets(source, x))
        for p in sorted_p:
            if p.num_ships < source.num_ships // 2:
                return p           
        return sorted_p[0]

def view_bots_battle():
    """
    Runs a battle and show the results in the Java viewer

    Note: The viewer can only open one battle at a time - so before viewing new battle close the window of the
    previous one.
    Requirements: Java should be installed on your device.
    """
    map_str = get_random_map()
    run_and_view_battle(the_killers(), AttackWeakestPlanetFromStrongestBot(), map_str)


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
