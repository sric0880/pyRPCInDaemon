from concurrent.futures import ThreadPoolExecutor, as_completed

import rpcindaemon


def test_batch_terminate(param):
    t = rpcindaemon.Task(
        20,
        "python heavy_task.py --arg_live_time=30",  # longer in case to keep alive before run terminate
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
    )

    t2 = rpcindaemon.Task(
        21,
        "python heavy_task_with_tcp.py --arg_live_time=30",
        param["hostname"],
        username=param["user"],
        password=param["pwd"],
        py_env_activate=param["py_env_activate"],
        working_dir=param["working_path"],
        port=9999,
    )
    pool = ThreadPoolExecutor(2)
    f = pool.submit(t.run)
    f2 = pool.submit(t2.run)
    # 如果这么写，f f2可能还没运行完就退出了
    # 也是很诡异, t.running=False
    # for _ in as_completed([f, f2]):
    #     pass
    for d in as_completed([f, f2]):
        d.result()
    assert t.running
    assert t2.running

    t.wait_alive(20)
    t2.wait_alive(20)
    assert t2.is_alive()
    assert t.is_alive()

    rpcindaemon.batch_terminate([t, t2])

    assert not t.is_alive()
    assert not t2.is_alive()
