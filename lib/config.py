import configparser
import system
import os

# Setup config
config = configparser.ConfigParser(
    converters={
        'datetime': system.parse_iso_datetime
    }
)
config_file = 'config.ini'
if not os.path.exists(config_file):
    config['settings'] = {
        'offsite_open': True,
        'offsite_last_open': 0,
        'offsite_frequency_days': 7
    }
    config['db'] = { 'address': 'sqlite:///rmm.sqlite'}
    config['gameloc'] = { 'railroader': '/path/to/railroader/mods' }
    config['nexus'] = { 'apikey': 'your_nexusmods_api_key_here' }
    with open(config_file, 'w') as configfile:
        config.write(configfile)
else:
    config.read(config_file)

