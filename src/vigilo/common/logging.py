# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Sets up logging, with twisted and multiprocessing integration.
"""
from __future__ import absolute_import

import os.path, sys, types
import logging, logging.config # pylint: disable-msg=W0406
import warnings

from vigilo.common.conf import settings, log_initialized

try:
    from multiprocessing import current_process
except ImportError:
    current_process = None # pylint: disable-msg=C0103

__all__ = ( 'get_logger', 'fileConfig')


# Adapté depuis le code du module logging.config de Python 2.6
# Copyright 2001-2007 by Vinay Sajip.
# W0212: Access to a protected member FOO of a client class.
# pylint: disable-msg=W0212
def fileConfig(disable_existing_loggers=1):
    """
    Read the logging configuration from a ConfigObj-format file.

    This can be called several times from an application, allowing an end user
    the ability to select from various pre-canned configurations (if the
    developer provides a mechanism to present the choices and load the chosen
    configuration).
    """
    formatters = _create_formatters()

    # critical section
    logging._acquireLock()
    try:
        logging._handlers.clear()
        del logging._handlerList[:]
        # Handlers add themselves to logging._handlers
        handlers = _install_handlers(formatters)
        _install_loggers(handlers, disable_existing_loggers)
    finally:
        logging._releaseLock()


# Adapté depuis le code du module logging.config de Python 2.6
# Copyright 2001-2007 by Vinay Sajip.
def _resolve(name):
    """Resolve a dotted name to a global object."""
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found


def _strip_spaces(alist):
    """Retire les espaces autour de chacune des valeurs de la liste."""
    return [x.strip() for x in alist]


# Adapté depuis le code du module logging.config de Python 2.6
# Copyright 2001-2007 by Vinay Sajip.
def _create_formatters():
    """Create and return formatters"""
    fconf = settings.get('formatters')
    if not fconf:
        return {}
    flist = fconf.as_list("keys")
    if not len(flist):
        return {}
    flist = _strip_spaces(flist)
    formatters = {}
    for form in flist:
        sectname = "formatter_%s" % form
        opts = settings.get(sectname, {})
        # vigilo.common.conf dispose d'un hack afin que la valeur
        # des options "format" et "datefmt" dans les sections dont
        # le nom commence par "formatter_" ne soit pas interprétée.
        # Ce hack est nécessaire pour pouvoir gérer correctement
        # une valeur contenant des virgules dans le fichier de
        # configuration.
        if "format" in opts:
            fs = opts.get("format", 1)
        else:
            fs = None
        if "datefmt" in opts:
            dfs = opts.get("datefmt", 1)
        else:
            dfs = None
        c = logging.Formatter
        if "class" in opts:
            class_name = opts.get("class")
            if class_name:
                c = _resolve(class_name)
        f = c(fs, dfs)
        formatters[form] = f
    return formatters


# Adapté depuis le code du module logging.config de Python 2.6
# Copyright 2001-2007 by Vinay Sajip.
# W0212: Access to a protected member FOO of a client class.
# pylint: disable-msg=W0212
def _install_handlers(formatters):
    """Install and return handlers"""
    hconf = settings.get('handlers')
    if not hconf:
        return {}
    hlist = hconf.as_list("keys")
    if not len(hlist):
        return {}
    hlist = _strip_spaces(hlist)
    handlers = {}
    fixups = [] #for inter-handler references
    for hand in hlist:
        sectname = "handler_%s" % hand
        opts = settings.get(sectname, {})
        klass = opts["class"]
        fmt = opts.get("formatter", "")
        try:
            klass = eval(klass, vars(logging))
        except (AttributeError, NameError):
            klass = _resolve(klass)
        # vigilo.common.conf dispose d'un hack afin que la valeur
        # de l'option "args" dans les sections dont le nom commence
        # par "handler_" ne soit pas interprétée. Ce hack est
        # nécessaire pour pouvoir gérer correctement une valeur
        # comme (sys.stdout, ) dans le fichier de configuration.
        args = opts.get("args")
        args = eval(args, vars(logging))
        h = klass(*args)
        level = opts.get("level")
        if level != None:
            h.setLevel(logging._levelNames[level])
        if len(fmt):
            h.setFormatter(formatters[fmt])
        if issubclass(klass, logging.handlers.MemoryHandler):
            target = opts.get("target", "")
            if len(target): #the target handler may not be loaded yet, so keep for later...
                fixups.append((h, target))
        handlers[hand] = h
    #now all handlers are loaded, fixup inter-handler references...
    for h, t in fixups:
        h.setTarget(handlers[t])
    return handlers


# Adapté depuis le code du module logging.config de Python 2.6
# Copyright 2001-2007 by Vinay Sajip.
def _install_loggers(handlers, disable_existing_loggers):
    """Create and install loggers"""
    lconf = settings.get('loggers')
    if not lconf:
        return

    # configure the root first
    root = logging.root
    llist = lconf.as_list("keys")
    llist = _strip_spaces(llist)
    try:
        llist.remove("root")
    except ValueError:
        pass
    else:
        sectname = "logger_root"
        log = root
        opts = settings.get(sectname)
        level = opts.get("level", None)
        if level != None:
            log.setLevel(logging._levelNames[level])
        for h in root.handlers[:]:
            root.removeHandler(h)
        hlist = opts.as_list("handlers")
        if len(hlist):
            hlist = _strip_spaces(hlist)
            for hand in hlist:
                log.addHandler(handlers[hand])

    #and now the others...
    #we don't want to lose the existing loggers,
    #since other threads may have pointers to them.
    #existing is set to contain all existing loggers,
    #and as we go through the new configuration we
    #remove any which are configured. At the end,
    #what's left in existing is the set of loggers
    #which were in the previous configuration but
    #which are not in the new configuration.
    existing = root.manager.loggerDict.keys()
    #The list needs to be sorted so that we can
    #avoid disabling child loggers of explicitly
    #named loggers. With a sorted list it is easier
    #to find the child loggers.
    existing.sort()
    #We'll keep the list of existing loggers
    #which are children of named loggers here...
    child_loggers = []
    #now set up the new ones...
    for log in llist:
        sectname = "logger_%s" % log
        opts = settings.get(sectname)
        qn = opts["qualname"]
        if "propagate" in opts:
            propagate = opts.as_int("propagate")
        else:
            propagate = 1
        logger = logging.getLogger(qn)
        if qn in existing:
            i = existing.index(qn)
            prefixed = qn + "."
            pflen = len(prefixed)
            num_existing = len(existing)
            i = i + 1 # look at the entry after qn
            while (i < num_existing) and (existing[i][:pflen] == prefixed):
                child_loggers.append(existing[i])
                i = i + 1
            existing.remove(qn)
        level = opts.get("level", None)
        if level != None:
            logger.setLevel(logging._levelNames[level])
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.propagate = propagate
        logger.disabled = 0
        hlist = opts.as_list("handlers")
        if len(hlist):
            hlist = _strip_spaces(hlist)
            for hand in hlist:
                if hand:
                    logger.addHandler(handlers[hand])

    #Disable any old loggers. There's no point deleting
    #them as other threads may continue to hold references
    #and by disabling them, you stop them doing any logging.
    #However, don't disable children of named loggers, as that's
    #probably not what was intended by the user.
    for log in existing:
        logger = root.manager.loggerDict[log]
        if log in child_loggers:
            logger.level = logging.NOTSET
            logger.handlers = []
            logger.propagate = 1
        elif disable_existing_loggers:
            logger.disabled = 1


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
    # Le test sur la présence de loggers permet de gérer certains cas
    # où les loggers sont créés avant qu'une configuration des logs
    # n'ait pu être chargée (cf. #1057).
    if (not PLUGINS_LOADED) and settings.get('loggers'):
        PLUGINS_LOADED = True

        # On configure les logs depuis le(s) fichier(s) de configuration.
        fileConfig()

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

def get_error_message(exc):
    """
    Étant donné une exception, récupère le message d'erreur
    contenu dans l'exception.

    @param exc: Exception Python.
    @type exc: C{Exception}
    @return: Message d'erreur représenté par l'exception.
    @rtype: C{unicode}
    """
    try:
        # On tente d'abord une conversion directe vers Unicode
        # (nécessite que la classe de l'exception redéfinisse
        # __unicode__; c'est le cas de toutes les classes
        # dérivées de Exception depuis Python 2.6).
        return unicode(exc)

    except UnicodeDecodeError:
        # On suppose que l'exception contient en fait
        # un message d'erreur de type str encodé en UTF-8.
        return unicode(str(exc), 'utf-8', 'replace')

    except UnicodeEncodeError:
        # Contournement pour Python 2.5, unicode(exc) nous amène ici
        # si l'exception contient de l'unicode car Exception.__unicode__
        # n'existe pas dans cette version et un str() implicite a lieu.
        return unicode(exc.message)
