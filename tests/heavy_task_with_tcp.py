import time
import datetime
import fire
import rpcindaemon

class CustomServerCmd(rpcindaemon.ServerCmd):
    def deal_with_message(self, arg1, arg2, option_arg1=1):
        print("receive msg: ", arg1, arg2, option_arg1)

@rpcindaemon.makedaemon(server_cmd=CustomServerCmd)
def heavy_backgournd_task(task_id: int, port: int = 0, arg_sleep_time=10):
    print(task_id, datetime.datetime.now(), "Start")
    time.sleep(arg_sleep_time)
    print(task_id, datetime.datetime.now(), "End")

if __name__ == "__main__":
    fire.Fire(heavy_backgournd_task)