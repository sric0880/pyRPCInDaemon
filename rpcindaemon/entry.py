import signal
import sys
from typing import List

import fire
import psutil

from .exceptions import ParamError


def terminate_proc(pids: List[int]=[], task_ids: List[int]=[]):
    """
    terminate processes by pids or task-ids

    params:
        pids: list of process ids to terminate, using on Linux.
        task_ids: list of task ids to terminate task, using on Windows.
    """
    if sys.platform == "win32":
        if not task_ids:
            raise ParamError("terminate_proc on windows need --task-ids=[tid,...] options")
        from rpcindaemon.daemoniker import SIGINT, send

        try:
            for tid in task_ids:
                # Send a SIGINT to a process denoted by a PID file
                send(f"pidfile-{tid}", SIGINT)
            return True
        except Exception as e:
            print(str(e))
            return False
    else:
        if not pids:
            raise ParamError("terminate_proc on linux need --task-ids=[pid,...] options")
        try:
            wait_procs = []
            for _pid in pids:
                p = psutil.Process(_pid)
                p.send_signal(signal.SIGINT)
                wait_procs.append(p)
            gone, alive = psutil.wait_procs(wait_procs, timeout=10)
            for p in alive:
                p.kill()
                p.parent().send_signal(signal.SIGCHLD)
            return True
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            return False


def get_pid(task_id: int):
    """read pid from pidfile, return 0 if process is dead"""
    try:
        with open(f"pidfile-{task_id}", "r") as f:
            pid = int(f.read().strip())
        return pid if psutil.pid_exists(pid) else 0
    except:
        return 0


if __name__ == "__main__":
    fire.Fire({
        "terminate_proc": terminate_proc,
        "get_pid": get_pid,
    })
