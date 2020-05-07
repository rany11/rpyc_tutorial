import sys
from Terminal import Terminal
from CommandHandlersManager import CommandHandlersManager
from server import DEFAULT_PORT

DEFAULT_IP = "localhost"


def get_terminal(ip_server=DEFAULT_IP, port_server=DEFAULT_PORT, is_test_mod=False):
    command_handlers_manager = CommandHandlersManager(ip_server, port_server)
    return Terminal(command_handlers_manager, is_test_mod=is_test_mod)


"""
input: ip_host (default localhost) and port_host (default 18871)
output: gives a client side terminal, that communicates with the server.
"""

if __name__ == "__main__":
    ip_host = DEFAULT_IP if len(sys.argv) <= 1 else sys.argv[1]
    port_host = DEFAULT_PORT if len(sys.argv) <= 2 else sys.argv[2]

    try:
        terminal = get_terminal(ip_host, port_host)
        terminal.start()
    except ConnectionRefusedError:
        print("cannot connect to server {0} on port {1}".format(ip_host, port_host), file=sys.stderr)
