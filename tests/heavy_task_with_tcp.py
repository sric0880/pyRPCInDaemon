import datetime
import time

import fire

import rpcindaemon


class CustomServerCmd(rpcindaemon.ServerCmd):
    def deal_with_message(self, arg1, arg2, option_arg1=1):
        print("deal_with_message: ", arg1, arg2, option_arg1)

    def deal_with_return(self, arg1, arg2, option_arg1=1):
        print("deal_with_return: ", arg1, arg2, option_arg1)
        return arg1 + arg2 + option_arg1


@rpcindaemon.makedaemon(server_cmd=CustomServerCmd)
def heavy_backgournd_task(task_id: int, f: rpcindaemon.F, arg_live_time=20):
    print(task_id, datetime.datetime.now(), "Start")
    t = 0
    while True:
        if t > arg_live_time:
            break
        time.sleep(0.5)  # will block signal term or signal int
        t += 0.5
    print(task_id, datetime.datetime.now(), "End")


if __name__ == "__main__":
    fire.Fire(heavy_backgournd_task)
