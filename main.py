from utils import setup_logging
from lib.config import config
from lib.data import data
from pathlib import Path
from lib import nexus
import asyncio
import logging

log = logging.getLogger(__name__)
setup_logging(log, logging.DEBUG)

# log.debug(f"Database Address: {config['db']['address']}")
# log.debug("Connecting to database...")
# log.debug(f"Database Object: {data.base}")


def do_all_pending_files_exist(pending_mods):
    all_exist = True
    for mod in pending_mods:
        for modid, pending in mod.items():
            pending_file = pending['pending_file']
            if not pending_file:
                continue
            pending_path = Path(DOWNLOADS_PATH) / pending_file
            if not pending_path.exists():
                log.warning(f"Pending file for mod {modid} ({pending['name']}) does not exist: {pending_path}")
                all_exist = False
            # else:
            #     log.info(f"Pending file for mod {modid} exists: {pending_path}")
    return all_exist

# This is just my railroader mod-list. This is tempoarary for testing and will be moved to an example file later.
# A shame some cool mods got removed by the authors. Woulda loved to put them here but guess I gotta remove them from my save.
# tmp_mod_list = [
#     346, 94, 447, 651, 591, 42, 443, 689, 583, 132, 356, 569, 346, 315, 370, 494, 329, 464, 345, 628, 309, 239,
#     211, 364, 709, 714, 328, 238, 821, 59, 60, 342, '143#misc:1', '143#misc:2', '143#main:2', '143#main:3',
#     '491#misc:1', '491#misc:2', '491#misc:3', '491#misc:4', 253, 242, 794, 706, 265, 241, 387, 739, 317,
#     303, 806, 604, '410#main:2', 18, 816, 492, 503, 740, 752, 400, 614, 532, 545, 692, 434, 440, 421,
#     567, 52, 858, 823, 894, '1174#main:2', '1174#main:3', '1173#main:2', '1173#main:3', 1040, 1236, 1202
# ]
tmp_mod_list = [
    '1645$fuse!toolshed', '1645$toolshed', 239, '1378@latest$fuse;install'
]


# 444 was removed, sadge, write a thing to detect that i guess

for x in tmp_mod_list:
    data.base['mods'].upsert({
        'modid': f'railroader-{x}',
        'name': 'test'
    }, ['modid'])

    # nexus.parse_id_string(f'railroader-{x}')

# data.base['mods'].upsert({
#     'modid': 'railroader-1029',
#     'name': 'test',
#     'version': '0.1.0'
# }, ['modid'])

DOWNLOADS_PATH = str(Path.home() / "Downloads")
# nexus.build_railroader_modlist_from_gamefiles()
# nexus.check_for_mod_updates('railroader-1096@1.0')
async def refresh_nexus_data_and_install():
    # for x in tmp_mod_list:
    #     await nexus.fetch_nexus_file_info(f'railroader-{x}')

    # return
    check_func = nexus.check_for_updates_and_download_if_available
    mod_ids = sorted([mod['modid'] for mod in data.base['mods'].all()])
    # mod_ids = sorted([mod['modid'] + '@' + str(mod['version']) for mod in data.base['mods'].all()])

    log.debug(mod_ids)
    # for mod in mods:
    #     log.debug(mod)
        # await func(mod['modid'] + '@' + mod['version'])
    # log.debug(list(mods))
    # log.debug(data.base['mods'].all())
    # for mod in data.base['mods']:
    #     log.debug(f"Checking for updates for mod: {mod['modid']} (current version: {mod['version']})")
    # mod_ids = []
    # mod_ids = [
    #     'railroader-1029',
    #     'railroader-143',
    #     'railroader-410'
    # ]
    # return
    async with asyncio.TaskGroup() as tg:
        for id in mod_ids:
            tg.create_task(check_func(id))
    # log.debug(nexus.VCACHE)
    nexus.VCACHE = {}
    pending_mods = [{mod['modid']: {'name': mod['name'], 'pending_file': mod['pending_filename'],'pending_version': mod['pending_version'], 'old_filename': mod['current_filename']}} for mod in data.base['mods'].all() if mod['pending_filename'] is not None]

    while not do_all_pending_files_exist(pending_mods):
        log.info("These messages will display every 10 seconds until all pending update files are present in the Downloads folder.")
        await asyncio.sleep(10)
        
    log.info("All pending update files are present. Proceeding with installation...")
    # for mod in pending_mods:
    #     for modid, pending in mod.items():
    #         pending_file = pending['pending_file']
    #         pending_version = pending['pending_version']
    #         if not pending_file:
    #             log.info(f"No pending file for mod {modid} ({pending['name']}). Skipping installation.")
    #             continue
    #         pending_path = Path(DOWNLOADS_PATH) / pending_file
    #         if pending_path.exists():
    #             log.info(f"Installing update for mod {modid} ({pending['name']}) from file: {pending_path}")
    #             await nexus.install_nexus_file(modid + '@' + pending_version, str(pending_path))
    #         else:
    #             log.error(f"Pending file for mod {modid} ({pending['name']}) not found during installation: {pending_path}")

    # log.warning("Please run this program again after having downloaded the update files.")

    

if __name__ == "__main__":
    asyncio.run(refresh_nexus_data_and_install())
# asyncio.run(nexus.download_nexus_file('railroader-1096@1.0'))
# asyncio.run(nexus.check_for_updates_and_open_if_available('railroader-1096@1.0'))
# asyncio.run(nexus.open_page_for_nexus_file('railroader-1096@1.0'))
# asyncio.run(nexus.fetch_nexus_file_info('railroader-1096@1.0'))
# nexus.fetch_nexus_file_info('railroader-1029')
# nexus.fetch_nexus_file_info('railroader-143')
# nexus.fetch_nexus_file_info('railroader-410')
# nexus.fetch_nexus_file_info('railroader-1028')
# nexus.fetch_nexus_file_info('railroader-1027')
# nexus.fetch_nexus_file_info('railroader-1026')