import argparse
import signal
import sys

import psutil


def terminate_proc(pids, strategy_ids):
    if sys.platform == "win32":
        from rpcindaemon.daemoniker import SIGINT, send

        try:
            for sid in strategy_ids:
                # Send a SIGINT to a process denoted by a PID file
                send(f"pidfile-{sid}", SIGINT)
            return True
        except Exception as e:
            print(str(e))
            return False
    elif sys.platform == "linux":
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


def get_pid(strategy_id):
    """从进程文件读取pid并判断pid是否活跃"""
    try:
        with open(f"pidfile-{strategy_id}", "r") as f:
            pid = int(f.read().strip())
        return pid if psutil.pid_exists(pid) else 0
    except:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(title="子任务", required=True, dest="cmd")

    cmd1_parser = commands.add_parser("term")
    cmd1_parser.add_argument(
        "-pids",
        nargs="+",
        type=int,
        required=True,
        help="pid进程ID列表，" "分隔。Linux必填，Windows可填0",
    )
    cmd1_parser.add_argument(
        "-ids",
        nargs="+",
        type=int,
        required=True,
        help="策略ID列表，" "分隔。Windows必填，Linux可填0",
    )

    cmd2_parser = commands.add_parser("get-pid")
    cmd2_parser.add_argument("taskid", help="task id")

    args = parser.parse_args()
    cmd = args.cmd
    if cmd == "term":
        terminate_proc(args.pids, args.ids)
    elif cmd == "get-pid":
        print(get_pid(args.taskid))
