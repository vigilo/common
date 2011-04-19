# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

""" VIGILO gettext """
from __future__ import absolute_import

import gettext # pylint: disable-msg=W0406

__all__ = ("translate", "translate_narrow")

def _translate_module(module_name):
    """
    Retrourne le module de traduction correspondant au module demandé.
    """
    # extraction of the module_name from the complete
    # module_name (which include the filename we don't want)
    parts = module_name.strip().split('.')
    if parts:
        module_name = '-'.join(parts[0:2]).replace('_', '-')
    return gettext.translation(module_name, fallback=True)

def translate(module_name):
    """
    Retourne la fonction de traduction de chaînes, qui retourne de l'unicode.
    """
    t = _translate_module(module_name)
    return t.ugettext

def translate_narrow(module_name):
    """
    Retourne la fonction de traduction de chaînes, qui ne retourne pas
    d'unicode mais une simple C{str}.
    """
    t = _translate_module(module_name)
    return t.gettext

