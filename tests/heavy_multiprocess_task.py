import datetime
import multiprocessing
import signal
import sys
import time

import fire

import rpcindaemon


def simple(a, is_daemon):
    time.sleep(0.5)


def redirect_stdout_to_file(a, is_daemon):
    if is_daemon:
        # 后台运行要将标准输出写入文件
        stdout_file = f"pidfile-child-{a}.log"
        sys.stderr = sys.stdout = open(stdout_file, "w")
    time.sleep(0.5)
    print("test redirect_stdout_to_file end.", flush=True)


def msg_queue(a, is_daemon):
    msg_queue = rpcindaemon.daemonize.message_queue
    msg_queue.put(f"deal with {a} start")
    time.sleep(0.5)
    msg_queue.put(f"deal with {a} over")


def msg_handler(msg):
    print(msg)


def lock_and_msg_queue(a, is_daemon):
    msg_queue = rpcindaemon.daemonize.message_queue
    lock = rpcindaemon.daemonize.lock
    with lock:
        msg_queue.put(f"deal with {a} start")
        time.sleep(0.5)
        msg_queue.put(f"deal with {a} over")


def stop_signal_and_msg_queue(a, is_daemon):
    # msg_queue = rpcindaemon.daemonize.message_queue
    if not is_daemon:
        print("ssssssssssssssss")

        signal_stop = False

        def _sighandler(signum, stackframe):
            print(f"{a} child got signal {signum}, quit process", flush=True)
            nonlocal signal_stop
            signal_stop = True

        signal.signal(signal.SIGINT, _sighandler)
        signal.signal(signal.SIGTERM, _sighandler)

        while True:
            if signal_stop:
                break
            time.sleep(0.1)
    # else:
    #     signal_stop = rpcindaemon.daemonize.signal_stop
    #     while True:
    #         if signal_stop:
    #             msg_queue.put(f"{a} child got signal stop, quit process")
    #             break
    #         time.sleep(0.1)


@rpcindaemon.makedaemon()
def heavy_multiprocess_task01(task_id: int, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    rpcindaemon.run_parallel(simple, args, max_cpus=max_cpus)
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.makedaemon()
def heavy_multiprocess_task02(task_id: int, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    rpcindaemon.run_parallel(redirect_stdout_to_file, args, max_cpus=max_cpus)
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.makedaemon()
def heavy_multiprocess_task03(task_id: int, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    rpcindaemon.run_parallel(
        msg_queue,
        args,
        max_cpus=max_cpus,
        message_queue=multiprocessing.JoinableQueue(),
        message_handler=msg_handler,
    )
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.makedaemon()
def heavy_multiprocess_task04(task_id: int, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    rpcindaemon.run_parallel(
        lock_and_msg_queue,
        args,
        max_cpus=max_cpus,
        lock=multiprocessing.Lock(),
        message_queue=multiprocessing.JoinableQueue(),
        message_handler=msg_handler,
    )
    print(task_id, datetime.datetime.now(), "End")


@rpcindaemon.nodaemon()
def heavy_multiprocess_task05(task_id: int, max_cpus=None):
    print(task_id, datetime.datetime.now(), "Start")
    args = list(range(20))
    rpcindaemon.run_parallel(
        stop_signal_and_msg_queue,
        args,
        max_cpus=max_cpus,
        message_queue=multiprocessing.JoinableQueue(),
        message_handler=msg_handler,
    )
    print(task_id, datetime.datetime.now(), "End")


if __name__ == "__main__":
    fire.Fire(
        {
            "simple": heavy_multiprocess_task01,
            "redirect_stdout_to_file": heavy_multiprocess_task02,
            "msg_queue": heavy_multiprocess_task03,
            "lock_and_msg_queue": heavy_multiprocess_task04,
            "stop_signal_and_msg_queue": heavy_multiprocess_task05,
        }
    )
