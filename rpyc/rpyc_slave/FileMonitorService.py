import rpyc
import os
import time
from threading import Thread


# The fact that we inherit from rpyc.SlaveService makes the exposed_ prefix not to work.
# i.e., if we'd inherit from rpyc.Service using the exposed_ prefix would have worked.
class FileMonitorService(rpyc.SlaveService):
    class FileMonitor(object):
        def __init__(self, filename, callback, interval=1):
            self.filename = filename
            self.interval = interval
            self.last_stat = None
            self.callback = rpyc.async_(callback)  # create an async callback
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
