import sys


class Terminal(object):
    """
    command_handlers_manager is type CommandHandlersManager
    """

    def __init__(self, command_handlers_manager, prompt='> '):
        self.prompt = prompt
        self.command_handlers_manager = command_handlers_manager
        self.is_activated = False

    def start(self):
        self.is_activated = True
        while self.is_activated:
            command_output = self.read_execute_command()
            if command_output:
                if type(command_output) is str and command_output.startswith('Error: '):
                    print(command_output, file=sys.stderr)
                else:
                    print(command_output)

        self.__stop()

    def read_execute_command(self):
        user_input = input(self.prompt)
        if len(user_input) > 500:
            print("input is too long")
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

    def __stop(self):
        self.command_handlers_manager.close()
