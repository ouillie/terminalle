#!/usr/bin/env python3

from os.path import join as join_path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from . import Terminalle, load_settings, __version__
from .auto import auto, no_auto, xdg_config_home_path
from .key import (
    keybind_autodetect, keybind_gnome, keybind_kde,
    no_keybind_autodetect, no_keybind_gnome, no_keybind_kde,
)

def build_argparse() -> ArgumentParser:
    parser = ArgumentParser(
        description='A fancy "drop-down" terminal emulateur.',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument(
        '-c',
        '--config',
        metavar='PATH',
        help='load config settings from PATH',
        default=join_path(xdg_config_home_path, 'terminalle.yaml'),
    )
    parser.add_argument(
        '-s',
        '--show',
        action='store_true',
        help='show the window immediately on startup',
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        dest='subcommand',
        description='Use `<subcommand> --help` for more information.',
    )
    auto_parser = subparsers.add_parser(
        'auto',
        help='configure auto-start and/or auto-restart',
        description='Install an XDG desktop file to auto-start Terminalle (in hidden mode) on login,'
            ' as well as a DBUS service file to auto-restart Terminalle'
            ' if it\'s not already running when the user attempts to toggle it.',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    no_auto_parser = subparsers.add_parser(
        'no-auto',
        help='remove auto-(re)start functionality',
        description='Remove the DBUS service file and XDG desktop file'
            ' that were installed using the `auto` subcommand.',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    key_parser = subparsers.add_parser(
        'key',
        help='configure keyboard shortcuts',
        description='Set up keyboard shortcut(s) to invoke actions (Toggle or Quit).'
            ' Supports GNOME and KDE.'
            ' The running desktop environment is autodetected by default.',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    no_key_parser = subparsers.add_parser(
        'no-key',
        help='remove keyboard shortcuts',
        description='Remove any keyboard shortcuts'
            ' that were created using the `key` subcommand.',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    for sub_parser in [auto_parser, no_auto_parser]:
        target_group = sub_parser.add_mutually_exclusive_group()
        target_group.add_argument(
            '-u',
            '--user',
            action='store_true',
            help='apply to the current user only',
            default=True,
        )
        target_group.add_argument(
            '-s',
            '--system',
            action='store_true',
            help='apply to all users on the system',
            default=False,
        )
        sub_parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            help='modify files even if existing contents are unexpected',
        )
    auto_parser.add_argument(
        '--no-start-on-login',
        action='store_true',
        help='do *not* install XDG desktop file',
    )
    auto_parser.add_argument(
        '--no-restart-if-closed',
        action='store_true',
        help='do *not* install DBUS service file',
    )

    key_parser.add_argument(
        '-t',
        '--toggle',
        action='append',
        metavar='KEYS',
        help='shortcut to toggle window visibility',
    )
    key_parser.add_argument(
        '-q',
        '--quit',
        action='append',
        metavar='KEYS',
        help='shortcut to shut down the application',
    )
    for sub_parser in [key_parser, no_key_parser]:
        desktop = sub_parser.add_mutually_exclusive_group()
        desktop.add_argument(
            '--gnome',
            action='store_true',
            help='assume the desktop environment is GNOME',
        )
        desktop.add_argument(
            '--kde',
            action='store_true',
            help='assume the desktop environment is KDE',
        )

    return parser

def main():
    args = build_argparse().parse_args()
    if args.subcommand is None:
        Terminalle(settings=load_settings(args.config), show=args.show).run()
    elif args.subcommand == 'auto':
        auto(args.system, args.force, not args.no_start_on_login, not args.no_restart_if_closed)
    elif args.subcommand == 'no-auto':
        no_auto(args.system, args.force)
    elif args.subcommand == 'key':
        if args.gnome:
            keybind = keybind_gnome
        elif args.kde:
            keybind = keybind_kde
        else:
            keybind = keybind_autodetect
        keybind(args.toggle, args.quit)
    elif args.subcommand == 'no-key':
        if args.gnome:
            no_keybind = no_keybind_gnome
        elif args.kde:
            no_keybind = no_keybind_kde
        else:
            no_keybind = no_keybind_autodetect
        no_keybind()
    else:
        raise ValueError(f'Unexpected subcommand \'{args.subcommand}\'.')

if __name__ == '__main__':
    main()
