# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Sets up logging, with twisted and multiprocessing integration.
"""
from __future__ import absolute_import

import os.path, sys, types
import logging, logging.config # pylint: disable-msg=W0406
import warnings
import ConfigParser

from vigilo.common.conf import settings, log_initialized

try:
    from multiprocessing import current_process
except ImportError:
    current_process = None

__all__ = ( 'get_logger', )

plugins_loaded = False
def get_logger(name, silent_load=False):
    """
    Obtient le logger associé à un nom de module qualifié.

    Cette fonction doit être utilisée à la place de C{logging.getLogger}.
    L'argument L{name} correspond généralement au nom du module appelant.
    Cette fonction est typiquement utilisée ainsi::
        LOGGER = get_logger(__name__)
    """
    global plugins_loaded # pylint: disable-msg=W0603
    if not plugins_loaded:
        plugins_loaded = True

        # Si multiprocessing est disponible, on l'utilise
        # pour obtenir le nom du processus dont provient
        # le message de log.
        logging._acquireLock() # pylint: disable-msg=W0212
        try:
            # Utilisation du formatteur de Vigilo par défaut.
            logging._defaultFormatter = VigiloFormatter()

            old_logger_class = logging.getLoggerClass()
            class MultiprocessingLogger(old_logger_class):
                """
                Classe pour la génération de logs, qui ajoute les noms
                du processus courant (le nom de l'exécutable lancé par
                l'utilisateur ainsi que le nom éventuellement donné au
                processus dans multiprocessing).
                """
                # pylint: disable-msg=W0232

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
        finally:
            logging._releaseLock() # pylint: disable-msg=W0212

        # On configure les logs depuis le fichier de settings
        for filename in settings.filenames:
            try:
                logging.config.fileConfig(filename)
            except ConfigParser.NoSectionError:
                continue # Ce fichier de conf n'a rien pour logging

        # Si Twisted est utilisé, on le configure pour transmettre
        # ses messages de log aux mécanismes classiques de C{logging}.
        # ATTENTION: cela doit être fait *après* le fileConfig ci-dessus,
        # sinon ça ne loggue plus rien.
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^(twisted|ampoule)\.')
        try:
            import twisted.python.log as twisted_logging
        except ImportError:
            pass
        else:
            # Mise en place de l'observateur de logs de Twisted
            # et branchement sur le mécanisme classique des logs.
            # On s'assure que l'observateur n'a pas été enregistré
            # auparavant pour éviter un problème de boucle infinie
            # dans les rule runners (dû à des ajouts multiples de
            # l'observateur).
            cur_obs_classes = [ o.im_class for o in
                                twisted_logging.theLogPublisher.observers ]
            if cur_obs_classes == [twisted_logging.DefaultObserver,]:
                tw_obs = twisted_logging.PythonLoggingObserver(loggerName=name)
                tw_obs.start()

        # on affiche un message pour indiquer quel fichier de settings a été
        # utilisé (sauf si on a explicitement demandé de pas le faire).
        log_initialized(silent_load)

    return logging.getLogger(name)

class VigiloFormatter(logging.Formatter):
    """
    Une classe de formattage pour le module logging de Python
    qui supporte le passage d'un encodage.
    Ceci permet de gérer correctement les messages de logging Unicode.

    Le code provient de :
    http://tony.czechit.net/2009/02/unicode-support-for-pythons-logging-library/
    """
    def __init__(self, fmt=None, datefmt=None, encoding='utf-8'):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.encoding = encoding

    def formatException(self, ei):
        r = logging.Formatter.formatException(self, ei)
        if type(r) in [types.StringType]:
            r = r.decode(self.encoding, 'replace') # Convert to unicode
        return r

    def format(self, record):
        t = logging.Formatter.format(self, record)
        if type(t) in [types.UnicodeType]:
            t = t.encode(self.encoding, 'replace')
        return t
