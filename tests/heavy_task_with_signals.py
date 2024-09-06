import datetime
import multiprocessing
import signal
import time

import fire

import rpcindaemon


def msg_handler(msg):
    print(msg)


def child_subprocess(a, is_daemon):
    if not is_daemon:
        # 子进程中的前台任务，需要自己手动设置signal handler
        signal_stop = False

        def _sighandler(signum, stackframe):
            print(f"{a} child got signal {signum}, quit process.", flush=True)
            nonlocal signal_stop
            signal_stop = True

        signal.signal(signal.SIGINT, _sighandler)
        signal.signal(signal.SIGTERM, _sighandler)

        while True:
            if signal_stop:
                break
            time.sleep(0.1)
    else:
        signal_stop = rpcindaemon.daemonize.signal_stop
        msg_queue = rpcindaemon.daemonize.message_queue
        while True:
            if signal_stop:
                msg_queue.put(f"{a} child got signal stop, quit process.")
                break
            time.sleep(0.1)


def single_process(task_id, f):
    print(task_id, datetime.datetime.now(), "Start")

    signal_stop = False

    def _sighandler():
        nonlocal signal_stop
        signal_stop = True

    f.set_sighandler_single_process(_sighandler)

    while True:
        if signal_stop:
            break
        time.sleep(0.1)
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.nodaemon
def heavy_multiprocess_foreground_task(task_id: int, f: rpcindaemon.F, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    f.run_parallel(
        child_subprocess,
        args,
        max_cpus=max_cpus,
        message_queue=multiprocessing.JoinableQueue(),
        message_handler=msg_handler,
    )
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.nodaemon
def heavy_singleprocess_foreground_task(task_id: int, f: rpcindaemon.F):
    single_process(task_id, f)


@rpcindaemon.makedaemon()
def heavy_multiprocess_daemon_task(task_id: int, f: rpcindaemon.F, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    f.run_parallel(
        child_subprocess,
        args,
        max_cpus=max_cpus,
        message_queue=multiprocessing.JoinableQueue(),
        message_handler=msg_handler,
    )
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.makedaemon()
def heavy_singleprocess_daemon_task(task_id: int, f: rpcindaemon.F):
    single_process(task_id, f)


if __name__ == "__main__":
    fire.Fire(
        {
            "foreground_multiprocess": heavy_multiprocess_foreground_task,
            "foreground_single_process": heavy_singleprocess_foreground_task,
            "daemon_multiprocess": heavy_multiprocess_daemon_task,
            "daemon_single_process": heavy_singleprocess_daemon_task,
        }
    )
