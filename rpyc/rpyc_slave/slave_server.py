import sys
import os

sys.path.append(os.getcwd())

from rpyc.utils.server import ThreadedServer
from rpyc_slave.FileMonitorService import FileMonitorService

"""
Executes the slave server.
Run this as (from the rpyc project's root directory):
python -m rpyc_slave.slave_server
"""
if __name__ == "__main__":
    ThreadedServer(FileMonitorService, port=18871).start()
    # exec(open("C:\\Users\\ranyeheskel\\AppData\\Local\\Continuum\\anaconda3\\Scripts\\rpyc_classic.py").read())
