import functools
import os

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
                    port = kwargs.get('port')
                    if port:
                        # setup a tcp server
                        server = RpcServer(port, server_cmd)
                        try:
                            server.start()
                            func(task_id, *args, **kwargs)
                        except:
                            raise
                        finally:
                            server.stop()
                    else:
                        func(task_id, *args, **kwargs)
                    try:
                        os.remove(pidfile)
                    except OSError:
                        pass

        return _wrapper

    return decorate_func
