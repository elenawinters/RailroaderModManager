from lib.system import DATE_FORMAT, TMP_FOLDER, DOWNLOADS_PATH, does_zipfile_exist
from lib.config import config, config_file
from datetime import datetime, timedelta
from zipfile import ZipFile, is_zipfile
from bad_path import is_dangerous_path
from utils import setup_logging
from lib.data import data
from pathlib import Path
from lib import modlist
from lib import tests
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

        if not await does_zipfile_exist(pending_path):
            all_exist = False
            continue
    return all_exist

def handle_args():
    if '--import' in sys.argv:
        index = sys.argv.index('--import')
        if len(sys.argv) > index + 1:
            modlist.import_modlist(Path(sys.argv[index + 1]))
        else:
            log.error('Import path not provided!')
        return True

    if '--export' in sys.argv:
        index = sys.argv.index('--export')
        if len(sys.argv) > index + 2:
            modlist.export_modlist(sys.argv[index + 1], Path(sys.argv[index + 2]))
            return True
        else:
            log.error('Export path or format not provided!')
        return True

    if '--convert' in sys.argv:
        index = sys.argv.index('--convert')
        if len(sys.argv) > index + 2:
            modlist.convert_modlist(Path(sys.argv[index + 1]), sys.argv[index + 2])
            return True
        else:
            log.error('Convert path or format not provided!')
        return True

    if '--generate' in sys.argv:
        index = sys.argv.index('--generate')
        if len(sys.argv) > index + 1:
            tests.generate_rmm_modpack_from_gamefiles(Path(sys.argv[index + 1]))
            return True
        else:
            log.error('Generate path not provided!')
        return True


async def refresh_nexus_data_and_install():
    if handle_args():
        return

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

    if config['settings'].getboolean('offsite_open') == True:
        if datetime.now() - timedelta(days=config['settings'].getint('offsite_frequency')) > datetime.strptime(config['settings']['offsite_last_open'], DATE_FORMAT):
             config['settings']['offsite_last_open'] = datetime.now().strftime(DATE_FORMAT)

    with open(config_file, 'w') as configfile:
        config.write(configfile)

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
                if 'offsite' in mod['modid']: continue
                tg.create_task(install_mods(mod))
    except Exception as e:
        log.exception(e)

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

async def install_mods(moddat):
    meta = nexus.parse_id_string(moddat['modid'])
    meta.patch = moddat['patch']
    if is_dangerous_path(config['gameloc'][meta.game]):
        log.error(f'`{config['gameloc'][meta.game]}` has been flagged as a dangerous path. Aborting install.')
        return
    moddat['pending_filenames'] = json.loads(moddat['pending_filenames']) if moddat['pending_filenames'] else []

    # unpack and install new files
    folders = []
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
                        if modinfo['Id'] in patch['replaceId']:
                            modinfo['Id'] = patch['replaceId'][modinfo['Id']]
                            f.seek(0)
                            json.dump(modinfo, f, indent=4)
                            f.truncate()
                            log.info(f'`{true_id}` has been patched to `{modinfo['Id']}` ({moddat['modid']}).')
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
                        log.info(f'`{file.name}` has been patched for mod `{folder}` ({moddat['modid']}).')
                    else:
                        log.warning(f'Failed to patch `{file.name}` for `{folder}`: No conflicts defined by mod!')

            log.debug(f'Folder name has been determined to be {folder}.')
            folders.append(folder)

            path = Path(config['gameloc'][meta.game], folder)
            if await aiofiles.os.path.exists(path):
                log.debug(f"Clearing old `{folder}` install.")
                await asyncio.to_thread(shutil.rmtree, path)
            elif moddat['version'] is not None:  # this could probably be better
                if folder != true_id and await aiofiles.os.path.exists(true_id_path := Path(config['gameloc'][meta.game], true_id)):
                    log.warning(f"Folder `{folder}` didn't exist, but `{true_id}` was found. Deleting potential conflict.")
                    await asyncio.to_thread(shutil.rmtree, true_id_path)
                else:
                    log.warning(f"Folder `{folder}` doesn't exist and couldn't be cleared. This might mean that the mod identifier changed! Please manually verify. Continuing with install. ({moddat['modid']})")

            await asyncio.to_thread(shutil.copytree, file.parents[0], path)
            log.debug(f"Installed `{folder}`.")

    log.info(f'Installed {len(moddat['pending_filenames'])} file(s) for {moddat['modid']}')
    data.base['mods'].upsert({
        'modid': moddat['modid'],
        'version': moddat['pending_version'],
        'fileids': moddat['pending_fileids'],
        'folders': json.dumps(folders),
        'pending_filenames': None,
        'pending_fileids': None,
        'pending_version': None
    }, ['modid'])


if __name__ == "__main__":
    asyncio.run(refresh_nexus_data_and_install())
