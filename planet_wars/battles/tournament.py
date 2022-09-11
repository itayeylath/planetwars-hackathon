import os
import random
import time
from typing import List, Optional

import pandas as pd

from dataclasses import dataclass

from planet_wars import PLANET_WARS_MODULE_PATH, SHOW_GAME_JAR_PATH, TMP_DIR_PATH
from planet_wars.engine.game_logic import GameManager
from planet_wars.planet_wars import Player, PlanetWars, list_to_data_frame


@dataclass
class BattleResult:
    """
    Battle result, details about a battle that occurred
    """
    battle_id: int
    finish_state: str
    winner: int  # The battle winner: 1 -> player 1 won, 2 -> player 2 worn, 0 -> tie
    player_1_name: str
    player_2_name: str
    player_1_score: int
    player_2_score: int
    turns: int  # How many turns the battle occurred
    description_for_display: str  # String representation of the battle for display
    end_game_object: PlanetWars  # The PlanetWars object after the game ended


@dataclass
class PlayerScore:
    """
    Details about the player tournament score.
    """
    player_name: str  # The player name
    rank: Optional[int]  # The rank in the tournament (1 is first place)
    battle_count: int  # How many battles fought
    won: int  # How many times won the battle
    lost: int  # How many times lost the battle
    tie: int  # How many battles ended in tie
    points: float  # The points of the player. Equal:  won + 0.5 * tie
    total_score: int  # The total score (num of ship when the game ends) in all battles
    total_enemy_score: int  # The total scores of all the enemies fought.
    mean_score: float   # The player mean score
    mean_enemy_score: float  # All enemies mean score
    killed_all_enemy_units: int   # How many games ended with the player killing all the enemy ships
    all_units_died: int  # How many games ended with the enemy killing all the player ships
    wins_as_player_1: int  # how many times the player won as player 1
    wins_as_player_2: int   # How many times the player won as player 2


class Tournament:
    """
    Runs a tournament between list of players' bots.
    2 options:

    all_against_all = True
    In the tournament each player will battle each other player (on each map).
    The winner is the player that wins the most battle (tie is awarded with half of the points)

    all_against_all = False
    Will have a fighting rounds where only the winner goes to the next round.
    In each round each player will fight 2 other random players and will have to win/reach tie in at least one battle
    to go to the next round.
    The player that wins the last round is the winner.
    """

    def __init__(
            self,
            players: List[Player],
            maps: List[str],
            raise_bot_exceptions: bool=False,
            all_against_all: bool = True
    ):
        """
        Battles will be between each player in each map.
        Each 2 players and map will have 2 battles - changing sides between them.
        :param players: List of players
        :param maps: List of maps
        :param raise_bot_exceptions: If False catch exceptions from the player bots
        :param all_against_all: If True all bots play against all bots
        """
        assert len(players) >= 2, "tournament needs at least 2 players"
        assert len(maps) >= 1, "tournament needs at least 1 map"
        self.players = players
        self.maps = maps
        self.raise_bot_exceptions = raise_bot_exceptions
        self.battle_results = []
        self.last_battle_id = 0
        self.all_against_all = all_against_all

    def run_tournament(self) -> List[BattleResult]:
        """
        Runs the tournament - In the tournament each player will battle each other player (on each map).
        :return: The battle results
        """
        self.battle_results = []
        for map_str in self.maps:
            if self.all_against_all:
                for player1 in self.players:
                    for player2 in self.players:
                        if player1 == player2:
                            continue
                        self.battle_results.append(
                            self.run_battle(map_str, player1=player1, player2=player2)
                        )
            else:
                # Shuffle the players so the pairs are random
                shuffled_players = self.players.copy()
                random.shuffle(shuffled_players)
                next_round_players = shuffled_players

                # Some initializations
                round_number = 0
                round_pairs = []
                round_winners = []

                # Main tournament loop
                while len(next_round_players) > 1:
                    round_number += 1

                    # Create the pairs - each player will play against the player before and after it in the list
                    pairs = [(next_round_players[i], next_round_players[i + 1]) for i in
                             range(len(next_round_players) - 1)]
                    pairs.append( (next_round_players[0], next_round_players[-1]) )
                    pairs_str = "\t".join(
                        self._get_player_name(pair[0]) + "-" + self._get_player_name(pair[1]) for pair in pairs
                    )
                    round_pairs.append(pairs_str)

                    print(f"Round {round_number}\n{pairs_str}")

                    next_round_players = []
                    # Run the current round battles
                    for player1, player2 in pairs:
                        battle_result = self.run_battle(map_str, player1=player1, player2=player2)
                        self.battle_results.append(battle_result)

                        # The winner goes to the next round
                        if battle_result.winner == 1:
                            next_round_players.append(player1)
                        elif battle_result.winner == 2:
                            next_round_players.append(player2)
                        elif battle_result.winner == 0:
                            next_round_players.extend([player1, player2])

                    round_winners.append("\t".join(self._get_player_name(player) for player in next_round_players))
                    # Make sure next_round_players is unique while preserving the order
                    next_round_players = [
                        next_round_players[i] for i in range(len(next_round_players))
                        if next_round_players[i] not in next_round_players[i+1:]
                    ]

                    if len(next_round_players) == 1:
                        print(f"Winner is {self._get_player_name(next_round_players[0])}")
                        break

                print("\n\n\n\nTournament Summary: \n\n")
                for pairs, winners in zip(round_pairs, round_winners):
                    print(pairs, "\n", winners)

        return self.battle_results

    @staticmethod
    def _get_player_name(player: Player) -> str:
        """
        :param player: player object
        :return: The player name if the NAME is the default name uses the class name.
        """
        return player.NAME if player.NAME != Player.NAME else player.__class__.__name__

    def get_player_scores(self) -> List[PlayerScore]:
        """
        :return: List of all players scores
        """
        player_scores = [self.get_player_score_object(self._get_player_name(player)) for player in self.players]
        player_scores.sort(key=lambda ps: ps.points, reverse=True)
        for rank, player_score in enumerate(player_scores):
            player_score.rank = rank + 1
        return player_scores

    def get_player_scores_data_frame(self) -> pd.DataFrame:
        """
        :return: Data frame with all the player scores details
        """
        return list_to_data_frame(
            lst=self.get_player_scores(),
            columns=list(PlayerScore.__dataclass_fields__.keys())
        )

    def get_player_score_object(self, player_name) -> PlayerScore:
        """
        :param player_name: The name of the player to create the PlayerScore object for.
        :return: A player score object for the given player, see PlayerScore doc.
        """
        df = self.get_extended_battle_results_data_frame_for_player(player_name=player_name)
        return PlayerScore(
            player_name=player_name,
            rank=None,
            battle_count=len(df),
            won=df['won'].sum(),
            lost=df['lost'].sum(),
            tie=df['tie'].sum(),
            points=df['won'].sum() + df['tie'].sum() * 0.5,
            total_score=df['player_score'].sum(),
            total_enemy_score=df['enemy_score'].sum(),
            mean_score=df['player_score'].mean(),
            mean_enemy_score=df['enemy_score'].mean(),
            killed_all_enemy_units=(df['enemy_score'] == 0).sum(),
            all_units_died=(df["player_score"] == 0).sum(),
            wins_as_player_1=((df["player_number"] == 1) & df["won"]).sum(),
            wins_as_player_2=((df["player_number"] == 2) & df["won"]).sum()
        )

    def get_extended_battle_results_data_frame_for_player(self, player_name) -> pd.DataFrame:
        """
        Get data frame with all the battles fought by the given player. Each battle is a row in the data frame.
        The df is from the player perspective player_score will be the score of the given player and enemy score is
        the score of the second player in the battle.
        The df columns are:
            'player_name', 'enemy_name',
            'won' (True if the player won), 'tie' (True if tie), 'lost' (True is the player lost),
            'player_score', 'enemy_score',
            'player_number' (1 is the player was player 1 in this battle or 2 is it was player 2),
            'finish_state', 'turns'

        :param player_name: The player to get the battle results for
        :return: Data frame with all the battles fought by the given player
        """
        assert len(self.battle_results) > 0, "first run the tournament"
        battle_results_df = self.get_battle_results_data_frame()
        df = battle_results_df[
            (battle_results_df["player_1_name"] == player_name) | (battle_results_df["player_2_name"] == player_name)
        ]
        df["player_name"] = player_name

        played_as_player_1 = df["player_1_name"] == player_name
        played_as_player_2 = df["player_2_name"] == player_name

        df.loc[played_as_player_1, "player_number"] = 1
        df.loc[played_as_player_2, "player_number"] = 2

        df.loc[played_as_player_1, "enemy_name"] = df.loc[played_as_player_1, "player_2_name"]
        df.loc[played_as_player_2, "enemy_name"] = df.loc[played_as_player_2, "player_1_name"]

        df.loc[played_as_player_1, "player_score"] = df.loc[played_as_player_1, "player_1_score"]
        df.loc[played_as_player_2, "player_score"] = df.loc[played_as_player_2, "player_2_score"]

        df.loc[played_as_player_1, "enemy_score"] = df.loc[played_as_player_1, "player_2_score"]
        df.loc[played_as_player_2, "enemy_score"] = df.loc[played_as_player_2, "player_1_score"]

        df["won"] = df["player_number"] == df["winner"]
        df["tie"] = df["winner"] == 0
        df["lost"] = (~df["won"] & ~df["tie"])

        return df[
            ['player_name', 'enemy_name', 'won', 'tie', 'lost', 'player_score', 'enemy_score',
             'player_number', 'finish_state', 'turns']
        ]

    def get_battle_results_data_frame(self) -> pd.DataFrame:
        """
        Get data frame with all the battles fought in the tournament.
        See BattleResult doc of explanation on the data frame columns.
        :return: data frame with all the battles fought in the tournament.
        """
        assert len(self.battle_results) > 0, "first run the tournament"
        return list_to_data_frame(
            lst=self.battle_results,
            columns=[
                "battle_id", "player_1_name", "player_2_name", "winner", "finish_state",
                "player_1_score", "player_2_score", "turns", "description_for_display"
            ]
        ).set_index("battle_id")

    def run_battle(self, map_str: str, player1: Player, player2: Player) -> BattleResult:
        """
        Run a battle in the given map between the given player 1 and player 2. Returns the battle results.
        :param map_str: The map to battle in
        :param player1: Player 1 bot
        :param player2: Player 2 bot
        :return: The BattleResult
        """
        print(f"run battle between {self._get_player_name(player1)} and {self._get_player_name(player2)}")
        game_manager = GameManager(map_str, player1, player2, self.raise_bot_exceptions)
        finish_state = game_manager.run_game()

        winner = None
        if finish_state == GameManager.PLAYER_1_WIN_STATE:
            winner = 1
        elif finish_state == GameManager.PLAYER_2_WIN_STATE:
            winner = 2
        elif finish_state == GameManager.TIE_STATE:
            winner = 0

        self.last_battle_id += 1
        return BattleResult(
            battle_id=self.last_battle_id,
            finish_state=finish_state,
            winner=winner,
            player_1_name=self._get_player_name(player1),
            player_2_name=self._get_player_name(player2),
            player_1_score=game_manager.get_player_score(player_num=1),
            player_2_score=game_manager.get_player_score(player_num=2),
            turns=game_manager.turns,
            description_for_display=game_manager.get_description_for_display(),
            end_game_object=game_manager.game
        )

    def view_battle(self, battle_id: int):
        """
        Open the java viewer to view in cool GUI the given battle.
        see view_battle_given_battle_description function doc
        :param battle_id: The id of the battle to view
        """
        battle = [b for b in self.battle_results if b.battle_id == battle_id][0]
        self.view_battle_given_battle_description(battle.description_for_display)

    @staticmethod
    def view_battle_given_battle_description(battle_description_for_display: str):
        """
        Open the java viewer to view in cool GUI the given battle.
        Note: The viewer can only open one battle at a time - so before viewing new battle close the window of the
        previous one.
        Requirements: Java should be installed on your device.

        :param battle_description_for_display: String representation of the battle for display
        """
        # in windows we need to save the battle to file because there is limit to the cmd command length of 8161 chars
        if os.name == "nt":
            battle_file_path = os.path.join(TMP_DIR_PATH, f"battle_{time.time()}.txt")
            with open(battle_file_path, "w") as f:
                f.write(battle_description_for_display)
            command = f'type {battle_file_path} | java -jar {SHOW_GAME_JAR_PATH}'
        else:
            command = f'echo "{battle_description_for_display}" | java -jar {SHOW_GAME_JAR_PATH}'
        # print(command)
        os.system(command)


class TestBot(Tournament):
    """
    Test the given bot against a list of other bots.
    Battle will run between the given bot and all other bots on all the given maps.
    The API is similar to Tournament - the main difference is here all the battle include the bot you want to test
    while in a tournament all the bots are battling all other bots.
    """

    def __init__(
            self,
            player: Player,
            competitors: List[Player],
            maps: List[str],
            always_be_player_1: bool = False,
            raise_bot_exceptions: bool = True
    ):
        """
        Battle will run between the given player and all other competitors on all the given maps
        :param player: The player to test
        :param competitors: The players it should battle
        :param maps: A list of maps to run the battles on.
        :param always_be_player_1: If True the given player will always be player 1 in all battle, if False
                                   will run 2 battle in each map against each bot - changing sides between the battles.
        :param raise_bot_exceptions: If False catch exceptions from the player bots
        """
        assert len(maps) >= 1, "tournament needs at least 1 map"
        self.player = player
        self.competitors = competitors
        self.always_be_player_1 = always_be_player_1
        super().__init__(competitors + [player], maps, raise_bot_exceptions)

    def run_tournament(self) -> List[BattleResult]:
        """
        Run the "test" - the given player will battle each competitor in each map.
        :return: The BattleResults
        """
        self.battle_results = []
        for map_str in self.maps:
            for competitor in self.competitors:
                self.battle_results.append(
                    self.run_battle(map_str, player1=self.player, player2=competitor)
                )
                if not self.always_be_player_1:
                    self.battle_results.append(
                        self.run_battle(map_str, player1=competitor, player2=self.player)
                    )
        return self.battle_results

    def get_testing_results_data_frame(self) -> pd.DataFrame:
        """
        :return: Data frame with all the battles fought by the player you test
        """
        return self.get_extended_battle_results_data_frame_for_player(player_name=self._get_player_name(self.player))

    def get_score_object(self) -> PlayerScore:
        """
        :return: The PlayerScore object of the player you test.
        Note: Rank doesn't means much here - the player
        """
        return self.get_player_score_object(player_name=self._get_player_name(self.player))

    def get_player_scores(self) -> List[PlayerScore]:
        """
        :return: The PlayerScore object of the player you test.
        Note: Rank doesn't means much here - the player you test played much more battles then other competitors
        and thous probably and unjustly will be the first rank.
        """
        print("Warning! PlayerScores of the competitors are not the same as in the tournament. "
              "Here all competitors play just vs the player you want to test. ")
        return super().get_player_scores()


def run_and_view_battle(player_1: Player, player_2: Player, map_str: str, ):
    """
    Run a battle between the given players in the given map and open the Java viewer to view it.

    Note: The viewer can only open one battle at a time - so before viewing new battle close the window of the
    previous one.
    Requirements: Java should be installed on your device.

    :param player_1: Player 1 bot
    :param player_2: Player 2 bot
    :param map_str: The map to run the battle on
    """
    battle_runner = TestBot(player_1, [player_2], [map_str], always_be_player_1=True)
    battle_runner.run_tournament()
    battle_runner.view_battle(battle_runner.last_battle_id)


def get_map_by_id(map_id: int) -> str:
    """
    Read the relevant map from the maps folder
    :param map_id: Make should map{map_id).txt exists in the map folder. legal values are 1 to 100
    :return: The text in map{map_id).txt file
    """
    with open(os.path.join(PLANET_WARS_MODULE_PATH, "maps", f"map{map_id}.txt")) as f:
        return f.read()
