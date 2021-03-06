# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Décorateur pour le profiling de méthodes. Source:
U{http://stackoverflow.com/questions/1171166/how-can-i-profile-a-sqlalchemy-powered-application}

Exemple::

    from vigilo.common.profiling import profile
    @profile
    def function_to_profile():
        <do work>

"""

import cProfile as profiler
import gc, pstats, time

def profile(fn):
    def wrapper(*args, **kw):
        _elapsed, stat_loader, result = _profile("/tmp/profiling.txt", fn,
                                                 *args, **kw)
        stats = stat_loader()
        stats.sort_stats('cumulative')
        stats.print_stats()
        # uncomment this to see who's calling what
        #stats.print_callers()
        return result
    return wrapper

def _profile(filename, fn, *args, **kw): # pylint: disable-msg=W0613
    load_stats = lambda: pstats.Stats(filename)
    gc.collect()

    began = time.time()
    profiler.runctx('result = fn(*args, **kw)', globals(), locals(),
                    filename=filename)
    ended = time.time()

    return ended - began, load_stats, locals()['result']

