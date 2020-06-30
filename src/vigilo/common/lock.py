# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os
import fcntl
import atexit

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

__all__ = ("grab_lock", "delete_lock")


def grab_lock(lockfile):
    """
    Ajoute un verrou pour empêcher l'exécution simultanée
    de plusieurs instances de l'application.

    @note: Le verrou ainsi posé est automatiquement détruit
        lorsque l'exécution se termine.
    """
    f = open(lockfile, 'a+')
    try:
        LOGGER.debug("Acquiring the lock.")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError as e:
        LOGGER.error(_("Can't obtain lock on lockfile (%(lockfile)s). "
                       "Application already running? REASON: %(error)s"),
                     { 'lockfile': f.name, 'error': e })
        return False

    # On veut être sûr que le verrou sera supprimé
    # à l'arrêt de l'application.
    atexit.register(delete_lock, f)
    return True

def delete_lock(f):
    """
    Supprime le verrou posé lors du démarrage lorsque l'application se termine.

    @param f: Descripteur de fichier représentant le verrou.
    """
    LOGGER.debug("Removing the lock.")
    fcntl.flock(f, fcntl.LOCK_UN)
    filename = f.name
    f.close()
    if os.path.exists(filename):
        os.remove(filename)
