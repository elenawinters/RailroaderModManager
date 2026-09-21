from zipfile import ZipFile, is_zipfile
from bad_path import is_dangerous_path
from utils import setup_logging
from lib.config import config
from lib.data import data
from pathlib import Path
from lib import nexus
import aiofiles.os
import aiofiles
import asyncio
import logging
import shutil
import json5
import json
import os

log = logging.getLogger(__name__)
setup_logging(log, logging.DEBUG)

# log.debug(f"Database Address: {config['db']['address']}")
# log.debug("Connecting to database...")
# log.debug(f"Database Object: {data.base}")


async def do_all_pending_files_exist(pending_files):
    all_exist = True
    for pending_file in pending_files:
        if not pending_file:
            continue
        pending_path = Path(DOWNLOADS_PATH, pending_file)
        if not await aiofiles.os.path.exists(pending_path):
            log.warning(f"Pending file {pending_path} does not exist.")
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
# tmp_mod_list = [
#     '1645$fuse!toolshed', '1645$toolshed', 239, '1378@latest$fuse;install'
# ]


# # 444 was removed, sadge, write a thing to detect that i guess

# for x in tmp_mod_list:
#     data.base['mods'].upsert({
#         'modid': f'railroader-{x}',
#         'names': json.dumps(['test'])
#     }, ['modid'])

    # nexus.parse_id_string(f'railroader-{x}')

# data.base['mods'].upsert({
#     'modid': 'railroader-1029',
#     'name': 'test',
#     'version': '0.1.0'
# }, ['modid'])

TMP_FOLDER = Path(Path.cwd(), 'tmp')
DOWNLOADS_PATH = Path(Path.home(), "Downloads")
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
    # pending_files = []
    # for mod in data.base['mods'].all():
    #     for file in json.loads(mod['pending_filenames']):
    #         pending_files.append(file)

    pending_files = [file for mod in data.base['mods'].all() for file in json.loads(mod['pending_filenames'])]

    #     if mod['pending_filenames'] is None: continue
    #     name = json.loads(mod['names'])
    #     folders = json.loads(mod['folders']) if mod['folders'] else None
    #     pending_filenames = json.loads(mod['pending_filenames'])
    #     for index in range(len(pending_filenames)):
    #         pending_mods.append({mod['modid']: {
    #             'name': name[index] if mod['names'] else None,
    #             'pending_file': pending_filenames[index] if mod['pending_filenames'] else None,
    #             'pending_version': mod['pending_version'],
    #             'old_installs': folders
    #         }})


    # pending_mods = [{mod['modid']: {'name': mod['names'], 'pending_file': mod['pending_filenames'],'pending_version': mod['pending_version'], 'old_filename': mod['folders']}} for mod in data.base['mods'].all() if mod['pending_filenames'] is not None]

    while not await do_all_pending_files_exist(pending_files):
        # log.info("These messages will display every 10 seconds until all pending update files are present in the Downloads folder.")
        log.info("Please download the missing files above to continue.")
        input("Press any key to initiate installation (if all files are present)...")
        # await asyncio.sleep(10)

    if not TMP_FOLDER.exists(): os.mkdir(TMP_FOLDER)

    log.info("All pending update files are present. Proceeding with installation...")
    try:
        async with asyncio.TaskGroup() as tg:
            for mod in data.base['mods'].all():
                if mod['pending_filenames'] is None: continue
                tg.create_task(install_mods(mod))
    except Exception as e:
        log.exception(e)

    # if not is_dangerous_path(TMP_FOLDER):
    #     shutil.rmtree(TMP_FOLDER)

def unpack_to_tmp(archive: Path):
    loc = Path(TMP_FOLDER, archive.name)
    if loc.exists():
        log.debug(f'Directory `{archive.name}` already exists in the temp folder!')
        return
    with ZipFile(archive, 'r') as obj:
        obj.extractall(path=loc)

    log.debug(f'`{archive.name}` extracted to temp folder.')
    
async def install_mods(moddat):
    meta = nexus.parse_id_string(moddat['modid'])
    if is_dangerous_path(config['gameloc'][meta.game]):
        log.error(f'`{config['gameloc'][meta.game]}` has been flagged as a dangerous path. Aborting install.')
        return
    moddat['names'] = json.loads(moddat['names'] if moddat['names'] else ['N/A'])
    moddat['folders'] = json.loads(moddat['folders']) if moddat['folders'] else []
    moddat['pending_filenames'] = json.loads(moddat['pending_filenames']) if moddat['pending_filenames'] else []

    ## decided not to use this code. it wipes every entry in moddat folders, but we might only be updating one of them
    # # cleanup old install
    # for folder in moddat['folders']:
    #     loc = Path(config['gameloc'][meta.game], folder)
    #     if is_dangerous_path(loc):  # probably unneccessary. Only way this would happen is if the database corrupted I think.
    #         log.error(f'`{loc}` has been flagged as a dangerous path. Aborting install.')
    #         return
    #     if not await aiofiles.os.path.isdir(loc): continue
    #     await asyncio.to_thread(shutil.rmtree, loc)
    #     log.debug(f"Deleted {loc} because an update is available! ({moddat['modid']})")

    # unpack and install new files
    for pending_file in moddat['pending_filenames']:
        loc = Path(DOWNLOADS_PATH, pending_file)
        if not await aiofiles.os.path.isfile(loc): continue
        if not await asyncio.to_thread(is_zipfile, loc): continue

        await asyncio.to_thread(unpack_to_tmp, loc)

        tmp = Path(TMP_FOLDER, pending_file)
        glob = list(tmp.rglob('Info.json', case_sensitive=False)) + list(tmp.rglob('Definition.json', case_sensitive=False))
        if not glob: log.error(f'Glob was empty!!! {pending_file}')
        for file in glob:
            folder = file.parents[0].name
            if file.name.lower() == 'info.json':
                with file.open("r", encoding="utf-8-sig") as f:
                    modinfo = json5.load(f)  # need to use json5 cuz some mods have misplaced commas
                    if modinfo:
                        folder = modinfo['Id']
            log.debug(f'Folder name has been determined to be {folder}.')

            # path = file.parents[0]
            path = Path(config['gameloc'][meta.game], folder)
            if await aiofiles.os.path.exists(path):
                log.debug(f"Clearing old `{folder}` install.")
                await asyncio.to_thread(shutil.rmtree, path)
            elif moddat['version'] is None:  # not sure how to hand this rn 
                log.warning(f"Folder `{folder}` doesn't exist and couldn't be cleared. This might mean that the mod identifier changed! Please manually verify. Continuing with install.")

            await asyncio.to_thread(shutil.copytree, file.parents[0], path)
            log.debug(f"Installed `{folder}`.")

            # log.debug(file)
            # break
        # done = False
        # while not done:

        

        
        



        # async with aiofiles.open(Path(await aiofiles.os.getcwd(), 'tmp')) as afp:
        #     pass




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