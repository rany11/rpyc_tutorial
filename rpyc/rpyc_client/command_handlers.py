import psutil
import datetime

"""
All the command handlers.
They parse, execute and return output (if any) to the terminal. 
"""


# TODO: make better parsing, a lot of code duplication. Also spaces in paths are not supported.

class CommandHandler(object):
    def __init__(self, rpyc_conn):
        self.rpyc_conn = rpyc_conn

    def execute(self, command_with_arguments):
        raise NotImplementedError()


class CopyFileHandler(CommandHandler):
    def execute(self, command_with_arguments):
        srcpath, dstpath = self.__parse_input(command_with_arguments)
        if command_with_arguments[0] == 'upload':
            return self.__execute_upload(srcpath, dstpath)
        return self.__execute_download(srcpath, dstpath)

    def __parse_input(self, command_with_arguments):
        if len(command_with_arguments) != 3:
            raise TypeError('Expecting 2 arguments')
        return command_with_arguments[1], command_with_arguments[2]

    def __execute_upload(self, srcpath, dstpath):
        with open(srcpath, 'rb') as src:
            with self.rpyc_conn.builtin.open(dstpath, "wb") as dst:
                self.__copy_file(src, dst)

    def __execute_download(self, srcpath, dstpath):
        with self.rpyc_conn.builtin.open(srcpath, 'rb') as src:
            with open(dstpath, "wb") as dst:
                self.__copy_file(src, dst)

    def __copy_file(self, src_file_handler, dst_file_handler, chunk_size=2 ** 14):
        while True:
            buf = src_file_handler.read(chunk_size)
            if not buf:
                break
            dst_file_handler.write(buf)


class DirlistHandler(CommandHandler):
    def execute(self, command_with_arguments):
        path = self.__parse_input(command_with_arguments)
        remote_os = self.rpyc_conn.modules.os
        return remote_os.listdir(path)

    def __parse_input(self, command_with_arguments):
        if len(command_with_arguments) != 2:
            raise TypeError('expecting one argument')
        return command_with_arguments[1]


class ProcessListHandler(CommandHandler):
    def execute(self, command_with_arguments):
        if len(command_with_arguments) != 1:
            raise TypeError('not expecting any arguments')

        remote_psutil = self.rpyc_conn.modules.psutil
        process_list = []
        for proc in remote_psutil.process_iter():
            try:
                # Get process name & pid from process object.
                process_name = proc.name()
                process_id = proc.pid
                process_list += [{'name': process_name, 'pid': process_id}]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass  # we can't access these processes

        return process_list


class FileStatHandler(CommandHandler):
    def execute(self, command_with_arguments):
        path = self.__parse_input(command_with_arguments)
        remote_os = self.rpyc_conn.modules.os
        return remote_os.stat(path)

    def __parse_input(self, command_with_arguments):
        if len(command_with_arguments) != 2:
            raise TypeError('expecting one argument')
        return command_with_arguments[1]


class KillProcessHandler(CommandHandler):
    def __init__(self, rpyc_conn, created_processes):
        super().__init__(rpyc_conn)
        self.created_processes = created_processes

    def execute(self, command_with_arguments):
        if len(command_with_arguments) < 2:
            raise TypeError('expects at least one argument')

        if len(command_with_arguments) == 3:
            return self.__execute_kill_signo_pid(command_with_arguments)

        if len(command_with_arguments) != 2:
            raise TypeError("Incorrect usage")

        if command_with_arguments[1] == 'all':
            return self.__execute_kill_all()

        return self.__execute_kill_pid(command_with_arguments)

    def __execute_kill_signo_pid(self, command_with_arguments):
        if not command_with_arguments[1].startswith('-'):
            raise ValueError('Incorrect usage')
        signo = int(command_with_arguments[1][1:])
        pid = int(command_with_arguments[2])
        return self.__kill(pid, signo)

    def __execute_kill_pid(self, command_with_arguments):
        pid = int(command_with_arguments[1])
        return self.__kill(pid)

    def __kill(self, pid, signal=9):
        remote_os = self.rpyc_conn.modules.os
        remote_os.kill(pid, signal)

    def __execute_kill_all(self):
        for process in self.created_processes:
            process.kill()
        self.created_processes.clear()


class RunAsNewProcessHandler(CommandHandler):
    def __init__(self, rpyc_conn, created_processes):
        super().__init__(rpyc_conn)
        self.created_processes = created_processes

    def execute(self, command_with_arguments):
        path_to_exe, argv_to_exe = self.__parse_input(command_with_arguments)
        remote_subprocess = self.rpyc_conn.modules.subprocess
        string_args = ' '.join(argv_to_exe)
        command_line_input = path_to_exe + ' ' + string_args
        process = remote_subprocess.Popen(command_line_input)

        self.created_processes += [process]

    def __parse_input(self, command_with_arguments):
        if len(command_with_arguments) < 2:
            raise TypeError('expecting at least one argument')
        return command_with_arguments[1], command_with_arguments[2:]


class MonitorHandler(CommandHandler):
    def __init__(self, rpyc_conn):
        super().__init__(rpyc_conn)
        self.monitored_paths = dict()  # filepath --> FileMonitor object

    def execute(self, command_with_arguments):
        # show monitors
        if len(command_with_arguments) == 1 and command_with_arguments[0] == 'monitors':
            return self.monitored_paths.keys()

        if len(command_with_arguments) != 3:
            raise TypeError("expecting 2 arguments")

        if command_with_arguments[1] == '-r':
            return self.__remove_monitor(command_with_arguments[2])
        return self.__add_monitor(command_with_arguments[1], command_with_arguments[2])

    def __remove_monitor(self, monitored_path):
        self.monitored_paths[monitored_path].stop()
        del self.monitored_paths[monitored_path]

    def __add_monitor(self, path_to_monitor, log_path):
        file_monitor = self.rpyc_conn.root.FileMonitor(path_to_monitor, self.__get_callback_on_file_change(log_path))
        self.monitored_paths[path_to_monitor] = file_monitor

    def __get_callback_on_file_change(self, log_path):
        def on_file_change_callback(old_stat, new_stat):
            with open(log_path, 'a+') as log_file:
                print(datetime.datetime.now(), file=log_file)
                print('old stat:', file=log_file)
                print(old_stat, '\n', file=log_file)
                print('new stat:', file=log_file)
                print(new_stat, '\n', file=log_file)
                print('-------------------------\n', file=log_file)

        return on_file_change_callback

    def close_monitors(self):
        for monitor in self.monitored_paths.values():
            monitor.stop()


class RemoveHandler(CommandHandler):
    def execute(self, command_with_arguments):
        path_to_delete = self.__parse_input(command_with_arguments)
        teleported_func = self.rpyc_conn.teleport(self.__get_remove_empty_files_recursively_function())
        teleported_func(path_to_delete)

    def __parse_input(self, command_with_arguments):
        if (command_with_arguments[1], command_with_arguments[2]) != ('-r', '--empty-files'):
            raise TypeError("incorrect usage")
        return command_with_arguments[3]

    def __get_remove_empty_files_recursively_function(self):
        def remove_empty_files_recursively(base_dir_path):
            import os
            for path, subdirs, files in os.walk(base_dir_path):
                for name in files:
                    full_file_name = os.path.join(path, name)
                    if os.stat(full_file_name).st_size == 0:
                        os.remove(full_file_name)

        return remove_empty_files_recursively
