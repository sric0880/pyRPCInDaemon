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
        port=port,
    )
    t.run()
    t.wait_alive(10)
    assert t.is_alive()
    with pytest.raises(rpcindaemon.MethodNotFound):
        t.do_rpc("deal_not_found")
    assert t.do_rpc("deal_with_return", 1, 23, 45) == 69
    assert t.do_rpc("deal_with_message", 1, 23, 45) is None
    time.sleep(25)
    assert not t.is_alive()

    t.run()  # run again
    t.wait_alive(10)
    assert t.is_alive()
    time.sleep(1)
    assert t.do_rpc("deal_with_return", 1, 23, 45) == 69
    assert t.do_rpc("deal_with_return", 1, 23, 45) == 69
    assert t.do_rpc("deal_with_message", 1, 23, 45) is None
    t.terminate()
    assert not t.is_alive()


def test_certain_port(param):
    _test_port(param, 11, 9999)


# 如果是云服务器，那么接口不是随便暴露的，要设置安全组
# 才能访问对应接口，所以用不了随机接口。
# @pytest.mark.skip
def test_random_port(param):
    _test_port(param, 12, 0)


def test_save_and_restore(param):
    t = rpcindaemon.Task(
        13,
        "python heavy_task_with_tcp.py --arg-sleep-time=40",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
        port=9999,
    )
    t.run()
    t.wait_alive(10)
    assert t.is_alive()
    assert t.do_rpc("deal_with_return", 1, 23, 45) == 69

    t.save(".")

    t2 = rpcindaemon.Task.restore_from_file(".", 13)
    assert t2.is_alive()
    assert t2.do_rpc("deal_with_return", 1, 23, 45) == 69

    assert t2.get_pid() == t.get_pid()

    t2.terminate()
    assert not t2.is_alive()
    assert not t.is_alive()
