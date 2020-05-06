import rpyc
import os
import time
from threading import Thread


class FileMonitorService(rpyc.SlaveService):
    """
    This is a service that is a SlaveService,
    and also supplies the FileMonitor class for monitoring file changes
    """
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
