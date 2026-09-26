from bad_path import is_dangerous_path
from utils import setup_logging
from pathlib import Path
import logging
import json5
import time

log = logging.getLogger(__name__)
setup_logging(log)

def generate_rmm_modpack_from_gamefiles(path: Path):
    if is_dangerous_path(path):
        log.error('Path is dangerous! Aborting!')
        return
    if not path.is_dir():
        log.error('Path is not a directory!')
        return
    log.warning('-' * 60)
    for _ in range(5):
        log.warning("This function is meant for modpack makers only!!!".upper())
        log.warning("This function ```CANNOT``` generate a full modpack.".upper())
        log.warning("Please review everything this generates.".upper())
        log.warning('-' * 60)

    log.critical('Turns out, not many mods provide a proper link to their modpage.')
    log.critical("This function likely won't be finished after this revelation.")
    log.warning('-' * 60)

    time.sleep(2)

    for file in path.rglob('Info.json', case_sensitive=False):
        with file.open("r+", encoding="utf-8-sig") as f:
            modinfo = json5.load(f)
            if not modinfo: continue
            if 'HomePage' not in modinfo: continue

            log.info(modinfo['HomePage'])







# WARNING: This function is deprecated and should not be used.
def build_railroader_modlist_from_gamefiles():
    raise NotImplementedError("This function is deprecated. It is very old and doesn't work the way it was supposed to.")
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