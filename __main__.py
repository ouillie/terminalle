#!python3

from argparse import ArgumentParser

from terminale import Terminale
from serve import serve
from settings import normalize

def main():
    parser = ArgumentParser(description='A fançy drop-down terminal.')
    parser.add_argument('-s', '--socket', metavar='PATH',
                        help='listen for client messages on PATH',
                        default='/etc/terminale/.server.skt')
    parser.add_argument('-f', '--force', action='store_true',
                        help='delete the server socket if it already exists')
    parser.add_argument('-S', '--show', action='store_true',
                        help='show the window immediately on startup')
    args = parser.parse_args()

    term = Terminale(settings=normalize(), show=args.show)
    serve(path=args.socket, force=args.force, timeout=0.1,
          run_fn=term.run, toggle_fn=term.toggle, quit_fn=term.quit)

if __name__ == '__main__':
    main()
