import asyncio
import base64
import shutil
import uuid
from zipfile import is_zipfile

import aiofiles
from bad_path import is_dangerous_path
import json5
import msgpack

from lib.patchlib import patcher
from lib.system import CACHE_PATH, DOWNLOADS_PATH, TMP_FOLDER, does_zipfile_exist, unpack_to_tmp
from datetime import datetime, timedelta
from lib.rmmlib import parse_id_string
from utils import setup_logging
from lib.config import config
from lib.data import data
from pathlib import Path
from lib import system
import logging
import json
import sys

log = logging.getLogger(__name__)
setup_logging(log)




async def check_mod(id_string):
    meta = parse_id_string(id_string)
    match meta.mod:
        case 'github':
            from lib.provider.github import init
            await init(id_string)
            return
        case 'patch':
            pass
        case 'url' | 'offsite':
            if config['settings'].getboolean('offsite_open') == True:
                if datetime.now() - timedelta(days=config['settings'].getint('offsite_frequency')) > datetime.strptime(config['settings']['offsite_last_open'], system.DATE_FORMAT):
                    log.info(f'Offsite mod detected. Opening link to allow the user to check if it needs to be updated. ({meta.version})')
                    system.open_url(meta.version)
                return 'offsite'
        case _:
            from lib.provider.nexus import init
            await init(id_string)
            return

global_patch = None

total_installs = 0
pending_installs = 0
detailed_mod_info = {}
async def install_mods(moddat):
    meta = parse_id_string(moddat['modid'])
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
    global detailed_mod_info
    for pending_file in moddat['pending_filenames']:
        loc = next(CACHE_PATH.glob(pending_file), Path(CACHE_PATH, pending_file))
        # loc = Path(CACHE_PATH, pending_file)
        if not await aiofiles.os.path.isfile(loc):
            # dl = Path(DOWNLOADS_PATH, pending_file)
            dl = next(DOWNLOADS_PATH.glob(loc.name), Path(DOWNLOADS_PATH, pending_file))
            if not await aiofiles.os.path.isfile(dl):
                log.critical(f'Pending file `{pending_file}` does not exist in Downloads or Cache. How did we get here?! Skipping file.')
                continue
            dl.move(loc)

        if not await asyncio.to_thread(is_zipfile, loc):
            log.debug(f'`{pending_file}` is not a valid zipfile. Skipping.')
            continue

        await asyncio.to_thread(unpack_to_tmp, loc)

        tmp = Path(TMP_FOLDER, loc.name)
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

        local_patch = msgpack.unpackb(base64.b64decode(patch)) if patch else None
        payload = base64.b85decode(payload).decode() if payload else None

        patch = msgpack.unpackb(base64.b64decode(global_patch))
        if local_patch:
            patch.update(local_patch)


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
                        'scope': 1 if 'scope' in modinfo and modinfo['scope'] == 'optional' else 0
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
