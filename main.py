from utils import setup_logging
from lib.config import config
from lib.data import data
from lib import nexus
import asyncio
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
async def refresh_nexus_data():
    func = nexus.check_for_mod_updates
    mod_ids = [
        'railroader-1029',
        'railroader-143',
        'railroader-410'
    ]
    async with asyncio.TaskGroup() as tg:
        for id in mod_ids:
            tg.create_task(func(id))

asyncio.run(refresh_nexus_data())
# nexus.check_for_mod_updates('railroader-1029')
# nexus.check_for_mod_updates('railroader-143')
# nexus.check_for_mod_updates('railroader-410')
# nexus.check_for_mod_updates('railroader-1028')
# nexus.check_for_mod_updates('railroader-1027')
# nexus.check_for_mod_updates('railroader-1026')