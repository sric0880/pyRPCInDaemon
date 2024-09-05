import pytest

import rpcindaemon


def test_batch_terminate(param):
    t = rpcindaemon.Task(
        20,
        "python heavy_task.py",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"]
    )
    t.run()

    t2 = rpcindaemon.Task(
        21,
        "python heavy_task_with_tcp.py",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
        port=9999
    )
    t2.run()
    assert t.is_alive()
    assert t2.is_alive()

    rpcindaemon.batch_terminate([t, t2], timeout=3)

    assert not t.is_alive()
    assert not t2.is_alive()
