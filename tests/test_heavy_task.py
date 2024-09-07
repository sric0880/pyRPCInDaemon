import time

import pytest

import rpcindaemon


def test_heavy_task(param):
    with pytest.raises(rpcindaemon.SSHExecutionError) as pidfileexistserror:
        rpcindaemon.Task(
            1,
            "python heavy_task.py",
            param["hostname"],
            username=param["user"],
            password=param["pwd"],
            py_env_activate=param["py_env_activate"],
            working_dir=param["working_path"],
        ).run()
    assert "pidfile-1 exists" in str(pidfileexistserror.value)

    t = rpcindaemon.Task(
        10,
        "python heavy_task.py --arg-sleep-time=40",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    t.wait_alive(10)
    assert t.is_alive()
    time.sleep(40)
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


def test_save_and_restore(param):
    t = rpcindaemon.Task(
        10,
        "python heavy_task.py --arg-sleep-time=40",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    t.wait_alive(10)
    assert t.is_alive()

    t.save(".")

    t2 = rpcindaemon.Task.restore_from_file(".", 10)
    assert t2.is_alive()

    assert t2.get_pid() == t.get_pid()

    t2.terminate()
    assert not t2.is_alive()
    assert not t.is_alive()
