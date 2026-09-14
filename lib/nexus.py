from collections import OrderedDict
from curses import meta
from dataclasses import dataclass
import subprocess
from utils import setup_logging
from lib.config import config
from lib.data import data
from pprint import pformat
from pathlib import Path
from lib import web
import logging
import asyncio
import random
import json5
import os
import re

log = logging.getLogger(__name__)
setup_logging(log, logging.DEBUG)
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
        # This will only work if you have Nexus premium, which I don't have, and have no intention of getting.
        # So, this code literally does nothing after it's executed, but it's here for future reference at the very least.
        # https://www.nexusmods.com/Core/Libs/Common/Widgets/ModRequirementsPopUp?id=3747&game_id=5982&nmm=1
        # =2rhpulWxfdP0CmL0QJkBUw&expires=1765333682
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
    # game_id = await API.get_numerical_game_id(game)
    # const downloadUrl = 'nxm://railroader/mods/410/files/3747?key=E8MbBu59eCkwNzhApS8yCA&expires=1765311054&user_id=124452793';
    # url = f"https://www.nexusmods.com/Core/Libs/Common/Widgets/ModRequirementsPopUp?id={file_id}&game_id={game_id}"
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

# Regex is hard.
RE_PATTERN = pattern = re.compile(
    r'^(?P<game>[^@#$!]+)-(?P<mod>[^-@#$!]+)'
    r'(?:@(?P<version>[^#$!]+))?'
    r'(?:#(?P<fileid>\d+))?'
    r'(?:\$(?P<search>[^!]+))?'
    r'(?:!(?P<exclude>.+))?$'
)
@dataclass
class ModMeta:
    game: str
    mod: str
    version: str = None
    fileid: str = None
    search: list = None
    exclude: list = None
        
def parse_id_string(id_string):
    meta = RE_PATTERN.match(id_string)
    meta_dict = meta.groupdict() if meta else {}
    meta_dict['search'] = meta_dict['search'].split(';') if meta_dict['search'] else []
    meta_dict['exclude'] = meta_dict['exclude'].split(';') if meta_dict['exclude'] else []
    return ModMeta(**meta_dict)
    # print(meta)
    log.debug(meta.groupdict())
    # # meta = re.split(r'[-@#$]', id_string)
    # game, mod = meta.pop(0), meta.pop(0)
    # # meta.pop(1)
    # version = meta
    # print(game, mod, version)
    # return game, mod, version

def compile_vstring(meta):
    vstring = meta
    # vstring = game + '-' + mod + '@' + f"{str(version) if version else 'latest'}"
    return vstring

async def refresh_nexus_data(kwargs):
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
    # log.debug('test')
    # log.debug(moddata)
    for version in moddata:
        # versions[version['version']] = version
        # log.debug(';<'.join([str(version['version']), str(version['file_id']), str(version['name'])]))
        versions[';;'.join([str(version['version']), str(version['file_id']), str(version['name'])])] = version
    # versions[None] = moddata[-1]
    # versions['latest'] = moddata[-1]
    return OrderedDict(reversed(list(versions.items())))

def formatted_version_string(version_string):
    matches = re.findall(r'\d+', version_string)
    return tuple(int(x) for x in matches) if matches else (0,)

def search_nexus_file_data(versions, meta):
    results = []

    log.debug(meta)

    # log.debug(f'--- Begin file dump for {meta.game}-{meta.mod} ---'.upper())
    # for x in versions.keys():
    #     log.debug(x)
    # log.debug(f'--- End file dump for {meta.game}-{meta.mod} ---'.upper())

    #  = []

    # order of filtration
    # filter by fileID if provided
    # filter by search terms if provided
    # filter out exluded terms if provided
    # filter by version if provided
    # if version is provided, return all files
    # if no version is provided, return latest file

    if meta.fileid:
        for key in versions.keys():
            v, f, n = key.split(';;')
            if f == meta.fileid:
                log.debug(f'fileid yes: {meta.fileid}')
                return [versions[key]]
        return []

    log.debug(len(versions))
    if meta.search:
        versions = {
            key: versions[key]
            for key in versions.keys()
            for search in meta.search
            if search.lower() in key.lower()
        }

    if meta.exclude:
        versions = {
            key: versions[key]
            for key in versions.keys()
            if not any(exclude.lower() in key.lower() for exclude in meta.exclude)
        }

    log.debug(len(versions))

    if meta.version:
        target_version = meta.version
        if meta.version == 'latest':
            paired = [(v.split(';;')[0], formatted_version_string(v.split(';;')[0])) for v in versions.keys()]
            target_version = max(paired, key=lambda pair: pair[1])[0]
            # target_version = max([formatted_version_string(v.split(';;')[0]) for v in versions.keys()])

        for key in versions.keys():
            v, f, n = key.split(';;')
            if v == target_version:
                results.append(versions[key])
                log.debug(f'version yes: {target_version}')
    else:
        for key in versions.keys():
            results.append(versions[key])
            log.debug('newest file yes')
            break
        return results
    return results

VCACHE = {}
async def fetch_nexus_file_info(id_string, return_all=False):
    meta = parse_id_string(id_string)
    log.debug(meta)
    vstring = id_string
    data = await API.get_mod_files(meta.game, meta.mod)
    if not data: 
        log.error(f"No data returned for {vstring}")
        return None
    # log.debug(data)
    if f"{meta.game}-{meta.mod}" in VCACHE:
        log.debug(f"Using VCACHE for {meta.game}-{meta.mod}")
    else:
        VCACHE[f"{meta.game}-{meta.mod}"] = format_nexus_file_data(data, meta)

    log.debug('Starting search...')
    result = search_nexus_file_data(VCACHE[f"{meta.game}-{meta.mod}"], meta)
    log.debug(f"Number of search results for {vstring}: {len(result)}")
    log.debug('Search concluded!')

    # log.debug(result)

    # if '#' in version:
    #     version = version.split('#')


    return None
    # vformatted = versions[meta.version]['name'] if meta.version in versions else 'Unknown Version'
    # log.debug(f"Fetched Nexus file info for {vstring}: {vformatted}")
    # if vformatted == 'Unknown Version':
    #     return versions['latest']
    # if return_all:
    #     return versions
    # return versions[version]

async def check_for_updates_and_download_if_available(id_string):
    meta = parse_id_string(id_string)
    file_info = await fetch_nexus_file_info(id_string)
    if not file_info:
        log.error(f"Failed to fetch file info for {meta.game}-{meta.mod}. Skipping update check.")
        return
    # log.debug(f"Download link data: {pformat(file_info)}")
    if file_info['version'] == meta.version:
        # log.debug(f"No update available for {meta.game}-{meta.mod} (current version: {meta.version})")
        return
    
    log.info(f"Update available for {meta.game}-{meta.mod}: {file_info['version']} (current version: {meta.version})")
    # await open_dl_link(meta.game, meta.mod)

    data.base['mods'].upsert({
        'modid': f'{meta.game}-{meta.mod}',
        'name': file_info['name'],
        # 'last_update': None,
        'pending_filename': file_info['file_name'],
        'pending_version': file_info['version']
    }, ['modid'])

    
    # log.debug(f"Download link data: {pformat(file_info)}")
    # await open_dl_link(meta.game, meta.mod)
    pass

# WARNING: This function is deprecated and should not be used.
def build_railroader_modlist_from_gamefiles():
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