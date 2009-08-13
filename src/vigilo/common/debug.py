# vim: set fileencoding=utf-8 sw=4 ts=4 et :
from __future__ import absolute_import

from IPython.Debugger import Tracer

__all__ = ( 'debug_here', )

"""
Debugging helpers.

Usage:

    from vigilo.common.debug import debug_here

    … later in your code
    debug_here()

"""

debug_here = Tracer()

