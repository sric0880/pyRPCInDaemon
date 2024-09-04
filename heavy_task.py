import time
import datetime
from rpcindaemon.daemonize import indaemon


@indaemon()
def heavy_backgournd_task():
    print(datetime.datetime.now(), "start")
    time.sleep(10)
    print(datetime.datetime.now(), "end")

if __name__ == "__main__":
    heavy_backgournd_task()