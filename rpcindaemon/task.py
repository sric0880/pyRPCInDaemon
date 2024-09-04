import copy
import json
import os
import random
import socket
import time
from collections import defaultdict
from multiprocessing.connection import Client

import paramiko

from .exceptions import *


class _RPCProxy:
    def __init__(self, address):
        self.address = address
        self._connection = None

    def do_rpc(self, func_name: str, *args, **kwargs):
        if self._connection is None:
            self._connection = Client(self.address)
        self._connection.send((func_name, args, kwargs))
        _try_count = 0
        while True:
            # 第一次调用recv时会报  [Errno 11] Resource temporarily unavailable
            # socket 异步模式下，recv没有取到值会抛该异常
            # 多次尝试
            try:
                result = self._connection.recv()
            except BlockingIOError as e:
                if e.errno == 11:
                    if _try_count > 10:
                        raise e
                    time.sleep(0.2)
                    _try_count += 1
                    continue
                else:
                    raise e
            break
        if isinstance(result, Exception):
            raise result
        return result

    def close(self):
        if self._connection is not None:
            self._connection.close()
        self._connection = None


class Task:

    def __init__(
        self,
        task_id: int,
        cmd: str,
        hostname: str,
        working_dir: str = "",
        py_env_activate: str = "",
        username: str = None,
        password: str = None,
        port: int = -1,
    ):
        """
        remote task over ssh running in remote background. not thread safe so you
        should use different task id. same task id is not allowed running at the same
        time.

        Params:
            task_id: unique task id
            cmd: to executed cammnad
            hostname: remote hostname for ssh
            working_dir: execute `cd $working_dir` on remote before execute cmd
            py_env_activate: activate remote python everionment, eg. conda base, otherwise stay empty.
            username: ssh username
            password: ssh password
            port:
            -1: no tcp connect to remote process
            0: connect to remote process using random port
            >0: connect to remote process using certain port
        """
        if not hostname:
            raise ParamError("hostname cannot be empty")
        if not cmd:
            raise ParamError("cmd cannot be empty")
        if task_id < 0:
            raise ParamError("task_id must be great than 0")
        if working_dir is None:
            raise ParamError("working_dir must not be None")
        self.task_id = task_id
        self.cmd = cmd
        self.hostname = hostname
        self.working_dir = working_dir
        if working_dir:
            self._working_dir = f"cd {working_dir};"
        else:
            self._working_dir = ""
        self.py_env_activate = py_env_activate
        self.username = username
        self.password = password
        if port == 0:
            port = get_available_port(hostname)
        self.port = port
        if port > 0:
            self._client = _RPCProxy((hostname, port))
        else:
            self._client = None
        self.running = False

    def release(self):
        """
        release the socket connection if the task is not used anymore.
        """
        if self._client is not None:
            self._client.close()

    def save(self, dir: str):
        """
        save for future load
        """
        with open(os.path.join(dir, f"taskfile-{self.task_id}.json"), "w") as f:
            d = copy.copy(self.__dict__)
            del d["_working_dir"]
            del d["_client"]
            json.dump(d, f)

    @classmethod
    def restore_from_file(cls, dir: str, task_id: int):
        with open(os.path.join(dir, f"taskfile-{task_id}.json"), "r") as f:
            d = json.load(f)
            running = d.pop("running")
            obj = cls(**d)
            obj.running = running

    def run(self):
        """
        开起远程进程。启动远程进程, 已经启动不再启动。不管启动是否成功，都返回。
        如需知道是否启动成功，请主动轮询
        """
        pid = self.get_pid()
        if pid:
            raise TaskIsRunningError("cannot run a running task")
        _ssh_execute(
            f"{self.py_env_activate} {self._working_dir} {self.cmd}",
            self.hostname,
            self.username,
            self.password,
        )
        self.running = True

    def is_alive(self):
        """
        判断进程是否存在
        """
        return self.get_pid() > 0

    def get_pid(self):
        """
        返回进程id:
            0 - 进程不存在, 也有可能存在，但是因为网络错误
        """
        if not self.running:
            return 0
        if self._client is not None:
            # 通过RPC调用获取进程ID
            pid_or_none = self._client.do_rpc("get_pid")
            return pid_or_none if pid_or_none else 0
        else:
            # 通过ssh读取pidfile文件获取进程ID
            cmd = f"{self.py_env_activate} {self._working_dir} python -m rpcindaemon.entry get-pid {self.task_id}"
            return int(
                _ssh_get(cmd, self.hostname, self.username, self.password, timeout=10)
            )

    def do_rpc(self, func_name, *args, **kwargs):
        """
        与远程进程通信(TCP socket)
        """
        if self._client is not None:
            return self._client.do_rpc(func_name, *args, **kwargs)
        return None

    def terminate(self):
        """
        退出远程进程

        主动轮询是否退出成功
        """
        pid = self.get_pid()
        if not pid:
            raise TaskIsNotRunningError("cannot terminate a task which is not running")
        self.release()
        cmd = f"{self.py_env_activate} {self._working_dir} python -m rpcindaemon.entry term -pids {pid} -ids {self.task_id}"
        _ssh_execute(cmd, self.hostname, self.username, self.password)
        self.running = False


def _ssh_execute(cmd, hostname, username, pwd, timeout=3):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname,
            username=username,
            password=pwd,
            timeout=1,
        )
        _, _, stderr = ssh.exec_command(cmd, timeout=timeout)
        err = stderr.read()
        if err:
            raise SSHExecutionError(f"ssh_execute [{cmd}] error: {err}")
    except socket.timeout:
        raise NetworkTimeoutError(
            f"ssh_execute connect to {username}@{hostname} timeout"
        )
    except:
        raise
    finally:
        try:
            ssh.close()
        except:
            pass


def _ssh_get(cmd, hostname, username, pwd, timeout=3):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname,
            username=username,
            password=pwd,
            timeout=1,
        )
        _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        data = stdout.readlines()
        if data:
            return data[-1].strip()
        else:
            raise SSHExecutionError(f"ssh_get [{cmd}] error: {stderr.read()}")
    except socket.timeout:
        raise NetworkTimeoutError(f"ssh_get connect to {username}@{hostname} timeout")
    except:
        raise
    finally:
        try:
            ssh.close()
        except:
            pass


def get_available_port(hostname: str):
    """
    获取远程机器可用的端口号

    这里有篇文章讲，端口没被占用，但是可能被预留，预留的端口上打开监听，会报`[WinError 10013] `
    https://zhaoji.wang/solve-the-problem-of-windows-10-ports-being-randomly-reserved-occupied-by-hyper-v/

    要选择没有预留的端口作为候选端口，查看被预留的端口命令行：
    `netsh int ipv4 show excludedportrange protocol=tcp`
    """
    while True:
        port = random.randint(50060, 63932)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex((hostname, port)) != 0:
                return port


# def batch_terminate(self, task_ids: list):
#     ''' 批量退出 '''
#     machines = defaultdict(list)
#     for strat in strategy:
#         machine = strat.get_machine()
#         machines[machine].append(strat)
#     for machine, strats in machines.items():
#         sids = []
#         pids = []
#         for strat in strats:
#             pid = self.get_pid(strat)
#             self.close_client(strat.id)
#             if pid:
#                 sids.append(strat.id)
#                 pids.append(pid)
#         if sids and pids:
#             cmd = f'{self.py_env_activate} {self._working_dir} python -m rpcindaemon.entry term -pids {" ".join(pids)} -ids {" ".join(sids)}'
#             try:
#                 self._ssh_execute(cmd, machine)
#             except Exception as e:
#                 pass
#     return True, None
