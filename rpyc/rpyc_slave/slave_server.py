# Run this as python -m rpyc_slave.slave_server

from rpyc.utils.server import ThreadedServer
import rpyc_slave.FileMonitorService

"""
Executes the slave server
"""
if __name__ == "__main__":
    ThreadedServer(rpyc_slave.FileMonitorService, port=18871).start()
    # exec(open("C:\\Users\\ranyeheskel\\AppData\\Local\\Continuum\\anaconda3\\Scripts\\rpyc_classic.py").read())
