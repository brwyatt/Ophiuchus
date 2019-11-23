# Parent class for subcommands.
class Subcommand:
    def __init__(self, parser):
        pass

    def __call__(self, *args, **kwargs) -> int:
        raise NotImplementedError("This subcommand has not been implemented")
