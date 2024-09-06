import datetime
import time

import fire

import rpcindaemon


@rpcindaemon.makedaemon()
def heavy_backgournd_task(task_id: int, f: rpcindaemon.F, arg_sleep_time=10):
    print(task_id, datetime.datetime.now(), "Start")
    t = 0
    while True:
        if t > arg_sleep_time:
            break
        time.sleep(0.5)  # will block signal term or signal int
        t += 0.5
    print(task_id, datetime.datetime.now(), "End")


if __name__ == "__main__":
    fire.Fire(heavy_backgournd_task)
