import sys
from rpyc_client.CommandHandlersManager import CommandHandlersManager

"""
The Terminal that reads commands and give them to the command_handlers_manager to execute.
Just a simple terminal, no advanced features.
__init__ may throw ConnectionRefusedError.
"""


class Terminal(object):
    """
    command_handlers_manager is type CommandHandlersManager
    """

    def __init__(self, server_ip, server_port, prompt='> '):
        self.prompt = prompt
        self.command_handlers_manager = CommandHandlersManager(server_ip, server_port)
        self.is_activated = False

    def start(self, close_on_input_end=True):
        self.is_activated = True
        while self.is_activated:
            command_output = self.read_execute_command()
            if command_output:
                if type(command_output) is str and command_output.startswith('Error: '):
                    print(command_output, file=sys.stderr)
                else:
                    print(command_output)

        if close_on_input_end:
            self.stop()

    def read_execute_command(self):
        user_input = input(self.prompt)
        if len(user_input) > 500:
            print("input is too long", file=sys.stderr)
            return
        if len(user_input) == 0:
            return

        split_input = user_input.split(' ')
        user_command, command_args = split_input[0], split_input[1:]

        if user_command in ["quit", "exit"]:
            self.is_activated = False
            return

        command_output = self.command_handlers_manager.execute(user_command, command_args)
        return command_output

    def stop(self):
        self.command_handlers_manager.close()
