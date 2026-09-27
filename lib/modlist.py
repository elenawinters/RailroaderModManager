from lib.system import DATE_FORMAT, does_zipfile_exist
from lib.config import config, config_file
from lib.nexus import parse_id_string
from utils import setup_logging
from datetime import datetime
from lib.data import data
from pathlib import Path
import msgpack
import logging
import shutil
import json5
import json
import sys
import os

log = logging.getLogger(__name__)
setup_logging(log)

BACKUP_FOLDER = Path(Path.cwd(), 'backups')

class ModpackImportError(Exception):
    pass
class ModpackExportError(Exception):
    pass

def dict_to_rmm(rmm_dict):
    return list(set([f'{game}-{mod}' for game in rmm_dict for mod in rmm_dict[game]]))

def import_modlist(path: Path, return_modlist: bool = False):
    if not path.exists():
        log.error(f'Import file `{path}` does not exist!')
        return

    mods = []
    match path.suffix.lower():
        case '.mpk' | '.mp' | '.msgpack':
            log.info(f'MsgPack ({path.suffix.lower()}) detected! Trying to parse.')
            with open(path, 'rb') as exportfile:
                mods = dict_to_rmm(msgpack.unpackb(exportfile.read()))
        case '.json' | '.json5':
            log.info('JSON detected! Trying to parse.')
            with open(path, 'r') as exportfile:
                mods = dict_to_rmm(json5.load(mods, exportfile))
        case '.rmmpack' | '.rmm' | '.txt':
            log.info('RMM plaintext detected! Trying to parse.')
            with open(path, "rt") as f:
                for line in f.readlines():
                    if line.startswith('\n') or line.startswith('\r') or line.startswith('#'): continue
                    if ' ' in line:  # comment support bullshit. if you don't have a space after the RMM-ID, that's on you
                        line = line.split(' ')[0]
                    mods.append(line.rstrip().lstrip())
        case _:
            raise ModpackImportError(f'`{path.suffix}` is not a recognized file import format!')

    if return_modlist:
        return mods

    if not BACKUP_FOLDER.exists():
        os.mkdir(BACKUP_FOLDER)
    log.info('Mods parsed! Backing up current install!')
    export_modlist('MSGPACK', Path(BACKUP_FOLDER, 'backup_' + datetime.now().strftime(DATE_FORMAT)))

    if '--append' not in sys.argv:
        log.info('Replacing installed modpack!')
        data.base['mods'].delete()
    else:
        log.info('Appending mods to current installation!')

    for mod in mods:
        meta = parse_id_string(mod)
        rmmid = mod.replace(f'|{meta.patch}', '') if meta.patch else mod

        data.base['mods'].upsert({
            'modid': rmmid,
            'patch': meta.patch
        }, ['modid'])

    if config['settings'].getboolean('offsite_open') == True:
        config['settings']['offsite_last_open'] = '2026-06-09T00:0:00.000000'
        with open(config_file, 'w') as configfile:
            config.write(configfile)

def rmm_to_dict(rmm_list):
    moddict = {}
    for mod in rmm_list:
        meta = parse_id_string(mod)
        if meta.game not in moddict:
            moddict[meta.game] = []
            
        shortened = mod.replace(meta.game + '-', '')
        if shortened.isdecimal():
            shortened = int(shortened)
        moddict[meta.game].append(shortened)
    return moddict

def export_modlist(packformat: str, path: Path, mods: list = None):
    modlist = []
    mod_name = {}
    if not mods:
        for moddat in data.base['mods'].all():
            fileids = json.loads(moddat['fileids']) if moddat['fileids'] else []
            meta = parse_id_string(moddat['modid'])
            meta.patch = moddat['patch']
            patch = ''
            if meta.patch: patch = '|' + meta.patch
            if fileids == [] or '--strict' not in sys.argv:
                modlist.append(f'{moddat['modid']}{patch}')
                if moddat['name'] is not None:
                    mod_name[f'{moddat['modid']}{patch}'] = moddat['name']
                continue
            for file in fileids:
                modlist.append(f'{meta.game}-{meta.mod}#{file}{patch}')
                if moddat['name'] is not None:
                    mod_name[f'{meta.game}-{meta.mod}#{file}{patch}'] = moddat['name']
    else:
        modlist = mods

    if modlist == []:
        log.error('Failed to export! Modlist is empty!')
        return

    log.info(f'Exporting modpack of {len(modlist)} mods as `{packformat.upper()}`{' strictly' if '--strict' in sys.argv else ''}!')
    match packformat.lower():
        case 'msgpack' | 'mpk' | '.mpk':
            mods = rmm_to_dict(modlist)
            mpk = msgpack.packb(mods)
            outfile = Path(path).with_suffix('.mpk')
            if outfile.exists(): raise ModpackExportError(f'File `{outfile}` already exists!')
            with open(outfile, 'wb') as exportfile:
                exportfile.write(mpk)
        case 'json' | '.json':
            mods = rmm_to_dict(modlist)
            outfile = Path(path).with_suffix('.json')
            if outfile.exists(): raise ModpackExportError(f'File `{outfile}` already exists!')
            with open(outfile, 'w') as exportfile:
                json.dump(mods, exportfile, indent=4)
            pass
        case 'plaintext' | 'rmm' | '.rmm' | 'rmmpack' | '.rmmpack':
            outfile = Path(path).with_suffix('.rmmpack')
            if outfile.exists(): raise ModpackExportError(f'File `{outfile}` already exists!')
            named_modlist = []
            for x in modlist:
                if x not in mod_name:
                    named_modlist.append(x)
                    continue
                log.debug(mod_name[x])
                named_modlist.append(x + '  # ' + mod_name[x])
            with open(outfile, 'w') as exportfile:
                exportfile.write('\n'.join(named_modlist))
            pass
        case _:
            raise ModpackExportError(f'`{packformat}` is not a recognized file export format!')


def convert_modlist(path: Path, desiredformat):
    log.info('Converting between pack formats!')
    mods = import_modlist(path, return_modlist=True)
    export_modlist(desiredformat, path, mods)
    log.info('Pack converted!')