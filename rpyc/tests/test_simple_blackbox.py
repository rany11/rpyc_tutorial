import rpyc_client.Terminal
import builtins
import pytest


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


@pytest.mark.usefixtures("set_input_commands")
@pytest.mark.parametrize("set_input_commands", [['ps']], indirect=True)
@pytest.mark.parametrize("terminal", [("localhost", 18871)], indirect=True)
def test_simple_stupid_upload(capsys, terminal):
    terminal.start()

    captured = capsys.readouterr()  # the output of stdout, stderr
    assert 'System Idle Process' in captured.out and captured.err == ''
