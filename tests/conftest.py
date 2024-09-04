import sys

import pytest


@pytest.fixture(scope="module")
def param():
    # TODO to change to your own config
    if sys.platform == "win32":
        return {
            "hostname": "192.168.2.9",
            "user": "admin",
            "pwd": "xxxxxxxx",
            "py_env_activate": "eval \"$('/c/ProgramData/Anaconda3/Scripts/conda.exe' 'shell.bash' 'hook')\"; conda activate base;",
            "working_path": "D:/lzq/pyRPCInDaemon/tests",
        }
    else:
        return {
            "hostname": "",
            "user": "root",
            "pwd": "",
            "py_env_activate": "",
            "working_path": "/root/pyRPCInDaemon/tests",
        }