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
        self.term.toggle()

    @method('org.gnome.Terminalle')
    def Quit(self):
        self.term.quit()

def parse_args():
    home = getenv('HOME', '~')
    parser = ArgumentParser(description='A fancy drop-down terminal emulateur.',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config', metavar='PATH',
                        help='load config settings from PATH',
                        default=f'{home}/.config/terminalle.yaml')
    parser.add_argument('-s', '--show', action='store_true',
                        help='show the window immediately on startup')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    loop = glib.DBusGMainLoop(set_as_default=True)
    bus = SessionBus()
    name = BusName('org.gnome.Terminalle', bus)
    term = Terminalle(settings=load(args.config), show=args.show)
    ctrl = Control(term, bus)
    term.run()
