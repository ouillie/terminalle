#!/usr/bin/python3

from os import getenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from dbus import SessionBus
from dbus.service import Object as DBusObject, BusName, method
from dbus.mainloop import glib

from .terminalle import Terminalle
from .settings import load

class Control(DBusObject):

    def __init__(self, term, bus, object_path='/termctl'):
        super().__init__(bus, object_path)
        self.term = term

    @method('org.gnome.Terminalle')
    def Toggle(self):
        print('tog')
        self.term.toggle()

    @method('org.gnome.Terminalle')
    def Quit(self):
        self.term.quit()

def main():
    home = getenv('HOME', '~')
    parser = ArgumentParser(description='A fançy drop-down terminal.',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config', metavar='PATH',
                        help='load config settings from PATH',
                        default=f'{home}/.config/terminalle.yaml')
    parser.add_argument('-f', '--force', action='store_true',
                        help='delete the server socket if it already exists')
    parser.add_argument('-s', '--show', action='store_true',
                        help='show the window immediately on startup')
    args = parser.parse_args()

    glib.DBusGMainLoop(set_as_default=True)
    bus = SessionBus()
    name = BusName('org.gnome.Terminalle', bus)
    term = Terminalle(settings=load(args.config), show=args.show)
    ctrl = Control(term, bus)
    term.run()

if __name__ == '__main__':
    main()
