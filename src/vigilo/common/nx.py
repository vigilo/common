# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient des extensions pour (la compatibilité ascendante de)
la bibliothèque Python NetworkX.
"""
import networkx

__all__ = ('networkx', )

# Monkey-patching pour la compatibilité networkx < 1.3
class NetworkXUnfeasible(networkx.NetworkXException):
    pass
if not hasattr(networkx, "NetworkXUnfeasible"):
    setattr(networkx, "NetworkXUnfeasible", NetworkXUnfeasible)
