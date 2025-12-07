from utils import setup_logging
from lib.config import config
from lib.data import data
from pprint import pformat
from pathlib import Path
from lib import web
import logging
import asyncio
import json5
import os
import re

log = logging.getLogger(__name__)
setup_logging(log, logging.DEBUG)

async def refresh_nexus_data(kwargs):
    pass
    # async with asyncio.TaskGroup() as tg:
    #     for func in _listeners:
    #         tg.create_task(func(**kwargs))

def format_nexus_file_data(moddata):
    if 'files' in moddata:
        moddata = moddata['files']
    versions = {}
    for version in moddata:
        versions[version['version']] = version
        versions[version['file_id']] = version
        # print(version['version'])
    versions[None] = moddata[-1]  # Default to latest version if no version specified
    versions['latest'] = moddata[-1]
    # log.debug(pformat(versions))
    # versions = { moddata[x]['version']: moddata[x] for x in range(len(moddata)) }
    # log.debug(pformat(versions))
    return versions

# Info types are UMM
# Definition types are Railloader
async def check_for_mod_updates(id):
    meta = re.split(r'[-@#]', id)
    game, mod, version = meta[0], meta[1], meta[2] if len(meta) > 2 else None
    # log.debug(meta)
    log.debug(game + ' ' + mod + ' ' + str(version))
    _id = id.split('-')
    test = await web.Client(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod}/files.json", headers={
        "accept": "application/json",
        "apikey": config['nexus']['apikey']
    }).async_get()
    # log.debug(f"Nexus Mod Info for {id}:\n{pformat(test.json())}")
    versions = format_nexus_file_data(test.json())
    log.debug(versions.keys())
    log.debug(pformat(versions[version]))
    # log.debug('\n' + pformat(out['files'][-1]))
    # log.debug(out['files'][-1]['name'] + ': ' + out['files'][-1]['version'])
    # for x in out['files'][-1]:
    #     log.debug(pformat(x))
    # https://api.nexusmods.com/v1/games/railroader/mods/1029/files.json
    pass

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