import os
import socket
import threading
import typing
from multiprocessing.connection import Listener

from .exceptions import MethodNotFound

__all__ = ["RpcServer"]


# 输入 只对实盘有用
class ServerCmd:
    """指令"""

    def __init__(self, cmd_name, cmd_args, cmd_kwargs) -> None:
        self.cmd_name = cmd_name
        self.cmd_args = cmd_args
        self.cmd_kwargs = cmd_kwargs

    def execute(self):
        executor = getattr(self, self.cmd_name, None)
        if executor is None:
            raise MethodNotFound(f"method {self.cmd_name} not found.")
        print(f"execute cmd {self}")
        return executor(*self.cmd_args, **self.cmd_kwargs)

    def __str__(self) -> str:
        return f"{self.cmd_name}({self.cmd_args}, {self.cmd_kwargs})"

    def get_pid(self):
        return os.getpid()


class RpcServer:
    def __init__(self, port: int, cmd_cls: typing.Type[ServerCmd]):
        self.port = port
        self.cmd_cls = cmd_cls
        self._server = None
        # 最多接受两个并发连接（一个用于发起者，一个用于监控者）
        self._server_thread_1 = None
        self._server_thread_2 = None

    def start(self):
        host = socket.gethostbyname(socket.gethostname())
        self._server = Listener((host, self.port))
        self._server_thread_1 = threading.Thread(target=self.serve_forever, args=(1,))
        self._server_thread_1.daemon = True
        self._server_thread_1.start()
        self._server_thread_2 = threading.Thread(target=self.serve_forever, args=(2,))
        self._server_thread_2.daemon = True
        self._server_thread_2.start()
        print(f"Start server[RPC] running at {host}:{self.port}")

    def serve_forever(self, tid):
        try:
            while True:
                with self._server.accept() as conn:
                    print(f"connected {tid}")
                    try:
                        while True:
                            # Receive a message
                            func_name, args, kwargs = conn.recv()
                            # Run the RPC and send a response
                            try:
                                r = self.cmd_cls(func_name, args, kwargs).execute()
                                conn.send(r)
                            except Exception as e:
                                conn.send(e)
                    except EOFError:
                        pass
                    print(f"disconnected {tid}")
        except:  # accept error
            pass

    def stop(self):
        if self._server is not None:
            self._server.close()
        if self._server_thread_1 is not None:
            self._server_thread_1.join()
        if self._server_thread_2 is not None:
            self._server_thread_2.join()
        print("Close server[RPC].")
