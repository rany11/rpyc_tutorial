import rpyc
import os
import time
from threading import Thread
import shutil


class FileMonitorService(rpyc.SlaveService):
    """
    This is a service that is a SlaveService,
    and also supplies the FileMonitor class for monitoring file changes
    """

    def __init__(self):
        super().__init__()
        self.__working_dir = "working_dir"
        self.__connection_num = 0

    def on_connect(self, conn):
        if self.__connection_num == 0:
            os.mkdir(self.__working_dir)
            os.chdir(self.__working_dir)
        self.__connection_num += 1

        super().on_connect(conn)

    def on_disconnect(self, conn):
        super().on_disconnect(conn)
        self.__connection_num -= 1
        if self.__connection_num == 0:
            os.chdir("..")
            shutil.rmtree(self.__working_dir, ignore_errors=True)

    class FileMonitor(object):
        """
        This class monitors changes in a given file.
        Upon change the client's callback is called.
        """

        def __init__(self, filename, callback, interval=1):
            self.filename = filename
            self.interval = interval
            self.last_stat = None

            # create an async callback. FileMonitor just notifies on the file change. Doesn't need to wait for an answer
            self.callback = rpyc.async_(callback)
            self.active = True
            self.thread = Thread(target=self.__work)
            self.thread.start()

        def stop(self):
            self.active = False
            self.thread.join()

        def __work(self):
            while self.active:
                stat = os.stat(self.filename)
                if self.last_stat is not None and self.last_stat != stat:
                    self.callback(self.last_stat, stat)  # notify the client of the change
                self.last_stat = stat
                time.sleep(self.interval)

        def get_monitored_filepath(self):
            return self.filename
