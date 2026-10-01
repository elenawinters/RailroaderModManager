from lib.system import does_zipfile_exist
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass
from utils import setup_logging
from lib.config import config
from pprint import pformat
from lib.data import data
from pathlib import Path
from lib import system
from lib import web
import logging
import json
import sys
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
    async def get_mod_data(game, mod_id):
        url = f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}.json"
        headers = {
            "accept": "application/json",
            "apikey": config['nexus']['apikey']
        }
        response = await web.Client(url, timeout=120, headers=headers).async_get()
        if response.status_code == 200:
            return response.json()
        else:
            log.error(f"Failed to fetch mod data: {response.status_code} - {response.text}")
            return {}

    @staticmethod
    async def get_mod_name(game, mod_id):
        data = await API.get_mod_data(game, mod_id)
        if data:
            return data['name']
        return
        
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
        raise NotImplementedError("This function is not implemented yet. It would require Nexus premium access to work.")
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
    system.open_url(url)


DELIMITER = ';;'
# Regex is hard.
RE_PATTERN = pattern = re.compile(
    r'^(?P<game>[^@#$!|]+)-(?P<mod>[^-@#$!|]+)'
    r'(?:@(?P<version>[^#$!|]+))?'
    r'(?:#(?P<fileid>\d+))?'
    r'(?:\$(?P<search>[^!|]+))?'
    r'(?:!(?P<exclude>[^|]+))?'
    r'(?:\|(?P<patch>.+))?$'
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
    raise NotImplementedError("This would require a UI for it to really be useful. Dunno if one will ever be made")
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
    if meta.game == 'offsite':
        if config['settings'].getboolean('offsite_open') == True:
            if datetime.now() - timedelta(days=config['settings'].getint('offsite_frequency')) > datetime.strptime(config['settings']['offsite_last_open'], system.DATE_FORMAT):
                log.info(f'Offsite mod detected. Opening link to allow the user to check if it needs to be updated. ({meta.version})')
                system.open_url(meta.version)
        return 'offsite'
    
    data = await API.get_mod_files(meta.game, meta.mod)
    if not data: 
        log.error(f"No data returned for {id_string}")
        return None
    
    if f"{meta.game}-{meta.mod}" in VCACHE:
        log.debug(f"Using VCACHE for {meta.game}-{meta.mod}")
    else:
        VCACHE[f"{meta.game}-{meta.mod}"] = format_nexus_file_data(data, meta)

    log.debug('Starting search...')
    result = search_nexus_file_data(VCACHE[f"{meta.game}-{meta.mod}"], meta)
    log.debug(f"Number of search results for {id_string}: {len(result)}")
    log.debug('Search concluded!')

    return result

# Yep, sometimes this happens. Dunno how to get around it so patches are hardcoded for now
# Could potentially rely on the end of file identifier, but I don't know how to easily get that rn
# TODO: Make this not hardcoded. Might require a rewrite
brokenDLFilenamePatches = {
    'Duel Whistle 1581 1.0.0 2026-07-19T02-08Z muYqJIOHI.zip': 'Duel Whistle 1581 1 2026-07-19T02-08Z muYqJIOHI.zip'
}
async def check_for_updates_and_download_if_available(id_string):
    meta = parse_id_string(id_string)
    file_info = await fetch_nexus_file_info(id_string)
    if not file_info:
        log.error(f"Failed to fetch file info for {id_string}. Skipping update check.")
        return
    if file_info == 'offsite':
        return

    aggregate = {
        'pending_fileids': [],
        'pending_files': []
    }

    moddat = data.base['mods'].find_one(modid=id_string)
    current_version = None
    if moddat:
        current_version = moddat['version']

    for file in file_info:
        if file['version'] == current_version and '--force' not in sys.argv:
            log.debug(f"No update available for {id_string} (current version: {current_version})")
            return

        if file['file_name'] in brokenDLFilenamePatches:
            file['file_name'] = brokenDLFilenamePatches[file['file_name']]

        aggregate['pending_files'].append(file['file_name'])
        aggregate['pending_fileids'].append(file['file_id'])
        log.info(f"Update available for {id_string}: {file['version']} (current version: {current_version}) ({file['name']})")
        pending_path = Path(system.DOWNLOADS_PATH, file['file_name'])

        # Some mods, like Dual Whistle, list the wrong file name in their metadata
        # I'm not sure if this is a Nexus mods issue or a mod maker issue
        # if 'duel whistle' in pending_path.name.lower():
        #     log.debug(pending_path.name)
        #     log.debug(file['file_name'])
        #     log.debug('Duel Whistle 1581 1 2026-07-19T02-08Z muYqJIOHI.zip')
        #     log.debug(file['file_name'] == pending_path.name)
        #     log.debug(pending_path.name == 'Duel Whistle 1581 1 2026-07-19T02-08Z muYqJIOHI.zip')
        #     log.debug(pending_path.exists())
        #     log.debug(file)
        #     sys.exit(0)
        if not await does_zipfile_exist(pending_path, True, False):
            await open_dl_link(meta.game, meta.mod, file['file_id'])

    data.base['mods'].upsert({
        'modid': id_string,
        'name': await API.get_mod_name(meta.game, meta.mod),
        'pending_filenames': json.dumps(aggregate['pending_files']),
        'pending_fileids': json.dumps(aggregate['pending_fileids']),
        'pending_version': file['version']
    }, ['modid'])

    pass
