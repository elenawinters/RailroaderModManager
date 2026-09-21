from collections import OrderedDict
from curses import meta
from dataclasses import dataclass
import subprocess
from main import DOWNLOADS_PATH
from utils import setup_logging
from lib.config import config
from lib.data import data
from pprint import pformat
from pathlib import Path
from lib import web
import logging
import asyncio
import random
import json
import sys
import os
import re

log = logging.getLogger(__name__)
setup_logging(log)
class API:
    @staticmethod
    async def get_mod_files(game, mod_id):
        url = f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files.json"
        headers = {
            "accept": "application/json",
            "apikey": config['nexus']['apikey']
        }
        response = await web.Client(url, timeout=120, headers=headers).async_get()
        if response.status_code == 200:
            return response.json()
        else:
            log.error(f"Failed to fetch mod files: {response.status_code} - {response.text}")
            return {}
        
    @staticmethod
    async def get_numerical_game_id(game):
        url = f"https://api.nexusmods.com/v1/games/{game}.json"
        headers = {
            "accept": "application/json",
            "apikey": config['nexus']['apikey']
        }
        response = await web.Client(url, headers=headers).async_get()
        if response.status_code == 200:
            return response.json()['id']
        else:
            log.error(f"Failed to fetch numerical gameId: {response.status_code} - {response.text}")
            return {}
        
    @staticmethod
    async def get_download_link(game, mod_id, file_id):
        return NotImplementedError("This function is not implemented yet. It would require Nexus premium access to work.")
        # This can only work if you have Nexus premium, which I don't have, and have no intention of getting.
        # I'm not gonna further develop it. PR if you want to make it work.
        nxm = {
            'key': 'asdasdasdasd',
            'expires': 1234567890
        }
        url = f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files/{file_id}/download_link.json?key={nxm['key']}&expires={nxm['expires']}"
        # url = f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files/{file_id}/download_link.json"
        headers = {
            "accept": "application/json",
            "apikey": config['nexus']['apikey']
        }
        response = await web.Client(url, headers=headers).async_get()
        if response.status_code == 200:
            return response.json()
        else:
            log.error(f"Failed to fetch download link: {response.status_code} - {response.text}")
            return {}


async def open_dl_link(game, mod_id, file_id=None):
    if file_id is None:
        url = f"https://www.nexusmods.com/{game}/mods/{mod_id}?tab=files"
    else:
        url = f"https://www.nexusmods.com/{game}/mods/{mod_id}?tab=files&file_id={file_id}"
    # log.info(f"Opening download page for {game}-{mod_id} in web browser...")
    # The webbrowser module opens the OS native browser, which in my case is FireDragon.
    # However, I use Zen on my Arch system, and I want the download page to open in the browser so that I am logged in.
    # From what I can tell, this is a common problem with webbrowser not respecting the default browser set in the OS.
    # So, I will provide OS specific commands to open the URL in the default browser.
    # I will only test this on Linux. Please PR if broken on other OSes.
    if os.name == 'nt':  # Windows
        os.startfile(url)
    elif os.name == 'mac':  # macOS
        subprocess.run(['open', url])
    else:  # Linux and other OSes
        subprocess.run(['xdg-open', url])

DELIMITER = ';;'
# Regex is hard.
RE_PATTERN = pattern = re.compile(
    r'^(?P<game>[^@#$!]+)-(?P<mod>[^-@#$!]+)'
    r'(?:@(?P<version>[^#$!]+))?'
    r'(?:#(?P<fileid>\d+))?'
    r'(?:\$(?P<search>[^!]+))?'
    r'(?:!(?P<exclude>.+))?$'
    r'(?:\|(?P<patch>[A-Za-z0-9+/=]+))?$'
)

@dataclass
class ModMeta:
    game: str
    mod: str
    version: str = None
    fileid: str = None
    search: list = None
    exclude: list = None
    patch: str = None
        
def parse_id_string(id_string):
    meta = RE_PATTERN.match(id_string)
    meta_dict = meta.groupdict() if meta else {}
    meta_dict['search'] = meta_dict['search'].split(';') if meta_dict['search'] else []
    meta_dict['exclude'] = meta_dict['exclude'].split(';') if meta_dict['exclude'] else []
    return ModMeta(**meta_dict)

async def refresh_nexus_data(kwargs):
    return NotImplementedError("This would require a UI for it to really be useful. Dunno if one will ever be made")
    pass
    # async with asyncio.TaskGroup() as tg:
    #     for func in _listeners:
    #         tg.create_task(func(**kwargs))

# todo: make this better bwo
def format_nexus_file_data(moddata, meta):
    if 'files' in moddata:
        moddata = moddata['files']
    else:
        log.warning(f"No 'files' key in moddata for {meta.game}-{meta.mod}. Using raw moddata.")
    versions = {}
    for version in moddata:
        versions[DELIMITER.join([str(version['version']), str(version['file_id']), str(version['name'])])] = version
    return OrderedDict(reversed(list(versions.items())))

def formatted_version_string(version_string):
    matches = re.findall(r'\d+', version_string)
    return tuple(int(x) for x in matches) if matches else (0,)

def search_nexus_file_data(versions, meta):
    results = []

    log.debug(meta)
    if meta.fileid:
        for key in versions.keys():
            f = key.split(DELIMITER)[1]
            if f == meta.fileid:
                log.debug(f'fileid returned: {meta.fileid}')
                return [versions[key]]
        return []

    log.debug(f'{len(versions)} (all versions)')
    if meta.search:
        versions = {
            key: versions[key]
            for key in versions.keys()
            if all(search.lower() in key.lower() for search in meta.search)
        }

    if meta.exclude:
        versions = {
            key: versions[key]
            for key in versions.keys()
            if not any(exclude.lower() in key.lower() for exclude in meta.exclude)
        }

    log.debug(f'{len(versions)} (reduced by search/exclude)')
    if meta.version:
        target_version = meta.version
        if meta.version == 'latest':
            paired = [(v.split(DELIMITER)[0], formatted_version_string(v.split(DELIMITER)[0])) for v in versions.keys()]
            target_version = max(paired, key=lambda pair: pair[1])[0]

        for key in versions.keys():
            v = key.split(DELIMITER)[0]
            if v == target_version:
                results.append(versions[key])
                log.debug(f'version returned: {target_version}')
    else:
        for key in versions.keys():
            results.append(versions[key])
            log.debug('newest file returned')
            break
        return results
    return results

VCACHE = {}
async def fetch_nexus_file_info(id_string):
    meta = parse_id_string(id_string)
    # log.debug(meta)
    data = await API.get_mod_files(meta.game, meta.mod)
    if not data: 
        log.error(f"No data returned for {id_string}")
        return None
    # log.debug(data)
    if f"{meta.game}-{meta.mod}" in VCACHE:
        log.debug(f"Using VCACHE for {meta.game}-{meta.mod}")
    else:
        VCACHE[f"{meta.game}-{meta.mod}"] = format_nexus_file_data(data, meta)

    log.debug('Starting search...')
    result = search_nexus_file_data(VCACHE[f"{meta.game}-{meta.mod}"], meta)
    log.debug(f"Number of search results for {id_string}: {len(result)}")
    log.debug('Search concluded!')

    return result


async def check_for_updates_and_download_if_available(id_string):
    meta = parse_id_string(id_string)
    file_info = await fetch_nexus_file_info(id_string)
    if not file_info:
        log.error(f"Failed to fetch file info for {id_string}. Skipping update check.")
        return
    # log.debug(f"Download link data: {pformat(file_info)}")
    aggregate = {
        'names': [],
        'pending_fileids': [],
        'pending_files': []
    }

    moddat = data.base['mods'].find_one(modid=id_string)
    current_version = None
    if moddat:
        current_version = moddat['version']
    # log.debug(current_version)

    for file in file_info:
        if file['version'] == current_version and '--force' not in sys.argv:
            log.debug(f"No update available for {meta.game}-{meta.mod} (current version: {current_version})")
            return
        aggregate['names'].append(file['name'])
        aggregate['pending_files'].append(file['file_name'])
        aggregate['pending_fileids'].append(file['file_id'])
        log.info(f"Update available for {id_string}: {file['version']} (current version: {current_version})")
        pending_path = Path(DOWNLOADS_PATH) / file['file_name']
        if not pending_path.exists():
            await open_dl_link(meta.game, meta.mod, file['file_id'])

    data.base['mods'].upsert({
        'modid': id_string,
        'names': json.dumps(aggregate['names']),
        # 'last_update': None,
        'pending_filenames': json.dumps(aggregate['pending_files']),
        'pending_fileids': json.dumps(aggregate['pending_fileids']),
        'pending_version': file['version']
    }, ['modid'])

    pass

# WARNING: This function is deprecated and should not be used.
def build_railroader_modlist_from_gamefiles():
    import json5
    directory = Path(config['gameloc']['railroader'])
    mods = []
    for file in directory.iterdir():
        if not file.is_dir(): continue
        meta = []
        info_path = None
        # modloader = None
        for x in ("info.json", "Definition.json"):
            info_path = file / x
            if info_path.is_file():
                try:
                    with info_path.open("r", encoding="utf-8-sig") as f:
                        meta = json5.load(f)  # of course normal json doesn't work all the time cuz some mods have misplaced commas etc
                except Exception as e:
                    log.warning(f"Failed to read/parse '{file.name}/{info_path.name}': {e}")
                    continue
                break
        match info_path.name:
            case "info.json":
                modloader = "UMM"  # Unity Mod Manager
            case "Definition.json":
                modloader = "RL"   # Railloader
            case _:
                modloader = None
        if not meta:
            if file.name == 'Railloader': continue
            log.warning(f"No info.json or Definition.json in '{file.name}'")
            continue
        if not isinstance(meta, dict):
            log.warning(f"Unexpected metadata type in '{file.name}': {type(meta).__name__}")
            continue
        log.debug(f"Found {modloader} mod: {file.name}")
        mods.append({"path": str(file), "type": modloader, "meta": meta})
    log.debug(f"Found {len(mods)} valid mod directories")
    return mods