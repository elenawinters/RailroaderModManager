from dataclasses import make_dataclass
from utils import setup_logging
from pathlib import Path
from lib import modlist
from lib import tests
import logging
import inspect
import sys
import re

log = logging.getLogger(__name__)
setup_logging(log)

def proc_arg(arg, fields = None):
    if arg not in sys.argv: return False
    if not fields: return True
    argindex = sys.argv.index(arg)
    if len(sys.argv) <= argindex + len(fields):
        log.error(f'Arguments missing for `{arg}`: {{ {', '.join(fields[len(sys.argv) - argindex - 1:])} }}')
        sys.exit(0)  # maybe don't continue execution 

    args = {field: sys.argv[argindex + index + 1] for index, field in enumerate(fields)}

    # yay, dataclass shenanigans!!!
    return make_dataclass(arg, [tuple([k, v]) for k, v in args.items()])(**args)

PATTERN = re.compile(r"if\s+args\s*:=\s*proc_arg\(\s*['\"](?P<command>[^'\"]+)['\"](?:\s*,\s*(?P<args>\[.*?\]))?\s*\)\s*:")
def handle_args():
    if args := proc_arg('--convert', ['path', 'desiredformat']):
        return modlist.convert_modlist(Path(args.path), args.desiredformat)

    if args := proc_arg('--import', ['path']):
        return modlist.import_modlist(Path(args.path))

    if args := proc_arg('--export', ['packformat', 'path']):
        return modlist.export_modlist(args.packformat, Path(args.path))
    
    if args := proc_arg('--remove', ['rmm_id']):
        return modlist.remove_mod(args.rmm_id)

    if args := proc_arg('--add', ['rmm_id']):
        return modlist.add_mod(args.rmm_id)

    if args := proc_arg('--help'):
        for com in PATTERN.findall(inspect.getsource(handle_args)):
            log.info(f"Command: {com[0]}")
            log.info(f"   Args: {com[1] if com[1] else 'None'}")
            if com[0] != '--help':
                log.info("")
        return True

