import time

import rpcindaemon


def test_simple(param):
    t = rpcindaemon.Task(
        200,
        "python heavy_multiprocess_task.py simple",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()


def test_redirect_stdout_to_file(param):
    t = rpcindaemon.Task(
        201,
        "python heavy_multiprocess_task.py redirect_stdout_to_file",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    while t.is_alive():
        time.sleep(1)


def test_msg_queue(param):
    t = rpcindaemon.Task(
        202,
        "python heavy_multiprocess_task.py msg_queue",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    while t.is_alive():
        time.sleep(1)


def test_lock_and_msg_queue(param):
    t = rpcindaemon.Task(
        203,
        "python heavy_multiprocess_task.py lock_and_msg_queue",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    while t.is_alive():
        time.sleep(1)
