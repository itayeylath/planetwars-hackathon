import os

PLANET_WARS_MODULE_PATH = os.path.dirname(__file__)

# If you are in windows and have space in the dir name you can copy ShowGame.jar to place without space in the path and
# change this constant
SHOW_GAME_JAR_PATH = os.path.join(PLANET_WARS_MODULE_PATH, "viewer", "ShowGame.jar")
# If you are in windows and have space in the dir name you can change this constant to a tmp path without space
TMP_DIR_PATH = os.path.join(PLANET_WARS_MODULE_PATH, "tmp")
