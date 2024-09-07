import rpcindaemon


def test_simple_run(param):
    rpcindaemon.Task(
        0,
        "echo hello",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
    ).run()


import cProfile
import pstats
from pstats import SortKey

pr = cProfile.Profile()
pr.enable()

test_simple_run(
    {
        "hostname": "192.168.2.9",
        "user": "admin",
        "pwd": "",
        "py_env_activate": "eval \"$('/c/ProgramData/Anaconda3/Scripts/conda.exe' 'shell.bash' 'hook')\"; conda activate base;",
        "working_path": "D:/lzq/pyRPCInDaemon/tests",
    }
)
pr.disable()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr).sort_stats(sortby)
ps.print_stats()
