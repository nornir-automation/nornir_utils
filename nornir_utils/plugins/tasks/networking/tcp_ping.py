import socket
from typing import Optional, List

from nornir.core.task import Result, Task


def tcp_ping(
    task: Task, ports: List[int], timeout: int = 2, host: Optional[str] = None, ipv6: bool = False
) -> Result:
    """
    Tests connection to a tcp port and tries to establish a three way
    handshake. To be used for network discovery or testing.

    Arguments:
        ports (list of int): tcp ports to ping
        timeout (int, optional): defaults to 2
        host (string, optional): defaults to ``hostname``
        ipv6 (bool): use ipv6 socket. defaults to ``False``


    Returns:
        Result object with the following attributes set:
          * result (``dict``): Contains port numbers as keys with True/False as values
    """

    if isinstance(ports, int):
        ports = [ports]

    if isinstance(ports, list):
        if not all(isinstance(port, int) for port in ports):
            raise ValueError("Invalid value for 'ports'")

    else:
        raise ValueError("Invalid value for 'ports'")

    host = host or task.host.hostname

    result = {}
    for port in ports:
        if ipv6:
            s = socket.socket(socket.AF_INET6)
        else:
            s = socket.socket()
        s.settimeout(timeout)
        try:
            status = s.connect_ex((host, port))
            if status == 0:
                connection = True
            else:
                connection = False
        except (socket.gaierror, socket.timeout, socket.error):
            connection = False
        finally:
            s.close()
        result[port] = connection

    return Result(host=task.host, result=result)
