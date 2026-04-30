import sys
from quads_client.shell import QuadsClientShell


def main():
    shell = QuadsClientShell()

    if len(sys.argv) > 1:
        shell.onecmd(" ".join(sys.argv[1:]))
    else:
        shell.cmdloop()


if __name__ == "__main__":
    main()
