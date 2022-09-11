from planet_wars.planet_wars import PlanetWars, Player, Planet, Fleet, Order


def clone_game_object(game: PlanetWars) -> PlanetWars:
    """
    Cloned the given game object
    """
    cloned_fleet = []
    cloned_planets = []
    for f in game.fleets:
        cloned_fleet.append(Fleet(
            f.owner, f.num_ships, f.source_planet_id, f.destination_planet_id, f.total_trip_length, f.turns_remaining
        ))
    for p in game.planets:
        cloned_planets.append(Planet(p.planet_id, p.owner, p.num_ships, p.growth_rate, p.x, p.y))
    return PlanetWars(planets=cloned_planets, fleets=cloned_fleet)


def switch_players_of_game_object(game: PlanetWars):
    """
    Switch between player 1 and player 2 in the given game object
    """
    for p in game.planets:
        if p.owner == 1:
            p.owner = 2
        elif p.owner == 2:
            p.owner = 1

    for f in game.fleets:
        if f.owner == 1:
            f.owner = 2
        elif f.owner == 2:
            f.owner = 1


class GameManager:
    """
    The engine logic - manage the game. Calles the bots play_turn function to get the issued orders and
    then apply these orders and excited all the turns logic like fleet fights, planet growth etc.

    Also keeps track of the points and tells the winning bot
    """

    MAX_TURNS = 200

    PLAYER_1_WIN_STATE = "Player 1 Wins"
    PLAYER_2_WIN_STATE = "Player 2 Wins"
    TIE_STATE = "Tie"
    IN_GAME_STATE = "Still In Game"

    def __init__(self, map_str: str, player_1: Player, player_2: Player, raise_bot_exceptions: bool = False):
        """
        Initiate a game
        :param map_str: The map to play in, as stirng.
        :param player_1: Player 1 bot
        :param player_2: Player 2 bot
        :param raise_bot_exceptions: If False catch exceptions from the player bots
        """
        self.game = PlanetWars.parse_game_state(map_str)
        self.original_map = clone_game_object(self.game)
        self.player_1 = player_1
        self.player_2 = player_2
        self.raise_bot_exceptions = raise_bot_exceptions
        self.turns = 0
        self.str_turns_for_display = []

    def safely_run_bot(self, player, game_object):
        """
        Safely run the player bot.

        :param player: The bot to run
        :param game_object: The game object to give the bot
        :return: The bot orders or False if the bot raised Exception of the orders are not iterable
        """
        # TODO add timeout to the play_turn call
        try:
            if self.turns == 0:
                player.new_game_has_started(game_object)
            orders = player.play_turn(game_object)
            # Don't fail if you return None - replace it with empty array
            orders = orders if orders is not None else []
            # Don't fail if you return order instead of list of orders
            if isinstance(orders, Order):
                orders = [orders]
            [o for o in orders]  # check orders is iterable
            return orders
        except Exception as e:
            if self.raise_bot_exceptions:
                raise e

            print(f"Player {player.__class__.__name__} throw exception {e.__class__.__name__}: {e}")
            return False

    def execute_order(self, order: Order, player_id: int) -> bool:
        """
        Execute the given order - send the ship in a new flee from the source planet towards the destination.
        :param order: The order to execute
        :param player_id: The player sening this order
        :return: True is the order successfully sent.
        """
        order = Order(order.source_planet_id, order.destination_planet_id, order.num_ships)
        if not order.verify_order(self.game, player_id):
            return False

        # execute order
        source_planet = self.game.get_planet_by_id(order.source_planet_id)
        destination_planet = self.game.get_planet_by_id(order.destination_planet_id)
        total_trip_length = Planet.distance_between_planets(source_planet, destination_planet)

        source_planet.num_ships -= order.num_ships

        fleet = Fleet(
            owner=player_id,
            num_ships=order.num_ships,
            source_planet_id=order.source_planet_id,
            destination_planet_id=order.destination_planet_id,
            total_trip_length=total_trip_length,
            turns_remaining=total_trip_length  # assume speed of 1 per turn
        )
        self.game.fleets.append(fleet)
        return True

    def advance(self):
        """
        Advance all the flees - reduce the turns_remaining by 1
        """
        for fleet in self.game.fleets:
            fleet.turns_remaining -= 1

    def population_growth(self):
        """
        Increase the population of all non neutral planets
        """
        for planet in self.game.planets:
            if planet.owner != 0:
                planet.num_ships += planet.growth_rate

    def arrival(self):
        """
        Handle when a flee arrive at a planet.
        If the flee owner different from the planet owner - a battle occur.
        The battle happens between the planet population and all the fleet arriving to the planet this turn.
        The player with the most ships wins the battle,
        in case of a tie the current owner stays the owner of the planet.
        """
        arriving_fleets = [f for f in self.game.fleets if f.turns_remaining == 0]
        if len(arriving_fleets) == 0:
            return

        self.game.fleets = [f for f in self.game.fleets if f.turns_remaining > 0]

        for planet in self.game.planets:

            # If no fleet is arriving at to the planet - continue
            if not any(fleet.destination_planet_id == planet.planet_id for fleet in arriving_fleets):
                continue

            forces = {0: 0, 1: 0, 2: 0}
            forces[planet.owner] = planet.num_ships
            for fleet in arriving_fleets:
                if fleet.destination_planet_id == planet.planet_id:
                    forces[fleet.owner] += fleet.num_ships

            max_force_size = max(list(forces.values()))
            largest_force_owner = [owner for owner, size in forces.items() if size == max_force_size]
            if len(largest_force_owner) > 1:
                planet.num_ships = 0  # in a tie the original owner keeps the planet with zero ships remaining
                continue

            # When no tie the planet belongs to the biggest force.
            # The num_ships in the planet is the biggest force size minus the second biggest force size
            second_largest_force = max([size for size in forces.values() if size < max_force_size])
            planet.owner = largest_force_owner[0]
            planet.num_ships = max_force_size - second_largest_force

    def get_player_score(self, player_num: int):
        """
        Player score is the total number of ships it owns
        :param player_num: The player number
        :return: The player's score
        """
        return int(self.game.total_ships_by_owner(owner=player_num))

    def check_endgame_conditions(self):
        """
        The game ends if one players lost all his ships or we reached MAX_TURNS
        :return: The game state - tie, player 1 wins, player 2 wins or still in-game
        """
        player_1_num_ships = self.get_player_score(player_num=1)
        player_2_num_ships = self.get_player_score(player_num=2)

        if player_1_num_ships == 0:
            if player_2_num_ships == 0:
                return self.TIE_STATE
            return self.PLAYER_2_WIN_STATE
        if player_2_num_ships == 0:
            return self.PLAYER_1_WIN_STATE

        if self.turns >= self.MAX_TURNS:
            if player_1_num_ships > player_2_num_ships:
                return self.PLAYER_1_WIN_STATE
            elif player_1_num_ships < player_2_num_ships:
                return self.PLAYER_2_WIN_STATE
            else:
                return self.TIE_STATE

        return self.IN_GAME_STATE

    def make_turn(self) -> str:
        """
        Run one turn.
        Get the orders from the player's bot, execute them and advance the game one turn
        (a.k.a advance flees, increase planets population and handle flees arrival)

        :return: The game state - tie, player 1 wins, player 2 wins or still in-game
        """
        # get orders of player 1
        game_object_for_player_1 = clone_game_object(self.game)
        game_object_for_player_1.turns = self.turns
        orders_of_player_1 = self.safely_run_bot(self.player_1, game_object_for_player_1)
        if orders_of_player_1 is False:
            return self.PLAYER_2_WIN_STATE

        # get orders of player 2
        game_object_for_player_2 = clone_game_object(self.game)
        switch_players_of_game_object(game_object_for_player_2)
        game_object_for_player_2.turns = self.turns
        orders_of_player_2 = self.safely_run_bot(self.player_2, game_object_for_player_2)
        if orders_of_player_2 is False:
            return self.PLAYER_1_WIN_STATE

        for order in orders_of_player_1:
            self.execute_order(order, player_id=1)
        for order in orders_of_player_2:
            self.execute_order(order, player_id=2)

        self.advance()
        self.population_growth()
        self.arrival()

        self.turns += 1
        self.add_turn_for_display()

        return self.check_endgame_conditions()

    def run_game(self) -> str:
        """
        Run the game - run turns until the game end.
        :return: The game finish state - tie, player 1 wins or player 2 wins
        """
        state = self.IN_GAME_STATE
        while state == self.IN_GAME_STATE:
            state = self.make_turn()
        print(state)
        return state

    def add_turn_for_display(self):
        """
        Add self.str_turns_for_display string representation of the game state
        """
        planets_desc = ",".join(f"{p.owner}.{int(p.num_ships)}" for p in self.game.planets)
        if len(self.game.fleets) == 0:
            self.str_turns_for_display.append(planets_desc)
        else:
            fleet_desc = ",".join(
                f"{f.owner}.{int(f.num_ships)}.{f.source_planet_id}.{f.destination_planet_id}."
                f"{int(f.total_trip_length)}.{int(f.turns_remaining)}"
                for f in self.game.fleets
            )
            self.str_turns_for_display.append(planets_desc + "," + fleet_desc)

    def get_description_for_display(self):
        """
        :return: String representation of the game occurred.
        """
        map_desc = ":".join(f"{p.x},{p.y},{p.owner},{p.num_ships},{p.growth_rate}" for p in self.original_map.planets)
        turns_desc = ":".join(self.str_turns_for_display)
        return map_desc + "|" + turns_desc
