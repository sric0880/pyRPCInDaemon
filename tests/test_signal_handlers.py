import rpcindaemon

# windows 下不能发送SIGINT，无法测试。发送signal.CTRL_C_EVENT会导致测试中断
# 请手动测试，在命令行窗口运行
# `python tests/heavy_task_with_signals.py foreground_multiprocess 100`
# `python tests/heavy_task_with_signals.py foreground_single_process 100`


def test_daemon_multiprocess_signal_quit(param):
    t = rpcindaemon.Task(
        101,
        "python heavy_task_with_signals.py daemon_multiprocess",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )
    t.run()
    t.wait_alive(10)
    assert t.is_alive()

    t.terminate()
    assert not t.is_alive()


def test_daemon_singleprocess_signal_quit(param):
    t = rpcindaemon.Task(
        102,
        "python heavy_task_with_signals.py daemon_single_process",
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

    t.terminate()
    assert not t.is_alive()
