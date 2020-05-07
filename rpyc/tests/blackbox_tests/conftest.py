import pytest
import builtins
from client import get_terminal
import os
import shutil


# gets a list of commands to the terminal (as strings)
# Redirects these commands to the terminal as stdin
@pytest.fixture(autouse=True)
def set_input_commands(monkeypatch, request):
    # objects of this class simulates stdin input to the terminal
    class InputCommandsFactory(object):
        def __init__(self, commands):
            self.call_number = 0
            self.commands = commands

        def __call__(self, *args, **kwargs):
            if self.call_number >= len(self.commands):
                return 'quit'
            output = self.commands[self.call_number]
            self.call_number += 1
            return output

    # patch builtin input method to the given input
    monkeypatch.setattr(builtins, "input", InputCommandsFactory(request.param))


# receives the ip and port of the server
# Returns a terminal connected to the server
@pytest.fixture(scope='module')
def terminal(server_ip_port):
    server_ip, server_port = tuple(server_ip_port.split(':'))
    user_terminal = get_terminal(server_ip, server_port, is_test_mod=True)
    yield user_terminal
    user_terminal.stop()


@pytest.fixture()
def clean_dir():
    dirname = 'new_working_dir'
    os.mkdir(dirname)
    os.chdir(dirname)
    yield
    os.chdir('..')
    shutil.rmtree(dirname, ignore_errors=True)
