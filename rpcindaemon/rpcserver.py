import datetime
import os
import socket
import threading
import typing
from multiprocessing.connection import Client, Listener, wait

from .exceptions import MethodNotFound

__all__ = ["RpcServer"]


class ServerCmd:
    def __init__(self, cmd_name, cmd_args, cmd_kwargs) -> None:
        self.cmd_name = cmd_name
        self.cmd_args = cmd_args
        self.cmd_kwargs = cmd_kwargs

    def execute(self):
        executor = getattr(self, self.cmd_name, None)
        if executor is None:
            raise MethodNotFound(f"method {self.cmd_name} not found.")
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
        self._stop = False
        self._socket_info = None

    def start(self):
        host = socket.gethostbyname(socket.gethostname())
        self._socket_info = (host, self.port)
        self._server = Listener(self._socket_info)
        self._all_connections = []
        self._server_thread = threading.Thread(target=self.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()
        self._connection_thread = threading.Thread(target=self._do_recv)
        self._connection_thread.daemon = True
        self._connection_thread.start()
        print(f"Start server[RPC] running at {host}:{self.port}")

    def serve_forever(self):
        while True:
            try:
                conn = self._server.accept()
                self._all_connections.append(conn)
                if self._stop:
                    break
            except Exception as e:  # accept error
                print(e)

    def stop(self):
        self._stop = True
        try:
            Client(self._socket_info)  # to unblock accept()
        except:
            pass
        if self._server_thread is not None:
            self._server_thread.join()
            self._server_thread = None
        if self._connection_thread is not None:
            self._connection_thread.join()
            self._connection_thread = None
        for c in self._all_connections:
            c.close()
        if self._server is not None:
            self._server.close()
            self._server = None
        print("Close server[RPC]")

    def _do_recv(self):
        while True:
            if self._stop:
                break
            # FIXME: 在Windows下wait会导致其他线程的IO操作阻塞，严重影响性能
            for c in wait(self._all_connections, timeout=0.1):
                try:
                    # Receive a message
                    func_name, args, kwargs = c.recv()
                except (EOFError, OSError):  # oserror if conn is closed by server side
                    self._all_connections.remove(c)
                else:
                    try:
                        # Run the RPC and send a response
                        r = self.cmd_cls(func_name, args, kwargs).execute()
                        c.send(r)
                    except Exception as e:
                        c.send(e)
