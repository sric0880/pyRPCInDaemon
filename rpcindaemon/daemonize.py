import atexit
import errno
import multiprocessing
import os
import signal
import sys
from ctypes import c_bool
from functools import partial
from queue import Empty

import filelock

from .exceptions import *
from .rpcserver import RpcServer, ServerCmd


def nodaemon(func):
    def _wrapper(task_id, *args, **kwargs):
        func(task_id, F(None, False), *args, **kwargs)

    return _wrapper


def makedaemon(log_dir=".", server_cmd=ServerCmd):
    """
    Params:
        log_dir: daemon process write log to
    """
    if sys.platform == "win32":

        def decorate_func(func):
            def _wrapper(task_id, *args, port=0, **kwargs):
                from .daemoniker import Daemonizer

                with Daemonizer() as (is_setup, daemonizer):
                    if is_setup:
                        # This code is run before daemonization.
                        pass

                    # We need to explicitly pass resources to the daemon; other variables
                    # may not be correct
                    stdout_file = os.path.join(log_dir, f"pidfile-{task_id}.log")
                    invocation = " ".join(sys.argv)
                    is_parent, params = daemonizer(
                        f"pidfile-{task_id}",
                        (task_id, args, port, kwargs, server_cmd),
                        stdout_goto=stdout_file,
                        stderr_goto=stdout_file,
                        explicit_rescript=invocation,
                    )

                    if is_parent:
                        # Run code in the parent after daemonization
                        pass

                # We are now daemonized, and the parent just exited.
                _task_id, _args, _port, _kwargs, _server_cmd = params
                from .daemoniker import SignalHandler1

                win32_sighandler = SignalHandler1(f"pidfile-{_task_id}")
                win32_sighandler.start()
                server = None

                def _release():
                    nonlocal server
                    if server is not None:
                        server.stop()
                        server = None

                atexit.register(_release)  # 可以注册多次
                try:
                    if _port:
                        # setup a tcp server
                        server = RpcServer(_port, _server_cmd)
                        server.start()
                    func(_task_id, F(win32_sighandler, True), *_args, **_kwargs)
                except:
                    raise
                finally:
                    _release()

            return _wrapper

    else:

        def decorate_func(func):
            def _wrapper(task_id, *args, port=0, **kwargs):
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
                ):  # fork. parent process has exited.
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
                            if port:
                                # setup a tcp server
                                server = RpcServer(port, server_cmd)
                                server.start()
                            func(task_id, F(None, True), *args, **kwargs)
                        except:
                            raise
                        finally:
                            _release()

            return _wrapper

    return decorate_func


def _init_pool_processe(a, b, c):
    global lock
    global message_queue
    global signal_stop
    lock = a
    message_queue = b
    signal_stop = c


class F:
    __slot__ = ("_win32_sighandler", "_is_daemon")

    def __init__(self, _win32_sighandler, _is_daemon) -> None:
        self._win32_sighandler = _win32_sighandler
        self._is_daemon = _is_daemon

    def run_parallel(
        self,
        func,
        args: list,
        max_cpus: int = None,
        lock=None,
        message_queue=None,
        message_handler=None,
    ):
        """
        Params:
            func: function that run in multiple processes.
                eg. `func(arg, is_daemon): pass`
            args: run subprocess `func(arg, is_daemon) for arg in args`.
            max_cpus: max cpu cores to use or all the cores if None.
            locker: `multiprocessing.Lock()` using semaphore that can be shared among processes.
                if you need to access a same file or other resources by multiple processes.
            message_queue: `multiprocessing.JoinableQueue()` using Pipe to communicate.
            message_handler: handler msg send from child process, and handle it in parent process.
                `message_queue` and `message_handler` have to be both None or not None.

        """
        if (message_queue is not None and message_handler is None) or (
            message_queue is None and message_handler is not None
        ):
            raise ParamError(
                "message_queue and message_handler have to be None or not None at the same time"
            )
        pool = None
        try:
            if sys.platform == 'win32':
                # 在Linux下用spawn会卡死
                multiprocessing.set_start_method("spawn", force=True)
            # Value 底层使用共享内存，控制子进程退出
            signal_stop = multiprocessing.Value(c_bool, False, lock=False)
            self._set_sighandler_multi_process(signal_stop)
            # lock message_queue signal_stop 可以传入Process，但是不能通过pool.map 参数传入
            # _init_pool_processe 和三个参数一起传入Process，并在子进程中执行_init_pool_processes函数
            pool = multiprocessing.Pool(
                max_cpus, _init_pool_processe, (lock, message_queue, signal_stop)
            )
            mapresult = pool.starmap_async(
                func, [(arg, self._is_daemon) for arg in args]
            )
            while not mapresult.ready():
                try:
                    if message_queue is not None:
                        while True:
                            # raise Empty exception when empty
                            msg = message_queue.get(timeout=0.1)
                            # Linux下，当daemon运行时收到SIGINT时，msg会收到None
                            if msg is not None:
                                message_handler(msg)
                            message_queue.task_done()
                    else:
                        mapresult.wait(0.1)
                except Empty:
                    pass
                except EOFError:  # 当手动Kill子进程会导致该异常
                    break
                except IOError as e:
                    # 当在系统调用时，收到sigint，会报该错误，但是实际并不是错误，直接忽略
                    if e.errno == errno.EINTR:
                        pass
                    else:
                        raise
        except KeyboardInterrupt:
            print("got ^C while pool mapping, terminating the pool")
            if pool is not None:
                pool.terminate()
                print("multiprocessing pool is terminated")
        except Exception as e:
            print("got multiprocessing error: ", str(e))
            if pool is not None:
                pool.terminate()
                print("multiprocessing pool is terminated")
        finally:
            if pool is not None:
                pool.close()

    def set_sighandler_single_process(self, handler):
        """
        如果运行 `run_parallel`, 不要调用该函数。 `run_parallel`内部会自动设置
        信号处理，如何正常退出多进程，请看测试用例

        - windows 单进程 前台：win32_sighandler=None
        - windows 单进程 后台：win32_sighandler!=None
        - linux 单进程 前台：win32_sighandler=None
        - linux 单进程 后台：win32_sighandler=None
        """

        def _sigstop(signum):
            print(f"got signal {signum}, stop process!", flush=True)
            handler()

        def _sigstop_linuxlike(signum, stackframe):
            _sigstop(signum)

        if self._win32_sighandler is None:
            if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
                signal.signal(signal.SIGINT, _sigstop_linuxlike)
            if signal.getsignal(signal.SIGTERM) == signal.SIG_DFL:
                signal.signal(signal.SIGTERM, _sigstop_linuxlike)
        else:
            # Windows daemon环境下
            def __sigstop(signum):
                _sigstop(signum)
                self._win32_sighandler._stop_nowait()

            self._win32_sighandler.sigint = __sigstop
            self._win32_sighandler.sigterm = __sigstop
            self._win32_sighandler.sigabrt = __sigstop

    def _set_sighandler_multi_process(self, signal_stop):
        """
        - windows 多进程 前台：win32_sighandler=None, is_daemon=False
        - windows 多进程 后台：win32_sighandler!=None, is_daemon=True
        - linux 多进程 前台：win32_sighandler=None, is_daemon=False
        - linux 多进程 后台：win32_sighandler=None, is_daemon=True
        """
        if not self._is_daemon:
            # 父进程不需要设置，子进程需要设置。
            # 每个子进程也监听INT信号，INT信号会直接透传到子进程，不需要转发
            # SIGINT设成SIG_IGN，防止触发KeyboardInterrupt错误
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            return
        # 在后台运行
        if self._win32_sighandler is None:  # Linux
            if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
                signal.signal(signal.SIGINT, partial(_parentproc_sigstop1, signal_stop))
            if signal.getsignal(signal.SIGTERM) == signal.SIG_DFL:
                signal.signal(
                    signal.SIGTERM, partial(_parentproc_sigstop1, signal_stop)
                )
        else:  # Windows

            def __sigstop(signum):
                _parentproc_sigstop(signal_stop, signum)
                self._win32_sighandler._stop_nowait()

            self._win32_sighandler.sigint = __sigstop
            self._win32_sighandler.sigterm = __sigstop
            self._win32_sighandler.sigabrt = __sigstop


def _parentproc_sigstop(signal_stop, signum):
    print(f"parent got signal {signum}, stop process!", flush=True)
    signal_stop.value = True


def _parentproc_sigstop1(signal_stop, signum, stackframe):
    _parentproc_sigstop(signal_stop, signum)
