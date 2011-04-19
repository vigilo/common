# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Affiche les éléments appartenant à un point d'entrée.
Permet notamment de lister les extensions d'une application.
"""

import sys
from pkg_resources import working_set
from optparse import OptionParser
from vigilo.common.gettext import translate

_ = translate(__name__)

def main():
    """
    Cette fonction est appelée lorsqu'un utilisateur lance la commande
    'vigilo-plugins'.
    Cet utilitaire permet de lister le contenu d'un point d'entrée.
    """
    parser = OptionParser()
    parser.add_option('-p', '--provider', action="store_true",
        dest="display_provider", default=False,
        help=_("Displays the name and location of the Python package "
                "which provides this feature."))

    opts, args = parser.parse_args()
    if not args:
        sys.exit(-1)

    for ep in working_set.iter_entry_points(args[0]):
        print repr(ep.name),
        if opts.display_provider:
            print "--", _("Provided by:"), ep.dist,
        print
    sys.exit(0)


if __name__ == '__main__':
    main()
