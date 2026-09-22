from lib.nexus import parse_id_string
from utils import setup_logging
from lib.data import data
from pathlib import Path
import logging
import shutil

log = logging.getLogger(__name__)
setup_logging(log)


def import_modlist(path: Path):
    if not path.exists():
        log.error('Import file does not exist!')
        return
    mods = []
    match path.suffix:
        case '.rmm':
            log.debug('RMM plaintext detected!')
            with open(path, "rt") as f:
                for line in f.readlines():
                    if line.startswith('\n'): continue
                    if line.startswith('#'): continue
                    mods.append(line.rstrip().lstrip())
            pass
        case '.mpk':
            log.debug('MsgPack (mpk) detected!')
            pass
        case '.json':
            log.debug('JSON detected!')
            pass
        case _:
            log.debug(f'`{path.suffix}` is not a recognized file format!')
            return

    for mod in mods:
        meta = parse_id_string(mod)
        rmmid = mod.replace(f'|{meta.patch}', '') if meta.patch else mod
        log.debug(rmmid)

        data.base['mods'].upsert({
            'modid': rmmid,
            'patch': meta.patch
        }, ['modid'])


def export_modlist(format: str, path: Path):
    raise NotImplementedError