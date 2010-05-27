# vim: set fileencoding=utf-8 sw=4 ts=4 et :
""" VIGILO gettext """
from __future__ import absolute_import

import gettext

def translate(module_name):
    """ 
    Return function of traduction of the string 
    passed in parameter (if available) 
    """
    # extraction of the module_name from the complete 
    # module_name (which include the filename we don't want)
    liste = module_name.strip().split('.')
    if liste:
        module_name = '-'.join(liste[0:2]).replace('_', '-')

    t = gettext.translation(module_name, '/usr/share/locale', fallback=True)
    translate_ = t.ugettext
    return translate_

