import sys
sys.path.append(r'C:\Users\ranyeheskel\Desktop\Training\rpyc\rpyc_client')
from rpyc_client.CommandHandlersManager import CommandHandlersManager
from rpyc_client.Terminal import Terminal

if __name__ == "__main__":
    ip_host = "localhost" if len(sys.argv) <= 1 else sys.argv[1]
    port_host = 18812 if len(sys.argv) <= 2 else sys.argv[2]

    try:
        command_handlers_manager = CommandHandlersManager(ip_host, port_host)
        terminal = Terminal(command_handlers_manager)
        terminal.start()

    except ConnectionRefusedError:
        print("cannot connect to slave host {0} on port {1}".format(ip_host, port_host), file=sys.stderr)







