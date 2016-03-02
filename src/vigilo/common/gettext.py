# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

""" VIGILO gettext """
from __future__ import absolute_import

import gettext # pylint: disable-msg=W0406
from pkg_resources import resource_filename

__all__ = ("translate", "translate_narrow", "l_")

def _translate_module(module_name):
    """
    Retrourne le module de traduction correspondant au module demandé.
    """
    # extraction of the module_name from the complete
    # module_name (which include the filename we don't want)
    parts = module_name.strip().split('.')
    if parts:
        # Cas particulier des scripts dans les IHM web (TurboGears).
        if parts[0] != 'vigilo' and parts[0].startswith('vigi'):
            localedir = resource_filename(parts[0], 'i18n')
            return gettext.translation(parts[0], localedir=localedir,
                                       fallback=True)
        module_name = '-'.join(parts[0:2]).replace('_', '-')
    return gettext.translation(module_name, fallback=True)

def translate(module_name):
    """
    Retourne la fonction de traduction de chaînes, qui retourne de l'unicode.

    Cette fonction est à privilégier pour l'usage général (affichage
    dans les interfaces web, dans les journaux, etc.).

    @param module_name: Nom du module de Vigilo dans lequel les traductions
        doivent être recherchées.
    @type module_name: C{str}
    @return: Fonction de traduction retournant de l'unicode.
    @rtype: C{function}
    """
    t = _translate_module(module_name)
    return t.ugettext

def translate_narrow(module_name):
    """
    Retourne la fonction de traduction de chaînes, qui ne retourne pas
    d'unicode mais une simple C{str} dans l'encodage du système.

    Cette fonction est à privilégier pour les affichages en ligne de
    commandes.

    @param module_name: Nom du module de Vigilo dans lequel les traductions
        doivent être recherchées.
    @type module_name: C{str}
    @return: Fonction de traduction retournant des chaînes
        dans l'encodage du système.
    @rtype: C{function}
    """
    t = _translate_module(module_name)
    return t.lgettext

def l_(message):
    """
    Fonction permettant de marquer les messages comme nécessitant
    une traduction, sans pour autant les traduire.

    @param message: Message à marquer comme nécessitant une traduction.
    @type message: C{str}
    @return: Le C{message} original, sans altération.
    @rtype: C{str}
    """
    return message
