# vim: set fileencoding=utf-8 sw=4 ts=4 et :
""" VIGILO gettext """
from __future__ import absolute_import

import gettext

def unchanged(string):
    """ Fake function to not translate in case traduction file is missing """
    return string

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
    try :
        t = gettext.translation(module_name, '/usr/share/locale')
        translate_ = t.ugettext
        return translate_
    except IOError, e:
        # If the translation catalog did not load properly,
        # return a dummy translator which does nothing.
        return unchanged

