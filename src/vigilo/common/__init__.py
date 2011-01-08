# -*- coding: utf-8 -*-
"""
Ce module contient les éléments communs à la plupart des composants
de Vigilo.
"""

import os
import urllib
import hashlib

__all__ = ("get_rrd_path", )

_DIR_HASHES = {}

def get_rrd_path(hostname, ds=None, base_dir=None, path_mode="flat"):
    if base_dir is None:
        base_dir = "/var/lib/vigilo/rrds"
    subpath = ""
    if path_mode == "name" and len(hostname) >= 2:
        subpath = os.path.join(hostname[0], "".join(hostname[0:2]))
    elif path_mode == "hash":
        if hostname in _DIR_HASHES:
            subpath = _DIR_HASHES[hostname]
        else:
            hash = hashlib.md5(hostname).hexdigest()
            subpath = os.path.join(hash[0], "".join(hash[0:2]))
            _DIR_HASHES[hostname] = subpath
    host_dir = os.path.join(base_dir, subpath, hostname)
    if ds is None:
        return host_dir
    ds = urllib.quote_plus(ds)
    return os.path.join(host_dir, "%s.rrd" % ds)

