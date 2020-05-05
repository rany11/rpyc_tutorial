import sys
from .CommandHandlersManager import CommandHandlersManager
from .ErrorMessage import ErrorMessage

REGULAR_PROMPT = '> '
MAX_INPUT_LENGTH = 2000

"""
The Terminal that reads commands and give them to the command_handlers_manager to execute.
Just a simple terminal, no advanced features.
__init__ may throw ConnectionRefusedError.
"""


class Terminal(object):
    """
    command_handlers_manager is type CommandHandlersManager
    """

    def __init__(self, command_handlers_manager, prompt=REGULAR_PROMPT):
        self.prompt = prompt
        self.command_handlers_manager = command_handlers_manager
        self.is_activated = False

    def start(self):
        self.is_activated = True
        while self.is_activated:
            try:
                command_output = self.read_execute_command()
                if command_output:
                    print(command_output)

            except ErrorMessage as e:
                print(e.error_message, file=sys.stderr)

        self.__stop()

    """
    This function read a single command from the user, executes and returns the terminal output.
    @throws: ErrorMessage
    """
    def read_execute_command(self):
        user_input = input(self.prompt)
        if not self.__is_user_input_valid(user_input):
            raise ErrorMessage("invalid input")
        if len(user_input) == 0:  # user just pressed Enter key. We do nothing
            return

        split_input = user_input.split(' ')
        user_command, command_args = split_input[0], split_input[1:]

        if user_command in ["quit", "exit"]:
            self.is_activated = False
            return

        command_output = self.command_handlers_manager.execute(user_command, command_args)
        return command_output

    def __stop(self):
        self.command_handlers_manager.close()

    def __is_user_input_valid(self, user_input):
        return len(user_input) <= MAX_INPUT_LENGTH
