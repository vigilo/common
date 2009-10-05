# vim: set fileencoding=utf-8 sw=4 ts=4 et :
""" Daemonize """
from __future__ import absolute_import, with_statement

class empty_context:
    """ 
    define an empty context the functions '__enter__' and '__exit__' do nothing
    """
    def __enter__(self):
        pass
    def __exit__(self, type, value, traceback):
        pass



def daemonize():
    """ 
    function that return a daemon context (return None if parameters are wrong)
    """
    import os
    import sys
    from vigilo.common.gettext import translate
    _ = translate(__name__)
    import optparse
    from daemon import daemon, pidlockfile
    # hardcoding logging (no logger configured yet)
    # logger en dur (pas de logger déjà configuré)
    from logging import getLogger as temp_getLogger
    from logging.handlers import SysLogHandler as temp_SysLogHandler
    log = temp_getLogger(__name__)
    handler = temp_SysLogHandler("/dev/log", facility='daemon')
    log.addHandler(handler)

    parser = optparse.OptionParser()
    parser.add_option('--daemon', action='store_true', default=False,
            help='detach and run as a daemon')
    parser.add_option('--pidfile', action='store',
            help='write pid to PIDFILE. Avoid nfs, prefer /var/run on a tmpfs.')
    opts, leftovers = parser.parse_args()
    if leftovers:
        sys.stderr.write(_('%(moduleName)s: Too many arguments\n') % 
            {'moduleName': __name__})
        log.error(_('%(moduleName)s: Too many arguments.') %
            {'moduleName': __name__})
        return empty_context()
    if opts.daemon:
        pidfile = None
        if opts.pidfile is not None:
            pidfile = pidlockfile.PIDLockFile(opts.pidfile)
            if pidfile.is_locked():
                pid = pidfile.read_pid()
                if pid:
                    try:
                        os.kill(pid, 0) # Just checks it exists
                        # This has false positives, no matter.
                    except OSError: # Stale pid
                        # We must remove a stale pidfile by hand :/
                        log.info(_('Removing stale pid file at %(filename)s' +
                            ' (%(pid)d).') %
                            {'filename': opts.pidfile,
                             'pid': pid})
                        pidfile.break_lock()
                    else:
                        sys.stderr.write(_('Already running, pid is ' +
                            '%(pid)d.\n') % 
                            {'pid': pid})
                        log.error(_('Already running, pid is %(pid)d.') % 
                            {'pid': pid})
                else:
                    log.info(_('Removing stale pid file at %s (%d).') %
                        {'pidfile': opts.pidfile,
                         'pid': pid})
                    pidfile.break_lock()
        context = daemon.DaemonContext(
                     detach_process=True,
                     pidfile=pidfile,
                     )
        return context
    return empty_context()

