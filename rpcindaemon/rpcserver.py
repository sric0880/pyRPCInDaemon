import os
import socket
import threading
import typing
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.connection import Listener, Connection, Client

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
        self._thread_pool = ThreadPoolExecutor(max_workers=10)
        self._server = None
        self._stop = False
        self._socket_info = None

    def start(self):
        host = socket.gethostbyname(socket.gethostname())
        self._socket_info = (host, self.port)
        self._server = Listener(self._socket_info)
        self._server_thread = threading.Thread(target=self.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()
        print(f"Start server[RPC] running at {host}:{self.port}")

    def serve_forever(self):
        all_connections = []
        while True:
            try:
                conn = self._server.accept()
                all_connections.append(conn)
                if self._stop:
                    for c in all_connections:
                        c.close()
                    break
                self._thread_pool.submit(_do_recv, conn, self.cmd_cls)
            except Exception as e: # accept error
                print(e)

    def stop(self):
        self._stop = True
        try:
            Client(self._socket_info) # to unblock accept()
        except:
            pass
        if self._server_thread is not None:
            self._server_thread.join()
            self._server_thread = None
        self._thread_pool.shutdown(wait=True)
        if self._server is not None:
            self._server.close()
            self._server = None
        print("Close server[RPC]")

def _do_recv(conn: Connection, cmd_cls: typing.Type[ServerCmd]):
    try:
        while True:
            # Receive a message
            func_name, args, kwargs = conn.recv()
            # Run the RPC and send a response
            try:
                r = cmd_cls(func_name, args, kwargs).execute()
                conn.send(r)
            except Exception as e:
                conn.send(e)
    except EOFError:
        pass
    finally:
        try:
            conn.close()
        except: # maybe close by stop()
            pass
