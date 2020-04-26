# Run this as python -m rpyc_slave.slave_server

from rpyc.utils.server import ThreadedServer
# import sys
#
# sys.path.append(r'C:\Users\ranyeheskel\Desktop\Training\rpyc\rpyc_slave')
from rpyc_slave import FileMonitorService

# TODO: wtf is wrong with this?
if __name__ == "__main__":
    ThreadedServer(FileMonitorService, port=18871).start()
    # exec(open("C:\\Users\\ranyeheskel\\AppData\\Local\\Continuum\\anaconda3\\Scripts\\rpyc_classic.py").read())
