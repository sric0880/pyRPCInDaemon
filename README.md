# pyRPCInDaemon

## Install

```sh
pip install .
```

## Usage

These are more use cases in tests folder.

### TCP server based task

```python
import rpcindaemon

task_id = 1000
cmd = "python heavy_task.py --arg-live-time=40"
port = 9999 # optional
t = rpcindaemon.Task(
    task_id,
    cmd,
    ssh_config["hostname"],
    username=ssh_config["user"],
    password=ssh_config["pwd"],
    port=port,
)
```

in `heavy_task.py`

```python
import fire
import rpcindaemon

class CustomServerCmd(rpcindaemon.ServerCmd):
    def add(self, arg1, arg2=1):
        return arg1 + arg2

@rpcindaemon.makedaemon(server_cmd=CustomServerCmd)
def heavy_backgournd_task(task_id: int, f: rpcindaemon.F, arg_live_time=20):
    t = 0
    while True:
        if t > arg_live_time:
            break
        time.sleep(0.5)
        t += 0.5

if __name__ == "__main__":
    fire.Fire(heavy_backgournd_task)
```

then you can send do `add` from remote task

```python
assert t.do_rpc("add", 1, 2) == 3
assert t.do_rpc("add", 1) == 2
```

or you can generate multiple processes in daemon task

```python
import time
import rpcindaemon
import multiprocessing

def child_process(a, is_daemon):
    msg_queue = rpcindaemon.daemonize.message_queue
    lock = rpcindaemon.daemonize.lock
    with lock:
        msg_queue.put(f"{a}: send message to parent process")
        time.sleep(1)

@rpcindaemon.makedaemon()
def heavy_multiprocess_task(task_id: int, f: rpcindaemon.F, max_cpus=None):
    def msg_handler(msg):
        print(msg)
    args = list(range(20))
    f.run_parallel(
        child_process,
        args,
        max_cpus=max_cpus,
        lock=multiprocessing.Lock(),
        message_queue=multiprocessing.JoinableQueue(),
        message_handler=msg_handler,
    )

if __name__ == "__main__":
    fire.Fire(heavy_multiprocess_task)
```

you can terminate remote daemon task(process) whenever you want. you can setup your own signal handlers for quiting gracefully.

```python
t.terminate()
```

## Third-party library

- [daemoniker](https://pypi.org/project/daemoniker) with a little modification of the source code
