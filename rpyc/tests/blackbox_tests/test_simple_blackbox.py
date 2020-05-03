import pytest


class TestSimpleBlackbox(object):

    @pytest.mark.parametrize("set_input_commands", [['ps']], indirect=True)
    def test_simple_blackbox_ps(self, capsys, terminal):
        terminal.start()
        captured = capsys.readouterr()  # the output of stdout, stderr

        assert 'System Idle Process' in captured.out and captured.err == ''

    @pytest.mark.usefixtures("clean_dir")
    @pytest.mark.parametrize("set_input_commands", [[r'upload new_file .\new_remote_file', 'ls .']], indirect=True)
    def test_simple_blackbox_upload(self, capsys, terminal):
        with open('new_file', 'w+') as f:
            f.write('my special content')  # no need to delete file, due to cleandir fixture
        terminal.start()
        captured = capsys.readouterr()  # the output of stdout, stderr

        assert 'new_remote_file' in captured.out and captured.err == ''
