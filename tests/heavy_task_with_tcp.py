import time
import datetime
import fire
import rpcindaemon

class CustomServerCmd(rpcindaemon.ServerCmd):
    def deal_with_message(self, arg1, arg2, option_arg1=1):
        print("deal_with_message: ", arg1, arg2, option_arg1)

    def deal_with_return(self, arg1, arg2, option_arg1=1):
        print("deal_with_return: ", arg1, arg2, option_arg1)
        return arg1+arg2+ option_arg1

@rpcindaemon.makedaemon(server_cmd=CustomServerCmd)
def heavy_backgournd_task(task_id: int, arg_sleep_time=10):
    print(task_id, datetime.datetime.now(), "Start")
    time.sleep(arg_sleep_time)
    print(task_id, datetime.datetime.now(), "End")

if __name__ == "__main__":
    fire.Fire(heavy_backgournd_task)