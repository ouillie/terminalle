"""Command-line tool to configure keyboard shortcuts for actions."""

from functools import partial
from itertools import count
from os import getenv
from sys import stderr
from typing import Dict, List, Optional
import re

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio

_gnome_media_keys_key = 'org.gnome.settings-daemon.plugins.media-keys'
_gnome_custom_keybinding_key = 'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding'
_gnome_custom_keybinding_path_template = \
    '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{}/'
_gnome_custom_keybinding_path_regex = \
    re.compile(r'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom([0-9]+)/')
_gnome_shortcut_name = 'Toggle Terminalle'
_gnome_shortcut_command_template = \
    'dbus-send --session --type=method_call --dest=party.will.Terminalle' \
        ' /party/will/Terminalle party.will.Terminalle.{}'

def keybind_gnome(toggle: Optional[List[str]], quit: Optional[List[str]]):
    """Configure keybindings for GNOME."""
    media_keys = Gio.Settings.new(_gnome_media_keys_key)
    existing_keybindings = media_keys.get_strv('custom-keybindings')
    new_keybindings = existing_keybindings.copy()

    used_indices = set()
    for path in existing_keybindings:
        match = _gnome_custom_keybinding_path_regex.match(path)
        if match is not None:
            used_indices.add(int(match[1]))
    indices = count()

    for new_binding, action in _compile_actions(Toggle=toggle, Quit=quit):
        command = _gnome_shortcut_command_template.format(action)
        # Check if there's a pre-existing binding for the command.
        for path in existing_keybindings:
            custom = Gio.Settings.new_with_path(_gnome_custom_keybinding_key, path)
            if custom.get_string('command') == command:
                name = custom.get_string('name')
                existing_binding = custom.get_string('binding')
                print(
                    f'Shortcut already exists for {action}: \'{name}\' ({existing_binding})',
                    file=stderr,
                )
                break
        # If not, add the new keybinding.
        else:
            next_index = next(indices)
            while next_index in used_indices:
                next_index = next(indices)
            path = _gnome_custom_keybinding_path_template.format(next_index)
            new_keybindings.append(path)
            custom = Gio.Settings.new_with_path(_gnome_custom_keybinding_key, path)
            custom.set_string('name', f'{action} Terminalle')
            custom.set_string('command', command)
            custom.set_string('binding', new_binding)
            print(f'Creating shortcut for {action} ({new_binding})', file=stderr)

    media_keys.set_strv('custom-keybindings', new_keybindings)
    Gio.Settings.sync()

def no_keybind_gnome():
    """Remove keybindings for GNOME."""
    media_keys = Gio.Settings.new(_gnome_media_keys_key)
    existing_keybindings = media_keys.get_strv('custom-keybindings')
    new_keybindings = []

    actions = [
        (action, _gnome_shortcut_command_template.format(action))
        for action in ['Toggle', 'Quit']
    ]
    for path in existing_keybindings:
        for action, command in actions:
            custom = Gio.Settings.new_with_path(_gnome_custom_keybinding_key, path)
            if custom.get_string('command') == command:
                binding = custom.get_string('binding')
                custom.set_string('name', '')
                custom.set_string('command', '')
                custom.set_string('binding', '')
                print(f'Removing shortcut for {action} ({binding})', file=stderr)
                break
        else:
            new_keybindings.append(path)

    media_keys.set_strv('custom-keybindings', new_keybindings)
    Gio.Settings.sync()

def keybind_kde(toggle: Optional[List[str]], quit: Optional[List[str]]):
    """Configure keybindings for KDE."""
    raise NotImplementedError('kwriteconfig is not yet supported')

def no_keybind_kde():
    """Remove keybindings for KDE."""
    raise NotImplementedError('kwriteconfig is not yet supported')

def keybind_autodetect(toggle: Optional[List[str]], quit: Optional[List[str]]):
    """Configure keybindings for the current desktop environment."""
    _autodetect(
        partial(keybind_gnome, toggle, quit),
        partial(keybind_kde, toggle, quit),
    )

def no_keybind_autodetect():
    """Remove keybindings for the current desktop environment."""
    _autodetect(no_keybind_gnome, no_keybind_kde)

def _autodetect(gnome, kde):
    """
    Detect whether the current desktop environment is GNOME or KDE
    and invoke the corresponding function.
    """
    environment = getenv('XDG_CURRENT_DESKTOP')
    if environment == 'GNOME' or environment == 'ubuntu:GNOME':
        gnome()
    elif environment == 'KDE':
        kde()
    else:
        reason = 'XDG_CURRENT_DESKTOP is unset' if environment is None else f'\'{environment}\''
        raise RuntimeError(f'Unknown desktop environment: {reason}')

def _compile_actions(**kwargs) -> Dict[str, str]:
    """
    Given keyword arguments mapping action names (i.e. `Toggle` or `Quit`)
    to lists of keyboard shortcut strings (e.g. `<Super>Return`),
    return a list of doubles,
    where the the first element of each double is a single shortcut string,
    and the second element is the associated action.
    """
    binding_action_list = [
        (binding, action)
        for action, bindings in kwargs.items()
        if bindings is not None
        for binding in bindings
    ]
    binding_action_dict = dict(binding_action_list)
    if len(binding_action_list) > len(binding_action_dict):
        raise ValueError('Cannot use the same binding for multiple actions')
    return binding_action_list
