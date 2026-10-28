from lib.system import (
    DATE_FORMAT, TMP_FOLDER,
    DOWNLOADS_PATH, CACHE_PATH,
    does_zipfile_exist
)
from lib.config import config, config_file
from datetime import datetime, timedelta
from zipfile import ZipFile, is_zipfile
from bad_path import is_dangerous_path
from lib.patchlib import patcher
from lib.args import handle_args
from utils import setup_logging
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
import uuid
import sys
import os

log = logging.getLogger(__name__)
setup_logging(log)

async def do_all_pending_files_exist(pending_files):
    all_exist = True
    for pending_file in pending_files:
        if not pending_file:
            continue
        pending_path = Path(DOWNLOADS_PATH, pending_file)
        pending_cache_path = Path(CACHE_PATH, pending_file)

        if not await does_zipfile_exist(pending_path, False, False) and \
           not await does_zipfile_exist(pending_cache_path):
            all_exist = False
            continue
    return all_exist

async def refresh_nexus_data_and_install():
    check_func = nexus.check_for_updates_and_download_if_available
    mod_ids = sorted([mod['modid'] for mod in data.base['mods'].all() if mod['modid'] is not None])

    log.debug(mod_ids)

    log.info('Searching for updates...')
    try:
        async with asyncio.TaskGroup() as tg:
            for id in mod_ids:
                # if id is None: continue
                tg.create_task(check_func(id))
    except Exception as e:
        log.exception(e)

    nexus.VCACHE = {}

    if config['settings'].getboolean('offsite_open') == True:
        if datetime.now() - timedelta(days=config['settings'].getint('offsite_frequency')) > datetime.strptime(config['settings']['offsite_last_open'], DATE_FORMAT):
             config['settings']['offsite_last_open'] = datetime.now().strftime(DATE_FORMAT)

        with open(config_file, 'w') as configfile:
            config.write(configfile)

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
    if not CACHE_PATH.exists(): os.mkdir(CACHE_PATH)

    log.info("All pending update files are present. Proceeding with installation...")
    try:
        async with asyncio.TaskGroup() as tg:
            for mod in data.base['mods'].all():
                if mod['modid'] is None: continue
                if mod['pending_filenames'] is None: continue
                if 'offsite' in mod['modid']: continue
                tg.create_task(install_mods(mod))
    except Exception as e:
        log.exception(e)

    log.info(f'Successfully installed {total_installs}/{pending_installs} mod(s).')

    if config['settings'].getboolean('delete_tmp') == True and not is_dangerous_path(TMP_FOLDER):
        shutil.rmtree(TMP_FOLDER)

def unpack_to_tmp(archive: Path):
    loc = Path(TMP_FOLDER, archive.name)
    if loc.exists():
        log.debug(f'Directory `{archive.name}` already exists in the temp folder!')
        return
    with ZipFile(archive, 'r') as obj:
        obj.extractall(path=loc)

    log.debug(f'`{archive.name}` extracted to temp folder.')

    # Some mods, like TheTies and InterchangedIndustryUnloader have their archives structured weirdly
    # So, uh... this corrects it! Or, at least tries to.
    for orig in loc.glob('*'):
        if orig.is_dir(): return  # Safe to abort if we find a directory
        if '\\' not in str(orig): return
        final = Path(loc, *str(orig).split('\\'))
        final.parent.mkdir(parents=True, exist_ok=True)
        orig.move(final)

total_installs = 0
pending_installs = 0
async def install_mods(moddat):
    meta = nexus.parse_id_string(moddat['modid'])
    meta.patch = moddat['patch']
    if is_dangerous_path(config['gameloc'][meta.game]):
        log.error(f'`{config['gameloc'][meta.game]}` has been flagged as a dangerous path. Aborting install.')
        return
    moddat['pending_filenames'] = json.loads(moddat['pending_filenames']) if moddat['pending_filenames'] else []

    global total_installs
    global pending_installs
    pending_installs += len(moddat['pending_filenames'])

    # unpack and install new files
    folders = []
    detailed_mod_info = {}
    for pending_file in moddat['pending_filenames']:
        loc = Path(CACHE_PATH, pending_file)
        if not await aiofiles.os.path.isfile(loc):
            dl = Path(DOWNLOADS_PATH, pending_file)
            if not await aiofiles.os.path.isfile(dl):
                log.critical(f'Pending file `{pending_file}` does not exist in Downloads or Cache. How did we get here?! Skipping file.')
                continue
            dl.move(loc)

        if not await asyncio.to_thread(is_zipfile, loc):
            log.debug(f'`{pending_file}` is not a valid zipfile. Skipping.')
            continue

        await asyncio.to_thread(unpack_to_tmp, loc)

        tmp = Path(TMP_FOLDER, pending_file)
        glob = list(tmp.rglob('Definition.json', case_sensitive=False)) + list(tmp.rglob('Info.json', case_sensitive=False))
        if not glob:
            log.error(f'Glob was empty!!! {pending_file}. Cannot continue install!!!')
            continue

        patch = None
        payload = None
        if meta.patch:
            if '?payload' in meta.patch:
                patch, payload = meta.patch.split('?payload', 1)
            else:
                patch = meta.patch
            patch = msgpack.unpackb(base64.b64decode(patch))
            payload = base64.b85decode(payload).decode() if payload else None

        # log.debug(f'Patch: {patch} | Payload: {payload} | File: {pending_file}')
        # log.debug(glob)
        for file in glob:
            if 'SCAssetPacks' in str(file):
                log.debug(f"Skipping {file} because it's part of an asset pack!")
                continue
            if file.name.lower() == 'info.json' and list(file.parent.glob('Definition.json', case_sensitive=False)):
                log.warning(f'Refusing to install `{file}` because it is probably already installed.')
                continue
            
            true_path = Path(config['gameloc'][meta.game], str(uuid.uuid1()))
            patcher(file, moddat, patch, payload, true_path)
            true_id = file.parents[0].name
            folder = true_id

            with file.open("r", encoding="utf-8-sig") as f:
                modinfo = json5.load(f)  # need to use json5 cuz some mods have misplaced commas
                masterkey = None
                for key in ('Id', 'id', 'identifier'):
                    if key not in modinfo: continue
                    masterkey = key
                if 'identifier' in modinfo:
                    detailed_mod_info[modinfo['identifier']] = {
                        'version': modinfo['version'],
                        'enabled': True,
                        'scope': 0
                    }
                modid = modinfo.get(masterkey, true_id)
                if modinfo:
                    folder = modid.replace('/', '  -  ')
                    
            log.debug(f'Folder name has been determined to be {folder}.')
            folders.append(folder)
            path = Path(config['gameloc'][meta.game], folder)

            if await aiofiles.os.path.exists(path):
                log.debug(f"Clearing old `{folder}` install.")
                await asyncio.to_thread(shutil.rmtree, path)
            elif moddat['version'] is not None:  # this could probably be better
                if folder != true_id and await aiofiles.os.path.exists(true_path):
                    log.warning(f"Folder `{folder}` didn't exist, but `{true_id}` was found. Deleting potential conflict.")
                    await asyncio.to_thread(shutil.rmtree, true_path)
                else:
                    log.warning(f"Folder `{folder}` doesn't exist and couldn't be cleared. This might mean that the mod identifier changed! Please manually verify. Continuing with install. ({moddat['modid']})")
            total_installs += 1

            await asyncio.to_thread(shutil.copytree, file.parents[0], path)
            log.debug(f"Installed `{folder}`.")

    log.debug(f'Installed {len(folders)}/{len(moddat['pending_filenames'])} file(s) for {moddat['modid']}')
    data.base['mods'].upsert({
        'modid': moddat['modid'],
        'version': moddat['pending_version'],
        'fileids': moddat['pending_fileids'],
        'folders': json.dumps(folders),
        'pending_filenames': None,
        'pending_fileids': None,
        'pending_version': None
    }, ['modid'])

    if not detailed_mod_info:
        return
    
    pref = Path(Path(config['gameloc'][meta.game]).parent, 'Preferences.json')
    if not pref.exists:
        return

    with pref.open("r+", encoding="utf-8-sig") as f:
        prefdat = json5.load(f)
        prefmods = prefdat['mods']

        for identifier in detailed_mod_info.keys():
            dict_upsert(prefmods, { f'identifier': identifier, **detailed_mod_info[identifier]})
            log.debug(identifier)

        prefdat['mods'] = prefmods
        prefdat['settings']['mods.allow-dll'] = 1

        f.seek(0)
        json.dump(prefdat, f, indent=2)
        f.truncate()

    log.info('Enabled all mods in game and enabled unsafe DLL loading.')


def dict_upsert(items, new_item, key="identifier"):
    existing = next((i for i in items if i[key] == new_item[key]), None)
    if existing:
        existing.update(new_item)
    else:
        items.append(new_item)

if __name__ == "__main__":
    if handle_args():
        sys.exit(0)

    asyncio.run(refresh_nexus_data_and_install())
