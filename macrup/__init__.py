# Setup logging
from .log import Log
_log = Log('root')

from .cli import macrup


def entry():
    _log.debug('Starting CLI')
    macrup()