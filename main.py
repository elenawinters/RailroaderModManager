from utils import setup_logging
from lib.config import config
from lib.data import data
from lib import nexus
import logging

log = logging.getLogger(__name__)
setup_logging(log, logging.DEBUG)

# log.debug(f"Database Address: {config['db']['address']}")
# log.debug("Connecting to database...")
# log.debug(f"Database Object: {data.base}")


data.base['mods'].upsert({
    'modid': 'railroader-1096',
    'name': 'test',
    'last_update': None,
    'version': '0.1.0'
}, ['modid'])

nexus.build_railroader_modlist_from_gamefiles()
# nexus.check_for_mod_updates('railroader-1096@1.0')
nexus.check_for_mod_updates('railroader-1029')
# nexus.check_for_mod_updates('railroader-1028')
# nexus.check_for_mod_updates('railroader-1027')
# nexus.check_for_mod_updates('railroader-1026')