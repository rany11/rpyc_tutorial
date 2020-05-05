import psutil
import datetime
from ErrorMessage import ErrorMessage

"""
All the command handlers.
They parse, execute and possibly format the output for the terminal.
They (must) also return (and receive) additional information to the command_handlers_manager. 
"""


class CommandHandler(object):
    def __init__(self, rpyc_conn):
        self.rpyc_conn = rpyc_conn
        self.empty_output = (None, None)

    def _parse_input(self, split_input, additional_input):
        raise NotImplementedError()

    def _execute(self, **kwargs):  # real signature unknown
        raise NotImplementedError()

    def _format_output(self, output):
        return output

    def handle_command(self, split_input, additional_input):
        try:
            kwargs = self._parse_input(split_input, additional_input)
            terminal_output, manager_output = self._execute(**kwargs)
            terminal_output = self._format_output(terminal_output) if terminal_output else terminal_output
            return terminal_output, manager_output
        except Exception as e:
            # get just the error message without the stack-trace
            raise ErrorMessage(str(e).split('\n')[0])


class CopyFileHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) != 3:
            raise TypeError('expected two arguments')

        command = split_input[0]
        if command == 'upload':
            return {'local_path': split_input[1], 'remote_path': split_input[2], 'mod': command}
        else:
            return {'remote_path': split_input[1], 'local_path': split_input[2], 'mod': command}

    def _execute(self, local_path, remote_path, mod):
        chunk_size = 16000
        local_path_open_mod, remote_path_open_mod = ("rb", "wb") if mod == 'upload' else ("wb", "rb")

        with open(local_path, local_path_open_mod) as lf:
            with self.rpyc_conn.builtin.open(remote_path, remote_path_open_mod) as rf:
                if mod == 'download':  # remote to local
                    self.__copy_file(rf, lf, chunk_size)
                elif mod == 'upload':  # local to remote
                    self.__copy_file(lf, rf, chunk_size)

        return self.empty_output

    def __copy_file(self, src_file_handler, dst_file_handler, chunk_size):
        while True:
            buf = src_file_handler.read(chunk_size)
            if not buf:
                break
            dst_file_handler.write(buf)


class DirlistHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) != 2:
            raise TypeError('expected one argument')
        return {'path': split_input[1]}

    def _execute(self, path):
        remote_os = self.rpyc_conn.modules.os
        return remote_os.listdir(path), None


class ProcessListHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) != 1:
            raise TypeError('not expecting any arguments')
        return dict()

    def _execute(self):
        remote_psutil = self.rpyc_conn.modules.psutil
        process_list = []
        for proc in remote_psutil.process_iter():
            try:
                # Get process name & pid from process object.
                process_name = proc.name()
                process_id = proc.pid
                process_list += [{'name': process_name, 'pid': process_id}]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return process_list, None


class FileStatHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) != 2:
            raise TypeError('expecting one argument')
        return {'path': split_input[1]}

    def _execute(self, path):
        remote_os = self.rpyc_conn.modules.os
        return remote_os.stat(path), None


class KillProcessHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) < 2:
            raise TypeError('expects at least one argument')

        if len(split_input) == 3:
            if not split_input[1].startswith('-'):
                raise ValueError("kill signal number should start with '-'")
            return {'signal': int(split_input[1][1:]), 'pid': int(split_input[2])}
        elif len(split_input) == 2:
            return {'pid': int(split_input[1])}

        raise TypeError('too many arguments')

    def _execute(self, pid, signal=9):
        remote_os = self.rpyc_conn.modules.os
        remote_os.kill(pid, signal)
        return self.empty_output


class RunAsNewProcessHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) < 2:
            raise TypeError('expecting at least one argument')
        return {'path_to_executable': split_input[1], 'argv_to_exe': split_input[2:]}

    def _execute(self, path_to_executable, argv_to_exe):
        remote_subprocess = self.rpyc_conn.modules.subprocess
        string_args = ' '.join(argv_to_exe)
        command_line_input = path_to_executable + ' ' + string_args
        process = remote_subprocess.Popen(command_line_input)
        return None, process


class MonitorHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if len(split_input) != 3:
            raise TypeError("expecting 2 arguments")

        if split_input[1] == '-r':
            return {'monitored_path': split_input[2], 'log_path': '', 'monitors': additional_input, 'remove': True}

        return {'monitored_path': split_input[1], 'log_path': split_input[2], 'monitors': additional_input}

    def _execute(self, monitored_path, log_path, monitors, remove=False):
        if not remove and monitored_path in monitors:
            return self.empty_output

        if remove and monitored_path in monitors:
            monitors[monitored_path].stop()
            del monitors[monitored_path]
            return self.empty_output

        if remove and monitored_path not in monitors:
            return self.empty_output

        # not remove and monitored_path not in monitors
        return '', self.rpyc_conn.root.FileMonitor(monitored_path, self.__get_callback(log_path))

    # Warning: Careful with this closure
    def __get_callback(self, log_path):
        def callback(old_stat, new_stat):
            with open(log_path, 'a+') as log_file:
                print(datetime.datetime.now(), file=log_file)
                print('old stat:', file=log_file)
                print(old_stat, '\n', file=log_file)
                print('new stat:', file=log_file)
                print(new_stat, '\n', file=log_file)
                print('-------------------------\n', file=log_file)

        return callback


class RemoveHandler(CommandHandler):
    def _parse_input(self, split_input, additional_input):
        if {split_input[1], split_input[2]} != {'-r', '--empty-files'}:
            raise TypeError("incorrect usage")
        return {'path': split_input[3]}

    def __get_remove_empty_files_function(self):
        def remove_empty_files(base_dir_path):
            import os
            for path, subdirs, files in os.walk(base_dir_path):
                for name in files:
                    full_file_name = os.path.join(path, name)
                    if os.stat(full_file_name).st_size == 0:
                        os.remove(full_file_name)

        return remove_empty_files

    def _execute(self, path):
        teleported_func = self.rpyc_conn.teleport(self.__get_remove_empty_files_function())
        teleported_func(path)
        return self.empty_output
