import psutil
import datetime
import argparse

DEFAULT_COPY_CHUNK_SIZE = 2 ** 14


def parse_single_path_argument(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument('path')
    args = parser.parse_args(argv[1:])
    return args.path


"""
All the command handlers.
They parse, execute and return output (if any) to the terminal. 
"""


class CommandHandler(object):
    def __init__(self, rpyc_conn):
        self.rpyc_conn = rpyc_conn

    def execute(self, command_with_arguments):
        """
        executes the command. Might raise exception on failures or incorrect usage.
        :param command_with_arguments: exactly as argv for a script
        :return: string that is an output to the terminal
        """
        raise NotImplementedError()


class CopyFileHandler(CommandHandler):
    def __init__(self, rpyc_conn):
        super().__init__(rpyc_conn)
        self.DOWNLOAD_COMMAND = 'download'
        self.UPLOAD_COMMAND = 'upload'

    def execute(self, command_with_arguments):
        srcpath, dstpath = self.__parse_input(command_with_arguments)
        if command_with_arguments[0] == self.UPLOAD_COMMAND:
            return self.__execute_upload(srcpath, dstpath)
        elif command_with_arguments[0] == self.DOWNLOAD_COMMAND:
            return self.__execute_download(srcpath, dstpath)
        raise ValueError("Unexpected command")

    def __parse_input(self, command_with_arguments):
        parser = argparse.ArgumentParser(command_with_arguments[0])
        parser.add_argument('srcpath')
        parser.add_argument('dstpath')
        args = parser.parse_args(command_with_arguments[1:])
        return args.srcpath, args.dstpath

    def __execute_upload(self, srcpath, dstpath):
        with open(srcpath, 'rb') as src:
            with self.rpyc_conn.builtin.open(dstpath, "wb") as dst:
                self.__copy_file(src, dst)

    def __execute_download(self, srcpath, dstpath):
        with self.rpyc_conn.builtin.open(srcpath, 'rb') as src:
            with open(dstpath, "wb") as dst:
                self.__copy_file(src, dst)

    def __copy_file(self, src_file_handler, dst_file_handler, chunk_size=DEFAULT_COPY_CHUNK_SIZE):
        while True:
            buf = src_file_handler.read(chunk_size)
            if not buf:
                break
            dst_file_handler.write(buf)


class DirlistHandler(CommandHandler):
    def execute(self, command_with_arguments):
        path = parse_single_path_argument(command_with_arguments)
        remote_os = self.rpyc_conn.modules.os
        return remote_os.listdir(path)


class ProcessListHandler(CommandHandler):
    def execute(self, command_with_arguments):
        self.__validate_input(command_with_arguments)

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

    def __validate_input(self, command_with_arguments):
        if len(command_with_arguments) != 1:
            raise TypeError('not expecting any arguments')


class FileStatHandler(CommandHandler):
    def execute(self, command_with_arguments):
        path = parse_single_path_argument(command_with_arguments)
        remote_os = self.rpyc_conn.modules.os
        return remote_os.stat(path)


class KillProcessHandler(CommandHandler):
    def __init__(self, rpyc_conn, created_processes):
        super().__init__(rpyc_conn)
        self.created_processes = created_processes

    def __parse_input(self, command_with_arguments):
        parser = argparse.ArgumentParser(command_with_arguments[0])
        parser.add_argument('path')
        args = parser.parse_args(command_with_arguments[1:])
        return args.path

    def execute(self, command_with_arguments):
        if len(command_with_arguments) == 3:
            # the command is: kill -signo pid
            if not command_with_arguments[1].startswith('-'):
                # signo should start with '-' prefix
                raise ValueError('Incorrect usage')
            return self.__execute_kill_signo_pid(command_with_arguments)

        if len(command_with_arguments) == 2:
            if command_with_arguments[1] == 'all':
                # the command is: kill all
                return self.__execute_kill_all()
            else:
                # the command is kill pid
                return self.__execute_kill_pid(command_with_arguments)

        raise TypeError('Incorrect usage')

    def __execute_kill_signo_pid(self, command_with_arguments):
        signo = int(command_with_arguments[1][1:])
        pid = int(command_with_arguments[2])
        return self.__kill(pid, signo)

    def __execute_kill_pid(self, command_with_arguments):
        pid = int(command_with_arguments[1])
        return self.__kill(pid)

    def __kill(self, pid, signal=9):
        remote_os = self.rpyc_conn.modules.os
        """
        if the process was created by exec command,
        should remove it from self.created_processes list.
        However, this is ok as it is.
        """
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
        path_to_exe, argv_to_exe = command_with_arguments[1], command_with_arguments[2:]
        remote_subprocess = self.rpyc_conn.modules.subprocess
        string_args = ' '.join(argv_to_exe)
        command_line_input = path_to_exe + ' ' + string_args
        process = remote_subprocess.Popen(command_line_input)

        self.created_processes += [process]


class MonitorHandler(CommandHandler):
    def __init__(self, rpyc_conn):
        super().__init__(rpyc_conn)
        self.monitored_paths = dict()  # filepath --> FileMonitor object
        self.REMOVE_FLAG = '-r'

    def execute(self, command_with_arguments):
        if len(command_with_arguments) == 1 and command_with_arguments[0] == 'monitors':
            # show the existing monitors
            return self.monitored_paths.keys()

        if len(command_with_arguments) == 3:
            if command_with_arguments[1] == self.REMOVE_FLAG:
                # the command is: monitor -r {monitored_path}
                return self.__remove_monitor(command_with_arguments[2])
            else:
                # the command is monitor {path} {logpath}
                return self.__add_monitor(command_with_arguments[1], command_with_arguments[2])

        raise TypeError("Incorrect usage")

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
        parser = argparse.ArgumentParser(prog=command_with_arguments[0])
        parser.add_argument("-r", "--recursive", action="store_true", required=True)
        parser.add_argument("--empty-files", action="store_true", required=True)
        parser.add_argument('path')
        args = parser.parse_args(command_with_arguments[1:])
        return args.path

    def __get_remove_empty_files_recursively_function(self):
        def remove_empty_files_recursively(base_dir_path):
            import os
            for path, subdirs, files in os.walk(base_dir_path):
                for name in files:
                    full_file_name = os.path.join(path, name)
                    if os.stat(full_file_name).st_size == 0:
                        os.remove(full_file_name)

        return remove_empty_files_recursively
