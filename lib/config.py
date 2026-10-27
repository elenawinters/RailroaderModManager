from lib.system import determine_mods_folder_location
from utils import setup_logging
import configparser
import platform
import logging
import sys
import os

log = logging.getLogger(__name__)
setup_logging(log)

# Setup config
config = configparser.ConfigParser()
config_file = 'config.ini'
if not os.path.exists(config_file):
    config['settings'] = {
        'offsite_open': True,
        'offsite_last_open': "2026-06-09T00:0:00.000000",
        'offsite_frequency': 7,
        'delete_tmp': True
    }
    config['db'] = { 'address': 'sqlite:///rmm.sqlite' }

    log.warning("For the `gameloc` variable in the `config.ini`, you will need to find the mod folder locations for your game version and OS.")
    log.warning(f'"{platform.system()}" has been determined to be your OS.')
    log.warning(f'For pre-MoW, use "{determine_mods_folder_location(pre_mow=True)}"')
    log.warning(f'For post-MoW, use "{determine_mods_folder_location()}"')
    log.warning('Please verify that locations are correct before running his software.')

    config['gameloc'] = { 'railroader': determine_mods_folder_location() }
    config['nexus'] = { 'apikey': 'your_nexusmods_api_key_here' }
    with open(config_file, 'w') as configfile:
        config.write(configfile)

    log.warning('Please edit the `config.ini` file before continuing! You will need to verify your `gameloc` and set your Nexus Mods API key!')
    sys.exit(0)
else:
    config.read(config_file)

