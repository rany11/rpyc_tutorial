import pytest


# TODO: make terminal scope='module'.
# TODO: Add a halt method to terminal (That stops reading input but not closing connections
# TODO: maybe add a remote delete file so we can clean remotely after tests. Or run server from clean dir and assume nothing of it

@pytest.mark.usefixtures("set_input_commands")
@pytest.mark.parametrize("set_input_commands", [['ps']], indirect=True)
@pytest.mark.parametrize("terminal", [("localhost", 18871)], indirect=True)
def test_simple_blackbox_ps(capsys, terminal):
    terminal.start()
    captured = capsys.readouterr()  # the output of stdout, stderr

    assert 'System Idle Process' in captured.out and captured.err == ''


@pytest.mark.usefixtures("set_input_commands", "clean_dir")
@pytest.mark.parametrize("set_input_commands", [[r'upload new_file .\new_remote_file', 'ls .']], indirect=True)
@pytest.mark.parametrize("terminal", [("localhost", 18871)], indirect=True)
def test_simple_blackbox_upload(capsys, terminal):
    with open('new_file', 'w+') as f:
        f.write('my special content')
    terminal.start()
    captured = capsys.readouterr()  # the output of stdout, stderr

    assert 'new_remote_file' in captured.out and captured.err == ''
