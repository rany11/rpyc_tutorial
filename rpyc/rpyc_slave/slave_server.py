from rpyc.utils.server import ThreadedServer
from rpyc_slave.FileMonitorService import FileMonitorService

DEFAULT_PORT = 18871

"""
Executes the slave server.
Run this as (from the rpyc project's root directory):
python -m rpyc_slave.slave_server
"""
if __name__ == "__main__":
    ThreadedServer(FileMonitorService, port=DEFAULT_PORT).start()
