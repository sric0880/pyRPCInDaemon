import time

import pytest

import rpcindaemon


def _test_port(param, task_id, port):
    t = rpcindaemon.Task(
        task_id,
        "python heavy_task_with_tcp.py",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
        port=port
    )
    t.run()
    assert t.is_alive()
    assert t.do_rpc("deal_with_return", 1,23,45) == 69
    assert t.do_rpc("deal_with_return", 1,23,45) == 69
    assert t.do_rpc("deal_with_message", 1,23,45) is None
    time.sleep(15)
    assert not t.is_alive()

    t.run() # run again
    assert t.is_alive()
    time.sleep(1)
    assert t.do_rpc("deal_with_return", 1,23,45) == 69
    assert t.do_rpc("deal_with_return", 1,23,45) == 69
    assert t.do_rpc("deal_with_message", 1,23,45) is None
    t.terminate()
    assert not t.is_alive()


def test_certain_port(param):
    _test_port(param, 11, 9999)

@pytest.mark.skip
def test_random_port(param):
    _test_port(param, 12, 0)
