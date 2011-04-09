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
    current_process = None # pylint: disable-msg=C0103

__all__ = ( 'get_logger', )

PLUGINS_LOADED = False
def get_logger(name, silent_load=False):
    """
    Obtient le logger associé à un nom de module qualifié.

    Cette fonction doit être utilisée à la place de C{logging.getLogger}.
    L'argument L{name} correspond généralement au nom du module appelant.
    Cette fonction est typiquement utilisée ainsi::
        LOGGER = get_logger(__name__)
    """
    global PLUGINS_LOADED # pylint: disable-msg=W0603
    if not PLUGINS_LOADED:
        PLUGINS_LOADED = True

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
            if cur_obs_classes == [twisted_logging.DefaultObserver, ]:
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
        """
        Formatte l'enregistrement à journaliser en prenant soin
        d'adapter l'encoding si nécessaire.
        """
        # On préfèrerait utiliser une classe qui hérite de Logger
        # pour éviter de faire ces opérations pour chaque message
        # et chaque appel au formateur.
        # Malheureusement, les bibliothèques externes (ex: Twisted)
        # n'utiliseront pas forcément notre classe et échoueront
        # si le format des messages contient 'processName', etc.
        record.processName = os.path.basename(sys.argv[0])
        if not current_process:
            record.multiprocessName = '???'
        else:
            record.multiprocessName = current_process().name

        t = logging.Formatter.format(self, record)
        if type(t) in [types.UnicodeType]:
            t = t.encode(self.encoding, 'replace')
        return t
