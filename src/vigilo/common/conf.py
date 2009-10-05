# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
A django-inspired settings module.

Use dictionary access on the 'settings' object.
Define VIGILO_SETTINGS in the environment to a valid file path
that will be imported.

The settings file will be searched in a list of directories defined in
the L{Settings._dirs} list.

The default file name is "settings.py", and the first valid file is returned.

To load the default config file::
    from vigilo.common.conf import settings
    conntype = settings['MEMCACHE_CONN_TYPE']

To load a module-specific config file::
    from vigilo.common.conf import settings
    settings.load("connector")

By loading a module, the filename will be looked for in a subdirectory
named after the module. Examples:

C{settings.load()} looks for:
  - /etc/vigilo/settings.py
  - ~/.vigilo/settings.py
  - ./settings.py

C{settings.load("connector")} looks for:
  - /etc/vigilo/connector/settings.py
  - ~/.vigilo/connector/settings.py
  - ./connector/settings.py

If you define VIGILO_SETTINGS to a valid filename, it will override the
search mechanism and be used instead.

Command-line usage::
    conntype=$(python -m vigilo.common.conf --get MEMCACHE_CONN_TYPE)


Impl notes::
    a ConfigParser.SafeConfigParser would have worked as well,
    we'd replace settings.py in PYTHONPATH with a settings.cfg in PWD.
    I guess I'm too used to django.

We can't import any other Vigilo code here.
This is because Vigilo code may log or require settings for some other reason.
"""

from __future__ import absolute_import

import os
import re
import sys
import UserDict

__all__ = ( 'settings', )

# Uppercase alnum, starts with alpha, underscores between alnums.
SETTING_RE = re.compile('[A-Z][A-Z0-9]*(_[A-Z0-9]+)*')

class Settings(UserDict.DictMixin, object):
    """
    A read-only dictionary that allows access only to properly-named settings.

    Valid settings name are of the form:
    FOO_BAR_BAZ2

    @ivar filename: Filename to load, defaults to "settings.py"
    @type filename: C{str}
    @ivar conf_file: The path of the chosen file (used for logging)
    @type conf_file: C{str}
    """

    def __init__(self, filename="settings.py"):
        self.__dct = {}
        self.filename = filename
        self.conf_file = None

    def __getitem__(self, name):
        if not SETTING_RE.match(name):
            # Or maybe ValueError
            raise KeyError('Invalid name', name)
        return self.__dct[name]

    def keys(self):
        return [k for k in self.__dct if SETTING_RE.match(k)]

    def load(self, module=None):
        """
        Load the configuration, optionnaly giving a Vigilo module

        @param module: a Vigilo module name
        @type  module: C{str}, for example "vigiconf" or "correlator".
        @raise IOError: no config file has been found
        """
        self.conf_file = self.find_file(module)
        if not self.conf_file:
            # hardcoding logging (file settings.py not found, so no logger 
            #  configured yet)
            # logger hardcodé (fichier settings.py non trouvé, pas de logger
            #  déjà configuré)
            import logging as temp_logging
            log = temp_logging.getLogger(__name__)
            handler = temp_logging.handlers.SysLogHandler(address="/dev/log", facility='daemon')
            log.addHandler(handler)
            log.error("No config file found")
            raise IOError("No config file found")
        self.load_file(self.conf_file)

    def find_file(self, module=None):
        """
        Search the paths for the settings file

        @param module: a Vigilo module name
        @type  module: C{str}, for example "vigiconf" or "correlator".
        @return: the full path to the config file
        @rtype: C{str}
        """
        env_file = os.environ.get('VIGILO_SETTINGS', None)
        if env_file and os.path.exists(env_file):
            return env_file
        for d in self._get_dirs(module):
            path = os.path.join(d, self.filename)
            if not os.path.exists(path):
                continue
            return path
        return None

    def load_file(self, filename):
        """
        Load a specific file

        @param filename: the file path to load. Must exist and be valid python.
        @type  filename: C{str}
        """
        settings_raw = {}
        execfile(filename, settings_raw)
        self.__dct.update(settings_raw)

    def _get_dirs(self, module=None):
        """
        Return the list of directories to use when loading a configuration
        file. The order in the list significant.

        @param module: a Vigilo module name
        @type  module: C{str}, for example "vigiconf" or "correlator".
        @rtype: C{list} of directories
        """
        dirs = []
        for confdir in ["/etc/vigilo",
                        os.path.join(os.environ.get("HOME", ""), ".vigilo")]:
            if module:
                confdir = "%s-%s" % (confdir, module)
            dirs.append(confdir)
        dirs.append(".")
        return dirs

settings = Settings()
settings.load()


def log_initialized():
    """
    A backdoor for logging to tell us it was initialized, so that
    we can log our own initialization.
    """

    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)
    LOGGER.info('Loaded settings from path %s', settings.conf_file)

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

