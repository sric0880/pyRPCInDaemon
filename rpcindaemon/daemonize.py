import atexit
import functools
import os
import signal

import filelock

from .exceptions import *
from .rpcserver import RpcServer, ServerCmd


def makedaemon(log_dir=".", server_cmd=ServerCmd):
    """
    Params:
    log_dir: daemon process write log to
    """

    def decorate_func(func):
        @functools.wraps(func)
        def _wrapper(task_id, *args, **kwargs):
            import daemon

            cwd = os.getcwd()
            stdout_file = open(os.path.join(log_dir, f"pidfile-{task_id}.log"), "w")
            pidfile = f"pidfile-{task_id}"
            if os.path.exists(pidfile):
                raise PidfileExistsError(
                    f"{pidfile} exists(task may be running), cannot overwrite it. something is wriong."
                )
            with daemon.DaemonContext(
                working_directory=cwd, stdout=stdout_file, stderr=stdout_file
            ):
                pidfile_lockfile = f"{pidfile}.lock"
                with filelock.FileLock(pidfile_lockfile, blocking=False):
                    with open(pidfile, "w") as f:
                        f.write(str(os.getpid()) + "\n")
                    server = None
                    def _release():
                        nonlocal server
                        nonlocal pidfile
                        try:
                            os.remove(pidfile)
                        except OSError:
                            pass
                        if server is not None:
                            server.stop()
                            server = None
                    atexit.register(_release)
                    try:
                        port = kwargs.get('port')
                        if port:
                            # setup a tcp server
                            server = RpcServer(port, server_cmd)
                            server.start()
                        func(task_id, *args, **kwargs)
                    except:
                        raise
                    finally:
                        _release()
                        
        return _wrapper

    return decorate_func


def set_signal_handler(handler):
    def _sigstop_linuxlike(signum, stackframe):
        handler()
    if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
        signal.signal(signal.SIGINT, _sigstop_linuxlike)
    if signal.getsignal(signal.SIGTERM) == signal.SIG_DFL:
        signal.signal(signal.SIGTERM, _sigstop_linuxlike)

# windows 单进程 前台：sighandler=None
# windows 单进程 后台：sighandler!=None
# linux 单进程 前台：sighandler=None
# linux 单进程 后台：sighandler=None
# def set_sighandler_one_process(sighandler, contexts):
#     if sighandler is None:
#         if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
#             signal.signal(signal.SIGINT, partial(_sigstop1, contexts))
#         if signal.getsignal(signal.SIGTERM) == signal.SIG_DFL:
#             signal.signal(signal.SIGTERM, partial(_sigstop1, contexts))
#     else:
#         # Windows daemon环境下
#         def __sigstop(signum):
#             _sigstop(contexts, signum)
#             sighandler._stop_nowait()

#         sighandler.sigint = __sigstop
#         sighandler.sigterm = __sigstop
#         sighandler.sigabrt = __sigstop