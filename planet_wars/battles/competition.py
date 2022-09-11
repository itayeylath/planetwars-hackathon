import warnings

import pandas as pd

from planet_wars.battles.tournament import Tournament
from planet_wars.player_bots.baseline_code.baseline_bot import AttackWeakestPlanetFromStrongestBot, \
    AttackEnemyWeakestPlanetFromStrongestBot, AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot

# Insert Your bot object here, as BotObject(). Don't forget to set BotObject.NAME to your team name
PLAYER_BOTS = [
    AttackWeakestPlanetFromStrongestBot(), AttackEnemyWeakestPlanetFromStrongestBot(),
    AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot(), AttackEnemyWeakestPlanetFromStrongestBot(),
    AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot()
]


ROUND1_MAP = "SECRET ;)"

if __name__ == '__main__':
    # Display options
    warnings.simplefilter(action='ignore')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('expand_frame_repr', False)

    tournament = Tournament(PLAYER_BOTS, [ROUND1_MAP], all_against_all=False)
    battle_results = tournament.run_tournament()
    # player_scores_df = tournament.get_player_scores_data_frame()
    battle_results_df = tournament.get_battle_results_data_frame()
    # print(player_scores_df)
    print(battle_results_df)

    # player_scores_df.to_parquet("./player_scores_df.parquet")
    battle_results_df.to_parquet("./battle_results_df.parquet")
    # player_scores_df.to_csv("./player_scores_df.csv")
    battle_results_df.to_csv("./battle_results_df.csv")
    # TODO commit the saved df so all players can see the battle results