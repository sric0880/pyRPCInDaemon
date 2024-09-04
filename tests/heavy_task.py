import time
import rpcindaemon


@rpcindaemon.makedaemon()
def heavy_backgournd_task():
    time.sleep(10)

if __name__ == "__main__":
    heavy_backgournd_task()