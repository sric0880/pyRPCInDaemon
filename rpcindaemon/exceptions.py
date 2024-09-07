class RPCInDaemonError(Exception):
    pass


class ParamError(RPCInDaemonError):
    pass


class NetworkTimeoutError(RPCInDaemonError):
    pass


class SSHExecutionError(RPCInDaemonError):
    pass


class TaskIsRunningError(RPCInDaemonError):
    pass


class PidfileExistsError(RPCInDaemonError):
    pass


class MethodNotFound(RPCInDaemonError):
    pass


class TaskStartTimeout(RPCInDaemonError):
    pass


class TaskDeadTimeout(RPCInDaemonError):
    pass
