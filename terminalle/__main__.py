#!/usr/bin/python3

from os import getenv
from os.path import join as join_path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from dbus import SessionBus
from dbus.service import Object as DBusObject, BusName, method
from dbus.mainloop.glib import DBusGMainLoop

from . import Terminalle, load_settings, service_name
from .auto import auto, no_auto, xdg_config_home_path

class Controller(DBusObject):

    def __init__(self, term, bus, object_path='/org/gnome/Terminalle'):
        super().__init__(bus, object_path)
        self.term = term

    @method(service_name)
    def Toggle(self):
        self.term.toggle()

    @method(service_name)
    def Quit(self):
        self.term.quit()

def build_parser():
    parser = ArgumentParser(description='A fancy "drop-down" terminal emulateur.',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='1.0')
    parser.add_argument('-c', '--config', metavar='PATH',
                        help='load config settings from PATH',
                        default=join_path(xdg_config_home_path, 'terminalle.yaml'))
    parser.add_argument('-s', '--show', action='store_true',
                        help='show the window immediately on startup')
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand',
                                       description='''
            Use `<subcommand> --help` for more information.''')
    auto_parser = subparsers.add_parser('auto', help='configure auto-start and/or auto-restart',
                                        description='''
            Install an XDG desktop file to auto-start Terminalle (in hidden mode) on login,
            as well as a DBUS service file to auto-restart Terminalle
            if it\'s not already running when the user attempts to toggle it.''',
                                        formatter_class=ArgumentDefaultsHelpFormatter)
    no_auto_parser = subparsers.add_parser('no-auto', help='remove auto-(re)start functionality',
                                           description='''
            Remove the DBUS service file and XDG desktop file
            that were installed using the `auto` subcommand.''',
                                           formatter_class=ArgumentDefaultsHelpFormatter)
    for sub_parser in [auto_parser, no_auto_parser]:
        target_group = sub_parser.add_mutually_exclusive_group()
        target_group.add_argument('-u', '--user', action='store_true',
                                  help='apply to the current user only', default=True)
        target_group.add_argument('-s', '--system', action='store_true',
                                  help='apply to all users on the system', default=False)
        sub_parser.add_argument('-f', '--force', action='store_true',
                                help='modify files even if existing contents are unexpected')
    auto_parser.add_argument('--no-start-on-login', action='store_true',
                             help='do *not* install XDG desktop file')
    auto_parser.add_argument('--no-restart-if-closed', action='store_true',
                             help='do *not* install DBUS service file')
    return parser

def main():
    args = build_parser().parse_args()
    if args.subcommand is None:
        # By default, run a new instance of the application.
        loop = DBusGMainLoop(set_as_default=True)
        bus = SessionBus()
        name = BusName(service_name, bus)
        term = Terminalle(settings=load_settings(args.config), show=args.show)
        ctrl = Controller(term, bus)
        term.run()
    elif args.subcommand == 'auto':
        auto(args.system, args.force,
             not args.no_start_on_login, not args.no_restart_if_closed)
    elif args.subcommand == 'no-auto':
        no_auto(args.system, args.force)
    else:
        raise ValueError(f'Unexpected subcommand \'{args.subcommand}\'.')

if __name__ == '__main__':
    main()
