""" Command-line tools to install and remove autostart-related files. """

from os import getenv, makedirs, readlink, symlink, unlink
from os.path import abspath, join as join_path, sep as path_sep, dirname, isfile, islink
from sys import stderr

from pkg_resources import resource_filename

from .terminalle import SERVICE_NAME

# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html (for reference)
# https://specifications.freedesktop.org/autostart-spec/autostart-spec-latest.html (auto-start)
# https://dbus.freedesktop.org/doc/dbus-daemon.1.html (auto-restart)
home_path = getenv('HOME', '~')
xdg_config_home_path = getenv('XDG_CONFIG_HOME', join_path(home_path, '.config'))
xdg_data_home_path = getenv('XDG_DATA_HOME', join_path(home_path, '.local', 'share'))
xdg_config_dirs_paths = getenv('XDG_CONFIG_DIRS', abspath(join_path(path_sep, 'etc', 'xdg')))
xdg_data_dirs_paths = getenv('XDG_DATA_DIRS', abspath(join_path(path_sep, 'usr', 'share')))

def _get_dests_and_srcs(system: bool):
    service_filename = '.'.join([SERVICE_NAME, 'service'])
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

def auto(system: bool, force: bool, start_on_login: bool, restart_if_closed: bool):
    desktop_dests, desktop_src, service_dests, service_src =  _get_dests_and_srcs(system)
    # Pick the least-precendence item in the destination lists.
    # This tends to be the system-wide rather than 'local' destination.
    for enable, src, dest in [(start_on_login, desktop_src, desktop_dests[-1]),
                              (restart_if_closed, service_src, service_dests[-1])]:
        if enable:
            if islink(dest):
                existing_src = readlink(dest)
                if existing_src == src:
                    print(f'Symlink already exists: {dest}\n'
                          f'                      → {src}', file=stderr)
                    continue
                elif force:
                    unlink(dest)
                else:
                    print(f'Unexpected symlink: {dest}\n'
                          f'                  → {existing_src}\n'
                          '(use `--force` to overwrite it)', file=stderr)
                    continue
            elif isfile(dest):
                if force:
                    unlink(dest)
                else:
                    print(f'Unexpected file: {dest}\n'
                          '(use `--force` to overwrite it)', file=stderr)
                    continue
            else:
                makedirs(dirname(dest), mode=0o755, exist_ok=True)
            symlink(src, dest)
            print(f'Created symlink: {dest}\n'
                  f'               → {src}', file=stderr)

def no_auto(system: bool, force: bool):
    desktop_dests, desktop_src, service_dests, service_src =  _get_dests_and_srcs(system)
    for src, dests in [(desktop_src, desktop_dests), (service_src, service_dests)]:
        for dest in dests:
            if islink(dest):
                existing_src = readlink(dest)
                if existing_src != src and not force:
                    print(f'Unexpected symlink: {dest}\n'
                          f'                  → {existing_src}\n'
                          '(use `--force` to delete it anyway)', file=stderr)
                    continue
            elif isfile(dest):
                if not force:
                    print(f'Unexpected file: {dest}\n'
                          '(use `--force` to delete it anyway)', file=stderr)
                    continue
            else:
                continue
            unlink(dest)
            print(f'Deleted: {dest}', file=stderr)
