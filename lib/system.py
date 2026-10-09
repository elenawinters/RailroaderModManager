from utils import setup_logging
from zipfile import is_zipfile
from lib.data import data
from pathlib import Path
import subprocess
import datetime
import aiofiles
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



async def does_zipfile_exist(path, partial: bool = False, do_log: bool = True):
    if not await aiofiles.os.path.exists(path):
        if do_log: log.warning(f"Pending file `{path}` does not exist.")
        return False

    check_path = DOWNLOADS_PATH if path.parent == DOWNLOADS_PATH else CACHE_PATH
    glob = list(check_path.glob(f'{path.name.removesuffix('.zip')}*.zip.part'))
    if glob:  # glob to the rescue!!!
        if do_log: log.warning(f"Please wait for `{path}` to finish downloading.")
        if partial:
            return True
        else:
            return False

    if not is_zipfile(path):
        if do_log: log.error(f"`{path}` is not a valid zipfile!")
        return False

    return True


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

