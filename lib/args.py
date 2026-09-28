from dataclasses import make_dataclass
from utils import setup_logging
from pathlib import Path
from lib import modlist
from lib import tests
import logging
import sys

log = logging.getLogger(__name__)
setup_logging(log)

def proc_arg(arg, fields):
    if arg not in sys.argv: return False
    argindex = sys.argv.index(arg)
    if len(sys.argv) <= argindex + len(fields):
        log.error(f'Arguments missing for `{arg}`: {{ {', '.join(fields[len(sys.argv) - argindex - 1:])} }}')
        sys.exit(0)  # maybe don't continue execution 

    args = {}  # could prob dict comprehend this but lazy
    for index, field in enumerate(fields):
        args[field] = sys.argv[argindex + index + 1]

    # yay, dataclass shenanigans!!!
    return make_dataclass(arg, [tuple([k, v]) for k, v in args.items()])(**args)

def handle_args():
    if args := proc_arg('--convert', ['path', 'desiredformat']):
        return modlist.convert_modlist(Path(args.path), args.desiredformat)

    if args := proc_arg('--import', ['path']):
        return modlist.import_modlist(Path(args.path))

    if args := proc_arg('--export', ['packformat', 'path']):
        return modlist.export_modlist(args.packformat, Path(args.path))
    

