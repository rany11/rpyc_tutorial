import rpyc
import command_handlers
from ErrorMessage import ErrorMessage
import subprocess

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

        self.monitors = dict()  # filepath --> monitor object

        # Background serving thread to the server's requests
        self.bgsrv = rpyc.BgServingThread(self.conn)

        self.created_processes = []
        self.command_handlers = {"upload": command_handlers.CopyFileHandler(self.classic_conn),
                                 "download": command_handlers.CopyFileHandler(self.classic_conn),
                                 "ps": command_handlers.ProcessListHandler(self.classic_conn),
                                 "ls": command_handlers.DirlistHandler(self.classic_conn),
                                 "exec": command_handlers.RunAsNewProcessHandler(self.classic_conn),
                                 "stat": command_handlers.FileStatHandler(self.classic_conn),
                                 "kill": command_handlers.KillProcessHandler(self.classic_conn),
                                 "monitor": command_handlers.MonitorHandler(self.conn),
                                 "rm": command_handlers.RemoveHandler(self.classic_conn)
                                 }

    """
    @returns: the command output (or None if there is no output).
    """
    def execute(self, command, args):
        command_with_args = [command] + args
        original_command_line_input = ' '.join(command_with_args)

        if original_command_line_input == 'kill all':
            self.__kill_all_created_processes()
            return
        elif original_command_line_input == 'monitors':
            return self.__get_monitored_paths()

        if command not in self.command_handlers:
            raise ErrorMessage('Unknown command')

        additional_input = None
        if command.startswith('kill'):
            additional_input = self.created_processes
        elif command.startswith('monitor'):
            additional_input = self.monitors
        terminal_output, manager_output = self.command_handlers[command].handle_command(command_with_args,
                                                                                        additional_input)
        if manager_output:
            if type(manager_output) == subprocess.Popen:
                self.created_processes += [manager_output]
            else:  # it's a monitor
                self.monitors[manager_output.get_monitored_filepath()] = manager_output
        return terminal_output

    def close(self):
        for monitor in self.monitors:
            monitor.stop()
        self.bgsrv.stop()
        self.conn.close()
        self.classic_conn.close()

    def __kill_all_created_processes(self):
        for process in self.created_processes:
            process.kill()
        self.created_processes = []

    def __get_monitored_paths(self):
        return self.monitors.keys()

    def __remove_monitor(self, filepath):
        if filepath in self.monitors:
            self.monitors[filepath].close()
            del self.monitors[filepath]
