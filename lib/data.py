from sqlalchemy import types as sqltypes
from utils import setup_logging
from lib.config import config
import logging
import dataset

log = logging.getLogger(__name__)
setup_logging(log)

class Data:
    def __init__(self):
        log.debug(f"Establishing Connection to Database Address: '{config['db']['address']}'")
        self.base = dataset.connect(config['db']['address'], engine_kwargs={'pool_recycle': 3600})
        dbtab1 = self.base.create_table('mods', primary_id='modid', primary_type=sqltypes.Text)
        # dbtab1.create_column('names', sqltypes.Text)
        dbtab1.create_column('version', sqltypes.Text)
        # dbtab1.create_column('folders', sqltypes.Text)
        dbtab1.create_column('pending_filenames', sqltypes.Text)
        dbtab1.create_column('pending_version', sqltypes.Text)
        dbtab1.create_column('pending_fileids', sqltypes.Text)
        dbtab1.create_column('fileids', sqltypes.Text)   # the only reason that we have this is to support the --static flag
        dbtab1.create_column('patch', sqltypes.Text)
        log.debug(f"Database Connected! Object: {self.base}")
        

data = Data()