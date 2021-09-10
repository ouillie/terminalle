""" Command-line tools to install and remove autostart-related files. """

from os import getenv, makedirs, readlink, symlink, unlink
from os.path import abspath, join as join_path, sep as path_sep, dirname, isfile, islink
from sys import stderr

from pkg_resources import resource_filename

from . import service_name

# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html (for reference)
# https://specifications.freedesktop.org/autostart-spec/autostart-spec-latest.html (auto-start)
# https://dbus.freedesktop.org/doc/dbus-daemon.1.html (auto-restart)
home_path = getenv('HOME', '~')
xdg_config_home_path = getenv('XDG_CONFIG_HOME', join_path(home_path, '.config'))
xdg_data_home_path = getenv('XDG_DATA_HOME', join_path(home_path, '.local', 'share'))
xdg_config_dirs_paths = getenv('XDG_CONFIG_DIRS', abspath(join_path(path_sep, 'etc', 'xdg')))
xdg_data_dirs_paths = getenv('XDG_DATA_DIRS', abspath(join_path(path_sep, 'usr', 'share')))

def _get_dests_and_srcs(system: bool):
    service_filename = '.'.join([service_name, 'service'])
    desktop_filename = 'terminalle.desktop'
    if system:
        xdg_config_dirs = xdg_config_dirs_paths.split(':')
        xdg_data_dirs = xdg_data_dirs_paths.split(':')
    else:
        xdg_config_dirs = [xdg_config_home_path]
        xdg_data_dirs = [xdg_data_home_path]
    return ([join_path(config_dir, 'autostart', desktop_filename)
             for config_dir in xdg_config_dirs],
            resource_filename(__name__, desktop_filename),
            [join_path(data_dir, 'dbus-1', 'services', service_filename)
             for data_dir in xdg_data_dirs],
            resource_filename(__name__, service_filename))

def auto(home_path: str, system: bool, force: bool, start_on_login: bool, restart_if_closed: bool):
    desktop_dests, desktop_src, service_dests, service_src =  _get_dests_and_srcs(home_path, system)
    # Pick the least-precendence item in the destination lists.
    # This tends to be the system-wide rather than 'local' destination.
    for enable, src, dest in [(start_on_login, desktop_src, desktop_dests[-1]),
                              (restart_if_closed, service_src, service_dests[-1])]:
        if enable:
            if isfile(dest):
                if islink(dest):
                    real_src = readlink(dest)
                    if real_src == src:
                        print(f'Symlink already exists: {dest}\n'
                              f'                     -> {src}', file=stderr)
                        continue
                    elif force:
                        unlink(dest)
                    else:
                        print(f'Unexpected symlink: {dest}\n'
                              f'                 -> {real_src}\n'
                              '(use `--force` to overwrite it)', file=stderr)
                        continue
                elif force:
                    unlink(dest)
                else:
                    print(f'Unexpected file: {dest}\n'
                          '(use `--force` to overwrite it)', file=stderr)
                    continue
            else:
                makedirs(dirname(dest), mode=0o755, exist_ok=True)
            symlink(src, dest)
            print(f'Created symlink: {dest}\n'
                  f'              -> {src}', file=stderr)

def no_auto(home_path: str, system: bool, force: bool):
    desktop_dests, desktop_src, service_dests, service_src =  _get_dests_and_srcs(home_path, system)
    for src, dests in [(desktop_src, desktop_dests), (service_src, service_dests)]:
        for dest in dests:
            if isfile(dest):
                if force or islink(dest):
                    if force or readlink(dest) == src:
                        unlink(dest)
                        print(f'Deleted: {dest}', file=stderr)
                    else:
                        real_src = readlink(dest)
                        print(f'Unexpected symlink: {dest}\n'
                              f'                 -> {real_src}'
                              '(use `--force` to delete it anyway)', file=stderr)
                else:
                    print(f'Unexpected file: {dest}\n'
                          '(use `--force` to delete it anyway)', file=stderr)
