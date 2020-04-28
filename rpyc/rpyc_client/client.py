import sys
import os

sys.path.append(os.getcwd())
from rpyc_client.Terminal import Terminal

"""
input: ip_host (default localhost) and port_host (default 18871)
output: gives a client side terminal, that communicates with the server.
"""

if __name__ == "__main__":
    ip_host = "localhost" if len(sys.argv) <= 1 else sys.argv[1]
    port_host = 18871 if len(sys.argv) <= 2 else sys.argv[2]

    try:
        Terminal(ip_host, port_host).start()
    except ConnectionRefusedError:
        print("cannot connect to slave host {0} on port {1}".format(ip_host, port_host), file=sys.stderr)
