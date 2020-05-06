from rpyc.utils.server import ThreadedServer
from FileMonitorService import FileMonitorService

DEFAULT_PORT = 18871

if __name__ == "__main__":
    ThreadedServer(FileMonitorService, port=DEFAULT_PORT).start()
