from color import trace
from typing import Any
import logging
import sys
import os

def is_docker() -> bool:
    path = '/proc/self/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.isfile(path) and any('docker' in line for line in open(path)))

def stream_supports_colour(stream: Any) -> bool:
    is_a_tty = hasattr(stream, 'isatty') and stream.isatty()

    # Pycharm and Vscode support colour in their inbuilt editors
    if 'PYCHARM_HOSTED' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
        return is_a_tty

    if sys.platform != 'win32':
        # Docker does not consistently have a tty attached to it
        return is_a_tty or is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ('ANSICON' in os.environ or 'WT_SESSION' in os.environ)
    
class _ColourFormatter(logging.Formatter):
    LEVEL_COLOURS = [
            (logging.DEBUG, trace.black.b),
            (logging.INFO, trace.blue),
            (logging.WARNING, trace.yellow),
            (logging.ERROR, trace.red),
            (logging.CRITICAL, trace.red.b),
        ]
    FORMATS = {
        level: logging.Formatter(
            f'{trace.style.bold}{trace.black}%(asctime)s{trace.reset} {trace.style.bold}{colour}%(levelname)-8s{trace.reset} {trace.magenta}%(name)s{trace.reset} %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'{trace.red}{text}{trace.reset}'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output

def setup_logging(logger, level = None) -> None:
    if level is None:
        if '--debug' in sys.argv:
            level = logging.DEBUG
        else:
            level = logging.INFO

    handler = logging.StreamHandler()

    file_handler = logging.FileHandler('debug.log')
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    f_formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

    if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream):
        formatter = _ColourFormatter()
    else:
        formatter = f_formatter


    # if root:
    #     logger = logging.getLogger()
    # else:
    #     library, _, _ = __name__.partition('.')
    #     logger = logging.getLogger(library)

    handler.setFormatter(formatter)
    file_handler.setFormatter(f_formatter)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(file_handler)
