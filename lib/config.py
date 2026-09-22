import configparser
import os

# Setup config
config = configparser.ConfigParser()
config_file = 'config.ini'
if not os.path.exists(config_file):
    config['settings'] = {
        'offsite_open': True,
        'offsite_last_open': "2026-06-09T00:0:00.000000",
        'offsite_frequency': 7
    }
    config['db'] = { 'address': 'sqlite:///rmm.sqlite'}
    config['gameloc'] = { 'railroader': '/path/to/railroader/mods' }
    config['nexus'] = { 'apikey': 'your_nexusmods_api_key_here' }
    with open(config_file, 'w') as configfile:
        config.write(configfile)
else:
    config.read(config_file)

