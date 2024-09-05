import sys

import paramiko
import pytest

import rpcindaemon

not_exists_hostname = "192.168.2.202"
wrong_user = "wrong-user"
wrong_pwd = "wrong-pwd"


@pytest.mark.skip
def test_exceptions(param):
    with pytest.raises(rpcindaemon.ParamError) as e:
        rpcindaemon.Task(0, "echo hello", "").run()

    with pytest.raises(rpcindaemon.ParamError) as e:
        rpcindaemon.Task(0, "", param["hostname"]).run()

    with pytest.raises(rpcindaemon.ParamError) as e:
        rpcindaemon.Task(-1, "echo hello", param["hostname"]).run()

    with pytest.raises(paramiko.ssh_exception.AuthenticationException) as e:
        rpcindaemon.Task(0, "echo hello", param["hostname"]).run()

    with pytest.raises(paramiko.ssh_exception.AuthenticationException) as e:
        rpcindaemon.Task(
            0,
            "echo hello",
            param["hostname"],
            username=param["user"],
            password=wrong_pwd,
        ).run()

    with pytest.raises(paramiko.ssh_exception.AuthenticationException) as e:
        rpcindaemon.Task(
            0,
            "echo hello",
            param["hostname"],
            username=wrong_user,
            password=param["pwd"],
        ).run()

    with pytest.raises(rpcindaemon.NetworkTimeoutError) as e:
        rpcindaemon.Task(
            0,
            "echo hello",
            not_exists_hostname,
            username=param["user"],
            password=param["pwd"],
        ).run()


@pytest.fixture
def exist_pid():
    return 4 if sys.platform == "win32" else 1

@pytest.mark.skip
def test_get_pid(param, exist_pid):
    t = rpcindaemon.Task(
        0,
        "echo hello",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
    )
    t.running = True
    assert t.get_pid() == 0

    t = rpcindaemon.Task(
        999999,
        "echo hello",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.running = True
    assert t.get_pid() == 0

    t = rpcindaemon.Task(
        exist_pid,
        "echo hello",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.running = True
    assert t.get_pid() == exist_pid


def test_simple_run(param):
    rpcindaemon.Task(
        0,
        "echo hello",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
    ).run()
