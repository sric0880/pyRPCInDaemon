import time
import datetime
import fire
import rpcindaemon


@rpcindaemon.makedaemon()
def heavy_backgournd_task(task_id, arg_sleep_time=10):
    print(task_id, datetime.datetime.now(), "Start")
    time.sleep(arg_sleep_time)
    print(task_id, datetime.datetime.now(), "End")

if __name__ == "__main__":
    fire.Fire(heavy_backgournd_task)