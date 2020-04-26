import psutil



class CommandHandler(object):
    def __init__(self, rpyc_conn):
        self.rpyc_conn = rpyc_conn
        self.empty_output = (None, None)

    def _parse_input(self, split_input, additional_input):
        pass

    def _execute(self, **kwargs):
        return self.empty_output

    def _format_output(self, output):
        return output

    def handle_command(self, split_input, additional_input):
        try:
            kwargs = self._parse_input(split_input, additional_input)
            terminal_output, manager_output = self._execute(**kwargs)
            terminal_output = self._format_output(terminal_output) if terminal_output else terminal_output
            return terminal_output, manager_output
        except BaseException as e:
            return 'Error: ' + str(e), None


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
        if split_input[1] == 'all':
            if len(split_input) != 2:
                raise TypeError('not expecting arguments after kill all command')
            return {'created_processes': additional_input}

        if len(split_input) == 3:
            if not split_input[1].startswith('-'):
                raise ValueError("kill signal number should start with '-'")
            return {'signal': int(split_input[1][1:]), 'pid': int(split_input[2])}
        elif len(split_input) == 2:
            return {'pid': int(split_input[1])}

        raise TypeError('too many arguments')

    def _execute(self, **kwargs):
        if 'created_processes' in kwargs:
            return self.__kill_all_created_processes(**kwargs)
        return self.__kill_process(**kwargs)

    def __kill_process(self, pid, signal=9):
        remote_os = self.rpyc_conn.modules.os
        remote_os.kill(pid, signal)
        return self.empty_output

    def __kill_all_created_processes(self, created_processes):
        for process in created_processes:
            process.kill()
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
