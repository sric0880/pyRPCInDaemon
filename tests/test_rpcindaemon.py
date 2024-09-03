import sys

import paramiko
import pytest

import rpcindaemon

not_exists_hostname = "192.168.2.202"
wrong_user = "wrong-user"
wrong_pwd = "wrong-pwd"


@pytest.fixture
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


def test_get_pid(param, exist_pid):
    assert (
        rpcindaemon.Task(
            0,
            "echo hello",
            param["hostname"],
            username=param["user"],
            password=param["pwd"],
            py_env_activate=param["py_env_activate"],
        ).get_pid()
        == 0
    )

    assert (
        rpcindaemon.Task(
            999999,
            "echo hello",
            param["hostname"],
            username=param["user"],
            password=param["pwd"],
            py_env_activate=param["py_env_activate"],
            working_dir=param["working_path"],
        ).get_pid()
        == 0
    )

    assert (
        rpcindaemon.Task(
            exist_pid,
            "echo hello",
            param["hostname"],
            username=param["user"],
            password=param["pwd"],
            py_env_activate=param["py_env_activate"],
            working_dir=param["working_path"],
        ).get_pid()
        == exist_pid
    )


def test_save_and_restore():
    pass
