import rpyc_client.Terminal
import builtins
import pytest


@pytest.fixture()
def set_input_commands(monkeypatch, request):
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

    monkeypatch.setattr(builtins, "input", InputCommandsFactory(request.param))


@pytest.mark.usefixtures("set_input_commands")
@pytest.mark.parametrize("set_input_commands", [['ps']], indirect=True)
def test_simple_stupid_upload(capsys):
    client = rpyc_client.Terminal.Terminal("localhost", 18871)
    client.start()

    captured = capsys.readouterr()
    assert len(captured.out) > 10 and 'p' in captured.out
