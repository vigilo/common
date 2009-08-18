# vim: set fileencoding=utf-8 sw=4 ts=4 et :
from __future__ import absolute_import

__all__ = ( 'settings', )

"""
A django-inspired settings module.

Use dictionary access on the 'settings' object.
Define VIGILO_SETTINGS_MODULE in the environment to a dotted module path
that will be imported.
The default is equivalent to 'import settings', meaning you should put
a settings.py file in the current directory or the PYTHONPATH.

Usage:
    from vigilo.common.conf import settings
    conntype = settings['MEMCACHE_CONN_TYPE']

Command-line usage:
    conntype=$(python -m vigilo.common.conf --get MEMCACHE_CONN_TYPE)

"""

"""
Impl notes:
    a ConfigParser.SafeConfigParser would have worked as well,
    we'd replace settings.py in PYTHONPATH with a settings.cfg in PWD.
    I guess I'm too used to django.

We can't import any other Vigilo code here.
This is because Vigilo code may log or require settings for some other reason.
"""

import os
import re
import logging
import runpy
import sys
import UserDict

# Uppercase alnum, starts with alpha, underscores between alnums.
SETTING_RE = re.compile('[A-Z][A-Z0-9]*(_[A-Z0-9]+)*')

class Settings(UserDict.DictMixin, object):
    """
    A read-only dictionary that allows access only to properly-named settings.

    Valid settings name are of the form:
    FOO_BAR_BAZ2
    """

    def __init__(self, dct):
        self.__dct = dct

    def __getitem__(self, name):
        if not SETTING_RE.match(name):
            # Or maybe ValueError
            raise KeyError('Invalid name', name)
        return self.__dct[name]

    def keys(self):
        return [k for k in self.__dct if SETTING_RE.match(k)]

VIGILO_SETTINGS_MODULE = os.environ.get('VIGILO_SETTINGS_MODULE', 'settings')

settings_raw = runpy.run_module(VIGILO_SETTINGS_MODULE)
settings = Settings(settings_raw)

def log_initialized():
    """
    A backdoor for logging to tell us it was initialized, so that
    we can log our own initialization.
    """

    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)
    LOGGER.info('Loaded settings module %r from path %r',
            VIGILO_SETTINGS_MODULE,
            settings_raw.get('__file__'),
            )

def main():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-g', '--get', dest='get', metavar='SETTING_NAME')
    (opts, args) = parser.parse_args()
    if opts.get is None:
        return -2
    val = settings[opts.get]
    sys.stdout.write('%s\n' % val)

if __name__ == '__main__':
    sys.exit(main())

