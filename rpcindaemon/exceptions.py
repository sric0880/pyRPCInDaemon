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


class TaskIsNotRunningError(RPCInDaemonError):
    pass


class ParamTaskIdMissing(ParamError):
    pass


class PidfileExistsError(RPCInDaemonError):
    pass