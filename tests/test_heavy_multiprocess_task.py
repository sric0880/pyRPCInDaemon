import time

import pytest

import rpcindaemon


def test_heavy_task(param):
    t = rpcindaemon.Task(
        10,
        "python heavy_multiprocess_task.py",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    assert t.is_alive()
    time.sleep(1)
    assert t.is_alive()
    time.sleep(10)
    assert not t.is_alive()

    t.run()  # run again
    assert t.is_alive()
    cur_pid = t.get_pid()
    time.sleep(1)
    with pytest.raises(rpcindaemon.TaskIsRunningError):
        t.run()  # run again with no effects
    assert t.get_pid() == cur_pid
    t.terminate()
    assert not t.is_alive()
    t.terminate()  # doing nothing
