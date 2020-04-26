import rpyc
from rpyc_client import command_handlers

"""
manages all the handlers.
"""


class CommandHandlersManager(object):
    """
    ip_slave_rpyc, port_slave_rpyc- ip and port of a machine that runs my special SlaveService.
    (my special SlaveService- currently, FileMonitorService)

    __init__ can throw: ConnectionRefusedError
    """

    def __init__(self, ip_slave_rpyc, port_slave_rpyc):
        self.ip_slave_rpyc = ip_slave_rpyc
        self.port_slave_rpyc = port_slave_rpyc

        self.conn = rpyc.connect(ip_slave_rpyc, port=port_slave_rpyc)
        self.classic_conn = rpyc.classic.connect(ip_slave_rpyc, port=port_slave_rpyc)

        self.created_processes = []
        self.command_handler = {"upload": command_handlers.CopyFileHandler(self.classic_conn),
                                "download": command_handlers.CopyFileHandler(self.classic_conn),
                                "ps": command_handlers.ProcessListHandler(self.classic_conn),
                                "ls": command_handlers.DirlistHandler(self.classic_conn),
                                "exec": command_handlers.RunAsNewProcessHandler(self.classic_conn),
                                "stat": command_handlers.FileStatHandler(self.classic_conn),
                                "kill": command_handlers.KillProcessHandler(self.classic_conn)
                                }

        # TODO: initialize it with something.
        # Maybe it won't be a *file* monitor anymore....
        # self.mon = conn.root.FileMonitor(, )

    """
    returns: the command output (or None if not any).
    Commands:
     - get file content (args: path, read_mode)
     - write content to file (args: write mode, pathname, content_to_write)
     - get dirlist (args: pathname)
     - get processlist
     - execute file as new process (args: filepath)
     - kill all created processes (created by the previous command)
     - kill process (args: pid)
     - get file stat (args: filepath)
    """

    def execute(self, command, args):
        if command not in self.command_handler:
            return 'Error: Unknown command'

        command_with_args = [command] + args
        terminal_output, manager_output = self.command_handler[command].handle_command(command_with_args,
                                                                                       self.created_processes)
        if manager_output:  # the only command that produces manager_output is the "exec" command
            self.created_processes += [manager_output]
        return terminal_output

    def close(self):
        self.conn.close()
        self.classic_conn.close()
