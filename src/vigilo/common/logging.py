# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Sets up logging, with twisted and multiprocessing integration.
"""
from __future__ import absolute_import

import logging, logging.config
import runpy

from vigilo.common.conf import settings, log_initialized

__all__ = ( 'get_logger', )

plugins_loaded = False
def get_logger(name):
    """
    Obtient le logger associé à un nom de module qualifié.

    L'argument L{name} correspond généralement au nom du module appelant.
    Cette méthode est typiquement utilisée ainsi::
        LOGGER = get_logger(__name__)
    """

    global plugins_loaded
    if not plugins_loaded:
        plugins_loaded = True
        logging.config.fileConfig(settings.filename)
        log_initialized()

    return logging.getLogger(name)

