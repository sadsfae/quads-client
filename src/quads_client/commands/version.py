class VersionCommands:
    def __init__(self, shell):
        self.shell = shell

    def cmd_version(self, args):
        """Display QUADS Client version"""
        from quads_client import __version__

        self.shell.poutput(f"quads-client version {__version__}")
