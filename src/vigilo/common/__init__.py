# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient les éléments communs à la plupart des composants
de Vigilo.
"""

import os
import urllib
import hashlib

__all__ = ("get_rrd_path", "parse_path")

_DIR_HASHES = {}

def get_rrd_path(hostname, ds=None, base_dir=None, path_mode="flat"):
    if base_dir is None:
        base_dir = "/var/lib/vigilo/rrds"
    subpath = ""

    if isinstance(hostname, unicode):
        # urllib et hashlib ne supportent pas unicode.
        hostname = hostname.encode('utf-8')

    if path_mode == "name" and len(hostname) >= 2:
        subpath = os.path.join(hostname[0], "".join(hostname[0:2]))
    elif path_mode == "hash":
        if hostname in _DIR_HASHES:
            subpath = _DIR_HASHES[hostname]
        else:
            host_hash = hashlib.md5(hostname).hexdigest()
            subpath = os.path.join(host_hash[0], "".join(host_hash[0:2]))
            _DIR_HASHES[hostname] = subpath

    host_dir = os.path.join(base_dir, subpath, urllib.quote_plus(hostname))
    if ds is None:
        return host_dir

    if isinstance(ds, unicode):
        # urllib ne supporte pas unicode.
        ds = ds.encode('utf-8')
    ds = urllib.quote_plus(ds)
    return os.path.join(host_dir, "%s.rrd" % ds)

def parse_path(path):
    """
    Analyse le contenu d'un chemin d'accès et retourne
    une liste de ses composantes.

    @param path: Chemin d'accès relatif ou absolu.
    @type path: C{basestr}
    @return: Ensemble des composantes du chemin d'accès
        ou C{None} si L{path} ne représente pas un chemin
        d'accès valide.
    @rtype: C{list} ou C{None}
    """
    parts = []

    # On refuse les chemins d'accès vides.
    if not path:
        return None

    absolute = (path[0] == '/')
    if absolute:
        path = path[1:]
    it = iter(path)

    try:
        portion = ""
        while True:
            ch = it.next()
            # Il s'agit d'une séquence d'échappement.
            if ch == '\\':
                ch = it.next()
                # Les seules séquences reconnus sont "\\" et "\/"
                # pour échapper le caractère d'échappement et le
                # séparateur des composantes du chemin respectivement.
                if ch == '/' or ch == '\\':
                    portion += ch
                else:
                    return None
            # Il s'agit d'un séparateur de chemins.
            elif ch == '/':
                if not portion:
                    return None
                parts.append(portion)
                portion = ""
            # Il s'agit d'un autre caractère (quelconque).
            else:
                portion += ch
    except StopIteration:
        if portion:
            parts.append(portion)

    # Permet de traiter correctement
    # le cas où le chemin est '/'.
    if not parts:
        return None

    # Un chemin relatif ne peut pas
    # contenir plusieurs composantes.
    if len(parts) != 1 and (not absolute):
        return None

    return parts
