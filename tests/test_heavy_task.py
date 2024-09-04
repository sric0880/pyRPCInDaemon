
import pytest
import time
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
            working_dir=param["working_path"]
        ).run()
    assert 'pidfile-1 exists' in str(pidfileexistserror.value)

    t = rpcindaemon.Task(
        10,
        "python heavy_task.py",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"]
    )
    t.run()
    assert t.is_alive()
    time.sleep(1)
    assert t.is_alive()
    time.sleep(10)
    assert not t.is_alive()
    