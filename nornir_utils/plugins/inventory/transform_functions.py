import os
from nornir.core.inventory import Host


def load_credentials(host: Host, username: str = None, password: str = None) -> None:
    """
    load_credentials is an transform_functions to add credentials to every host.
    Environment variables `NORNIR_USERNAME` and `NORNIR_PASSWORD` or arguments can be used.

    Args:

        username: Device username
        password: Device password
    """
    username = username if username else os.getenv("NORNIR_USERNAME")
    if username:
        host.username = username
    password = password if password else os.getenv("NORNIR_PASSWORD")
    if password:
        host.password = password
