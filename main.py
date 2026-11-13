# from lib.install import install_mods, total_installs, pending_installs, detailed_mod_info, check_mod
from lib import install
from lib.system import (
    DATE_FORMAT, TMP_FOLDER,
    DOWNLOADS_PATH, CACHE_PATH,
    does_zipfile_exist, dict_upsert
)
from lib.config import config, config_file
from datetime import datetime, timedelta
from zipfile import ZipFile, is_zipfile
from bad_path import is_dangerous_path
from lib.patchlib import patcher
from lib.args import handle_args
from utils import setup_logging
from lib.provider import nexus
from lib.data import data
from pathlib import Path
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
    check_func = install.check_mod
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

    # dumping the VCACHE is mostly a debug thing.
    with open("vcache.json", "w", encoding="utf-8-sig") as f:
        json.dump(nexus.VCACHE, f, indent=4)

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
    if config['settings'].getboolean('delete_tmp') == True and not is_dangerous_path(TMP_FOLDER):
        shutil.rmtree(TMP_FOLDER)

    log.info("All pending update files are present. Proceeding with installation...")

    install.global_patch = data.base['mods'].find_one(modid = 'global-patch').get('patch', None)
    log.critical(install.global_patch)

    try:
        async with asyncio.TaskGroup() as tg:
            for mod in data.base['mods'].all():
                if mod['modid'] is None: continue
                if mod['pending_filenames'] is None: continue
                if 'offsite' in mod['modid']: continue
                if 'patch' in mod['modid']: continue
                tg.create_task(install.install_mods(mod))
    except Exception as e:
        log.exception(e)

    log.info(f'Successfully installed {install.total_installs}/{install.pending_installs} mod(s).')

    if config['settings'].getboolean('delete_tmp') == True and not is_dangerous_path(TMP_FOLDER):
        shutil.rmtree(TMP_FOLDER)

    if not install.detailed_mod_info:
        return
    
    pref = Path(Path(config['gameloc']['railroader']).parent, 'Preferences.json')
    if not pref.exists():
        return

    with pref.open("r+", encoding="utf-8-sig") as f:
        prefdat = json5.load(f)
        prefmods = prefdat['mods']

        for identifier in install.detailed_mod_info.keys():
            dict_upsert(prefmods, { f'identifier': identifier, **install.detailed_mod_info[identifier]})
            # log.debug(identifier)

        prefdat['mods'] = prefmods
        prefdat['settings']['mods.allow-dll'] = 1

        f.seek(0)
        json.dump(prefdat, f, indent=2)
        f.truncate()

    log.info('Enabled all mods in game and enabled unsafe DLL loading.')


if __name__ == "__main__":
    if handle_args():
        sys.exit(0)

    asyncio.run(refresh_nexus_data_and_install())
