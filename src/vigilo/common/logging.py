# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Sets up logging, with twisted and multiprocessing integration.
"""
from __future__ import absolute_import

import os.path, sys
import logging, logging.config
import warnings
import ConfigParser

from vigilo.common.conf import settings, log_initialized

try:
    from multiprocessing import current_process
except ImportError:
    current_process = None

__all__ = ( 'get_logger', )

plugins_loaded = False
def get_logger(name):
    """
    Obtient le logger associé à un nom de module qualifié.

    Cette fonction doit être utilisée à la place de C{logging.getLogger}.
    L'argument L{name} correspond généralement au nom du module appelant.
    Cette fonction est typiquement utilisée ainsi::
        LOGGER = get_logger(__name__)
    """

    global plugins_loaded
    if not plugins_loaded:
        plugins_loaded = True

        # Si multiprocessing est disponible, on l'utilise
        # pour obtenir le nom du processus dont provient
        # le message de log.
        old_logger_class = logging.getLoggerClass()
        class MultiprocessingLogger(old_logger_class):
            """
            Classe pour la génération de logs, qui ajoute les noms
            du processus courant (le nom de l'exécutable lancé par
            l'utilisateur ainsi que le nom éventuellement donné au
            processus dans multiprocessing).
            """

            def makeRecord(self, *args, **kwargs):
                """Génération d'un enregistrement de log."""
                record = old_logger_class.makeRecord(self, *args, **kwargs)
                record.processName = os.path.basename(sys.argv[0])
                if not current_process:
                    record.multiprocessName = '???'
                else:
                    record.multiprocessName = current_process().name
                return record
        logging.setLoggerClass(MultiprocessingLogger)

        # Si Twisted est utilisé, on le configure pour transmettre
        # ses messages de log aux mécanismes classiques de C{logging}.
        warnings.filterwarnings(
                'ignore', category=DeprecationWarning, module='^twisted\.')
        try:
            import twisted.python.log as twisted_logging
        except ImportError:
            pass
        else:
            # Mise en place de l'observateur de logs de Twisted
            # et branchement sur le mécanisme classique des logs.
            tw_obs = twisted_logging.PythonLoggingObserver()
            tw_obs.start()

        # On configure les logs depuis le fichier de settings
        # et on affiche un message pour indiquer quel fichier
        # de settings a été utilisé.
        for filename in settings.filenames:
            try:
                logging.config.fileConfig(filename)
            except ConfigParser.NoSectionError, e:
                continue # Ce fichier de conf n'a rien pour logging
        log_initialized()

    return logging.getLogger(name)

