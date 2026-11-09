from lib.rmmlib import DELIMITER, parse_id_string
from lib.system import does_zipfile_exist
from collections import OrderedDict
from utils import setup_logging
from lib.config import config
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

async def init(id_string):
    meta = parse_id_string(id_string)
    log.debug(f'Initializing GitHub mod installation for: {meta}')
    pass