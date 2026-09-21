from zipfile import ZipFile, is_zipfile
from bad_path import is_dangerous_path
from utils import setup_logging
from lib.config import config
from lib.data import data
from pathlib import Path
from lib import nexus
import aiofiles.os
import aiofiles
import msgpack
import asyncio
import logging
import base64
import shutil
import json5
import json
import os

log = logging.getLogger(__name__)
setup_logging(log)

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
    check_func = nexus.check_for_updates_and_download_if_available
    mod_ids = sorted([mod['modid'] for mod in data.base['mods'].all()])

    log.debug(mod_ids)

    log.info('Searching for updates...')
    try:
        async with asyncio.TaskGroup() as tg:
            for id in mod_ids:
                tg.create_task(check_func(id))
    except Exception as e:
        log.exception(e)

    nexus.VCACHE = {}

    pending_files = [file for mod in data.base['mods'].all() for file in json.loads(mod['pending_filenames'] if mod['pending_filenames'] else '[]')]

    if not pending_files:
        log.info('All mods are up to date!')
        return

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

    if not is_dangerous_path(TMP_FOLDER):
        shutil.rmtree(TMP_FOLDER)

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
    meta.patch = moddat['patch']
    if is_dangerous_path(config['gameloc'][meta.game]):
        log.error(f'`{config['gameloc'][meta.game]}` has been flagged as a dangerous path. Aborting install.')
        return
    moddat['names'] = json.loads(moddat['names'] if moddat['names'] else ['N/A'])
    # moddat['folders'] = json.loads(moddat['folders']) if moddat['folders'] else []
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
        if not glob:
            log.error(f'Glob was empty!!! {pending_file}. Cannot continue install!!!')
            continue
        if meta.patch:
            patch = msgpack.unpackb(base64.b64decode(meta.patch))
        else:
            patch = None
        for file in glob:
            folder = file.parents[0].name
            true_id = folder
            if file.name.lower() == 'info.json':
                with file.open("r+", encoding="utf-8-sig") as f:
                    modinfo = json5.load(f)  # need to use json5 cuz some mods have misplaced commas
                    if modinfo:
                        folder = modinfo['Id']
                        true_id = folder
                    if meta.patch and modinfo and 'replaceId' in patch:
                        # patch = msgpack.unpackb(base64.b64decode(meta.patch))
                        if modinfo['Id'] in patch['replaceId']:
                            modinfo['Id'] = patch['replaceId'][modinfo['Id']]
                            f.seek(0)
                            json.dump(modinfo, f, indent=4)
                            f.truncate()
                            log.debug(f'`{true_id}` has been patched to `{modinfo['Id']}`')
                        folder = modinfo['Id']

            elif file.name.lower() == 'definition.json' and meta.patch and 'removeRLConflict' in patch:
                with file.open("r+", encoding="utf-8-sig") as f:
                    modinfo = json5.load(f)
                    if 'conflictsWith' in modinfo:
                        popqueue = []
                        for item in modinfo['conflictsWith']:
                            if item['id'] in patch['removeRLConflict']:
                                popqueue.append(item)
                        for item in popqueue:
                            modinfo['conflictsWith'].remove(item)
                        f.seek(0)
                        json.dump(modinfo, f, indent=4)
                        f.truncate()
                        log.debug(f'`{file.name}` has been patched for mod `{folder}`.')
                    else:
                        log.warning(f'Failed to patch `{file.name}` for `{folder}`: No conflicts defined by mod!')

            log.debug(f'Folder name has been determined to be {folder}.')

            path = Path(config['gameloc'][meta.game], folder)
            if await aiofiles.os.path.exists(path):
                log.debug(f"Clearing old `{folder}` install.")
                await asyncio.to_thread(shutil.rmtree, path)
            elif moddat['version'] is not None:  # not sure how to handle this rn 
                if folder != true_id and await aiofiles.os.path.exists(true_id_path := Path(config['gameloc'][meta.game], true_id)):
                    log.warning(f"Folder `{folder}` didn't exist, but {true_id} was found. Deleting potential conflict.")
                    await asyncio.to_thread(shutil.rmtree, true_id_path)
                else:
                    log.warning(f"Folder `{folder}` doesn't exist and couldn't be cleared. This might mean that the mod identifier changed! Please manually verify. Continuing with install.")

            await asyncio.to_thread(shutil.copytree, file.parents[0], path)
            log.debug(f"Installed `{folder}`.")

    log.info(f'Installed {len(moddat['pending_filenames'])} file(s) for {moddat['modid']}')
    data.base['mods'].upsert({
        'modid': moddat['modid'],
        # 'names': json.dumps(aggregate['names']),
        'version': moddat['pending_version'],
        'fileids': moddat['pending_fileids'],
        'pending_filenames': None,
        'pending_fileids': None,
        'pending_version': None
    }, ['modid'])
    # eepy, what needs to happen
    # - update database (right here)
    # - add support for the different import/export types (lib/modpack.py)
    # - 


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