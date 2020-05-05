import rpyc
import command_handlers
from exceptions import ErrorMessage

"""
manages all the command handlers.
Responsible to execute all the commands (using the relevant command handlers).
Can execute some commands by itself, if they don't require communication with the slave server (e.g. monitors).

The commands are:

upload srcpath dstpath
download srcpath dstpath
ps
ls path
exec path args
stat path
kill [-signo] pid
kill all
monitors
monitor path logpath
monitor -r path
rm -r --empty-files path
"""


class CommandHandlersManager(object):
    """
    @:arg ip_slave_rpyc, port_slave_rpyc
     ip and port of a machine that runs my FileMonitorService.
    (FileMonitorService is a SlaveService (inherits from it))

    @throws: ConnectionRefusedError
    """

    def __init__(self, ip_slave_rpyc, port_slave_rpyc):
        self.ip_slave_rpyc = ip_slave_rpyc
        self.port_slave_rpyc = port_slave_rpyc

        # a rpyc connection to the server
        self.conn = rpyc.connect(ip_slave_rpyc, port=port_slave_rpyc)

        # a rpyc classic-connection to the server (as a SlaveServer)
        self.classic_conn = rpyc.classic.connect(ip_slave_rpyc, port=port_slave_rpyc)

        # Background serving thread to the server's requests
        self.bgsrv = rpyc.BgServingThread(self.conn)

        created_processes = []
        monitor_handler = command_handlers.MonitorHandler(self.conn)
        upload_download_handler = command_handlers.CopyFileHandler(self.classic_conn)
        self.command_handlers = {"upload": upload_download_handler,
                                 "download": upload_download_handler,
                                 "ps": command_handlers.ProcessListHandler(self.classic_conn),
                                 "ls": command_handlers.DirlistHandler(self.classic_conn),
                                 "exec": command_handlers.RunAsNewProcessHandler(self.classic_conn, created_processes),
                                 "stat": command_handlers.FileStatHandler(self.classic_conn),
                                 "kill": command_handlers.KillProcessHandler(self.classic_conn, created_processes),
                                 "monitor": monitor_handler,
                                 "monitors": monitor_handler,
                                 "rm": command_handlers.RemoveHandler(self.classic_conn)
                                 }

    """
    @returns: the command output (or None if there is no output).
    """

    def execute(self, command_with_args):
        command = command_with_args[0]
        if command not in self.command_handlers:
            raise ErrorMessage('Unknown command')

        try:
            terminal_output = self.command_handlers[command].execute(command_with_args)
            return terminal_output
        except Exception as e:
            # get just the error message without the stack-trace
            raise ErrorMessage(str(e).split('\n')[0])
        except SystemExit as _:
            raise ErrorMessage("incorrect usage")

    def close(self):
        self.command_handlers['monitor'].close_monitors()
        self.bgsrv.stop()
        self.conn.close()
        self.classic_conn.close()

    """
    def __kill_all_created_processes(self):
        for process in self.created_processes:
            process.kill()
        self.created_processes = []
    """
