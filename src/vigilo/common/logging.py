# vim: set fileencoding=utf-8 sw=4 ts=4 et :
from __future__ import absolute_import

"""
Sets up logging, with twisted and multiprocessing integration.
"""

import logging
import runpy

from vigilo.common.conf import settings

__all__ = ( 'get_logger', )

plugins_loaded = False
def get_logger(name):
    """
    Gets a logger from a dotted name.

    This must replace all uses of logging.getLogger.

    Ensures that plugins listed in settings['LOGGING_PLUGINS']
    have been registered. Use them for very early logging initialization,
    such as calls to logging.setLoggerClass or multiprocessing.get_logger .

    Since name should be the package name, a common use pattern is:
        LOGGER = get_logger(__name__)
    """

    global plugins_loaded
    if not plugins_loaded:
        for plugin_name in settings['LOGGING_PLUGINS']:
            #load_plugin(plugin_name, False) # Needs registry
            runpy.run_module(plugin_name)['register'](None)
    return logging.getLogger(name)

