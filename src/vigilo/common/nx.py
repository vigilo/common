# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient des extensions pour (la compatibilité ascendante de)
la bibliothèque Python NetworkX.
"""
import networkx
from pkg_resources import parse_version

__all__ = ('networkx', )


# Monkey-patching pour la compatibilité networkx < 1.3
class NetworkXUnfeasible(networkx.NetworkXException):
    pass
if not hasattr(networkx, "NetworkXUnfeasible"):
    setattr(networkx, "NetworkXUnfeasible", NetworkXUnfeasible)

# shortest_path() lève une exception depuis networkx 1.4
# lorsqu'il n'existe aucun chemin entre les 2 nœuds,
# alors que la fonction retournait False précédemment.
# Monkey-patching pour la compatibilité ascendante.
class NetworkXNoPath(networkx.NetworkXException):
    pass

_old_shortest_path = networkx.shortest_path
def shortest_path(G, source=None, target=None, weight=None):
    res = _old_shortest_path(G, source, target, weight)
    if res == False:
        raise networkx.NetworkXNoPath("No path between %s and %s." % (source, target))
    return res

if not hasattr(networkx, "VigiloMonkeyPatch") and \
    parse_version(networkx.__version__) < parse_version("1.4"):
    setattr(networkx, "VigiloMonkeyPatch", True)
    setattr(networkx, "shortest_path", shortest_path)
