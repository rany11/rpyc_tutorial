import pytest
import builtins
import rpyc_client.Terminal
import os
import shutil


# gets a list of commands to the terminal (as strings)
# Redirects these commands to the terminal as stdin
@pytest.fixture()
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
@pytest.fixture()
def terminal(request):
    return rpyc_client.Terminal.Terminal(request.param[0], request.param[1])


@pytest.fixture()
def clean_dir():
    dirname = 'new_working_dir'
    os.mkdir(dirname)
    os.chdir(dirname)
    yield
    os.chdir('..')
    shutil.rmtree(dirname, ignore_errors=True)
