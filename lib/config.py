import configparser
import os

# Setup config
config = configparser.ConfigParser()
config_file = 'config.ini'
if not os.path.exists(config_file):
    config['db'] = { 'address': 'sqlite:///nantahala.sqlite'}
    config['gameloc'] = { 'railroader': '/path/to/railroader/mods' }
    config['nexus'] = { 'apikey': 'your_nexusmods_api_key_here' }
    with open(config_file, 'w') as configfile:
        config.write(configfile)
else:
    config.read(config_file)

