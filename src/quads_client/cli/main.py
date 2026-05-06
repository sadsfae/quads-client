import sys
from quads_client.shell import QuadsClientShell


def main():
    """
    Main entry point for quads-client.

    Supports two modes:
    - Interactive mode: quads-client
    - One-shot mode: quads-client <command>
    """
    # Detect one-shot mode
    is_oneshot = len(sys.argv) > 1

    # Create shell with quiet mode for one-shot
    shell = QuadsClientShell(quiet=is_oneshot)

    if is_oneshot:
        # One-shot mode: execute single command and exit
        cmd_str = " ".join(sys.argv[1:])

        # Auto-connect to default server if needed
        exit_code = shell.execute_oneshot_command(cmd_str)
        sys.exit(exit_code)
    else:
        # Interactive mode
        shell.cmdloop()


if __name__ == "__main__":
    main()
