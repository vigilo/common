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
        module_name = liste[0]
        for i in liste[1:-1]:
            module_name = module_name + "." + i
    try :
        t = gettext.translation(module_name, '/usr/share/locale')
        translate_ = t.gettext
        return translate_
    except IOError, e :
        #IOError: [Errno 2] No translation file found for domain: 'vigilo-connector'
        return unchanged

