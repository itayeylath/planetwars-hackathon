import os

import pandas as pd

from planet_wars import PLANET_WARS_MODULE_PATH
from planet_wars.battles.tournament import Tournament


def get_battle_results_df(round_id: int):
    """
    Get the round battle results data frame
    :param round_id: The id of the round 1/2/3
    :return: The battle_results_df
    """
    return pd.read_parquet(
        os.path.join(PLANET_WARS_MODULE_PATH, "rounds", f"round{round_id}", "battle_results_df.parquet")
    )


def get_player_results_df(round_id: int):
    """
    Get the round battle results data frame
    :param round_id: The id of the round 1/2/3
    :return: The battle_results_df
    """
    return pd.read_parquet(
        os.path.join(PLANET_WARS_MODULE_PATH, "rounds", f"round{round_id}", "player_scores_df.parquet")
    )


def print_df(df: pd.DataFrame):
    """
    Print the given data frame
    :param df: data frame to print
    """
    # for a nicer df printing
    pd.set_option('display.max_columns', 30)
    pd.set_option('display.max_row', None)
    pd.set_option('expand_frame_repr', False)
    print(df)


def view_battle(battle_results_df: pd.DataFrame, battle_id: int):
    """
    View the battle with the given battle id
    :param battle_results_df: The data frame with details on all the battle
    :param battle_id: The id of the battle to view
    """
    battle_description = battle_results_df.loc[battle_id]['description_for_display']
    Tournament.view_battle_given_battle_description(battle_description)


if __name__ == '__main__':
    print_df(get_battle_results_df(1))
    print("\n\n")
    # print_df(get_player_results_df(2))

    br = get_battle_results_df(1)
    view_battle(br, 7)  # 27 & 44
