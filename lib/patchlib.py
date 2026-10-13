from utils import setup_logging
from lib.system import rm_key
from pathlib import Path
import logging
import json5
import json

log = logging.getLogger(__name__)
setup_logging(log)

def patcher(file, moddat, patch, payload, path): 
    if not patch: return
    for key in patch.keys():
        match key:
            case 'removeRLConflict' | 'rmRLCnflct':
                if file.name.lower() != 'definition.json':
                    log.warning(f'Patch `{key}` is only applicable to `definition.json` files. Skipping patch for `{file.name}` ({moddat["modid"]}).')
                    continue
                with file.open("r+", encoding="utf-8-sig") as f:
                    modinfo = json5.load(f)
                    if 'conflictsWith' not in modinfo:
                        log.warning(f'Failed to patch `{file.name}` for `{path.name}`: No conflicts defined by mod!')
                        continue

                    modinfo['conflictsWith'] = [item for item in modinfo['conflictsWith'] if item['id'] not in patch[key]]

                    f.seek(0)
                    json.dump(modinfo, f, indent=4)
                    f.truncate()
                    log.info(f'`{file.name}` has been patched for mod `{path.name}` ({moddat['modid']}).')

            case 'customFile' | 'cFile':
                if payload is None:
                    log.warning(f'Patch `{key}` requires a payload. Skipping patch for `{file.name}` ({moddat["modid"]}).')
                    continue
                cfile = Path(file.parent, patch[key])
                if cfile.exists():
                    log.warning(f'Custom file `{patch[key]}` already exists for `{path.name}` ({moddat["modid"]}). Skipping patch.')
                    continue
                cfile.touch()
                with cfile.open("w", encoding="utf-8-sig") as f:
                    f.write(payload)
                log.info(f'Custom file `{patch[key]}` has been created for `{path.name}` ({moddat['modid']}).')

            case 'rmKeyIn':
                if payload is None:
                    log.warning(f'Patch `{key}` requires a payload. Skipping patch for `{file.name}` ({moddat["modid"]}).')
                    continue
                cfile = Path(file.parent, patch[key])
                with cfile.open("r+", encoding="utf-8-sig") as f:
                    cdat = rm_key(json5.load(f), payload)
                    f.seek(0)
                    json.dump(cdat, f, indent=4)
                    f.truncate()
                    log.info(f'Key `{payload}` has been removed from `{patch[key]}` for `{path.name}` ({moddat['modid']}).')

            case 'bkp' | 'bpk' | 'backup':  # bpk is cuz i kept typoing it when updating patches in my modpack and i dont wanna double check them all
                # This patch movess over files from the previous version of the mod to the new version. 
                # For me, I only need this for "Dynamic Weather", as the per-save profiles are stored in the mod folder.
                # works with files and folders. not sure if it works with nested folders/files, but will update this if it doesn't
                flist = patch[key] if isinstance(patch[key], list) else [patch[key]]
                for bkp in flist:
                    tmp = Path(file.parent, bkp)
                    if tmp.exists():
                        log.warning(f'Aborting backup patch for `{bkp}` in `{path.name}` ({moddat["modid"]}): File already exists.')
                        continue
                    curr = Path(path, bkp)
                    if not curr.exists():
                        log.warning(f'Backup file `{bkp}` does not exist for `{path.name}` ({moddat["modid"]}). Skipping backup.')
                        continue
                    curr.move(tmp)


