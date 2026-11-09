from dataclasses import dataclass
# from utils import setup_logging
# import logging
import re

# log = logging.getLogger(__name__)
# setup_logging(log)

DELIMITER = ';;'
# Regex is hard.
RE_PATTERN = pattern = re.compile(
    r'^(?P<game>[^@%#$!|]+)-(?P<mod>[^-@%#$!|]+)'
    r'(?:@(?P<version>[^#$!|]+?))?'
    r'(?:%(?P<author>[^+#$!]+)\+(?P<repo>[^#$!]+))?'  # nexus RMMs don't use this, but github RMMs do.
    r'(?:#(?P<fileid>[^$!|]+))?'
    r'(?:\$(?P<search>[^!|]+))?'
    r'(?:!(?P<exclude>[^|]+))?'
    r'(?:\|(?P<patch>.+))?$'
)


@dataclass
class ModMeta:
    game: str
    mod: str
    version: str = None
    author: str = None
    repo: str = None
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
