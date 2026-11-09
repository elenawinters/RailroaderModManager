from zipfile import is_zipfile, ZipFile
from utils import setup_logging
from pathlib import Path
import subprocess
import datetime
import aiofiles
import platform
import logging
import sys
import os

log = logging.getLogger(__name__)
setup_logging(log)

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
TMP_FOLDER = Path(Path.cwd(), 'tmp')
CACHE_PATH = Path(Path.cwd(), 'cache')
DOWNLOADS_PATH = Path(Path.home(), "Downloads")

def open_url(url):
    # The webbrowser module opens the OS native browser, which in my case is FireDragon.
    # However, I use Zen on my Arch system, and I want the download page to open in the browser so that I am logged in on.
    # From what I can tell, this is a common problem with webbrowser not respecting the default browser set in the OS.
    # So, I will provide OS specific commands to open the URL in the default browser.
    # I will only test this on Linux. Please PR if broken on other OSes.
    if os.name == 'nt':  # Windows
        os.startfile(url)
    elif os.name == 'mac':  # macOS
        subprocess.run(['open', url])
    else:  # Linux and other OSes
        subprocess.run(['xdg-open', url])


# for the purposes of this, we're only gonna do this for post-MoW locations
def determine_mods_folder_location(pre_mow=False):
    user = os.getlogin()
    log.debug(f'Determind that we should use `{user}` for the mod folder destination. This may not be accurate and should be verified.')
    if platform.system() == 'Windows':  # Microslop Wimdows
        return 'C:/Program Files (x86)/Steam/steamapps/common/Railroader/Mods/' if pre_mow else f"C:/users/{user}/Documents/Railroader/Mods/"
    elif platform.system() == 'Linux':  # I use Arch btw
        return f"/home/{user}/.local/share/Steam/steamapps/common/Railroader/Mods/" if pre_mow else f"/home/{user}/.local/share/Steam/steamapps/compatdata/1683150/pfx/drive_c/users/steamuser/Documents/Railroader/Mods/"
    else:
        return "/path/to/railroader/mods/"


async def does_zipfile_exist(path, partial: bool = False, do_log: bool = True):
    # DO GLOB FOR FINDING FILE

    # if not await aiofiles.os.path.exists(path):
    file = list(path.parent.glob(path.name))
    if not file:
        if do_log: log.warning(f"Pending file `{path.name}` could not be found.")
        return False

    check_path = DOWNLOADS_PATH if path.parent == DOWNLOADS_PATH else CACHE_PATH
    glob = list(check_path.glob(f'{path.name}.part'))
    if glob:  # glob to the rescue!!!
        if do_log: log.warning(f"Please wait for `{path.name}` to finish downloading.")
        if partial:
            return True
        else:
            return False

    if not is_zipfile(file[0]):
        if do_log: log.error(f"`{path.name}` is not a valid zipfile!")
        return False

    return file[0]

def dict_upsert(items, new_item, key="identifier"):
    existing = next((i for i in items if i[key] == new_item[key]), None)
    if existing:
        existing.update(new_item)
    else:
        items.append(new_item)

def rm_key(data, target):
    if isinstance(data, dict):
        return {
            k: rm_key(v, target)
            for k, v in data.items()
            if k != target
        }
    if isinstance(data, list):
        return [rm_key(item, target) for item in data]
    return data

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

