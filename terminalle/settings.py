""" Loading and validating settings configurations.

- shell : str
  * path to shell binary e.g. '$HOME/bash'
  * default: getenv('SHELL', '/bin/sh')
- home : str
  * initial home directory e.g. '/tmp' or '$HOME'
  * default: current working directory of caller
- font : str | Pango.FontDescription
  * must be valid input for Pango.font_description_from_string()
  * default: 'Source Code Pro 13'
- colors : [str | [int | float] | Gdk.RGBA]
  * must have length either 8, 16, 232, or 256:
    > first 8 are the main colors
    > next 8 are the bright colors
    > next 216 are the 6x6x6 color cube
    > next 24 are grayscale
  * each color is either:
    > a valid string for Gdk.RGBA().parse()
    > a list of 1 (R=G=B, A=1), 3 (A=1), or 4 number values,
      each being either:
      - an integer between 0 and 255
      - a float between 0.0 and 1.0
  * default: solarized dark with pure black background
- opacity : float | int
  * window opacity beween 0.0 and 1.0 or 0 and 100
  * default: 0.75
- tmux : bool
  * whether to enable recommended hardwired tmux shortcuts
  * default: false
"""

from os import getenv, getcwd
from os.path import expandvars

from yaml import safe_load
from gi.repository import Gdk, Pango

def load(path:str):
    """ Return normalized settings loaded from a YAML file. """
    try:
        with open(path) as f:
            attrs = safe_load(f)
        assert isinstance(attrs, dict)
    except:
        return normalize()
    # change hyphenated-keys to underscored_keys
    return normalize(**{key.replace('-', '_'): value
                        for key, value in attrs.items()})

_defaults = {
    'shell': getenv('SHELL', '/bin/sh'),
    'home': getcwd(),
    'font': 'Source Code Pro 13',
    # just solarized-dark with deeper black
    'colors': [
        # black red green yellow
        '#000000', '#dc322f', '#859900', '#b58900',
        # blue magenta cyan white
        '#268bd2', '#d33682', '#2aa198', '#eee8d5',
        # high-intensity
        '#002b36', '#cb4b16', '#586e75', '#657b83',
        '#839496', '#6c71c4', '#93a1a1', '#fdf6e3',
    ],
    'opacity': 0.75,
    'tmux': False,
}
_valid_colors_lengths = {8, 16, 232, 256}

def normalize(shell: str = _defaults['shell'],
              home: str = _defaults['home'],
              font: str = _defaults['font'],
              colors: list = _defaults['colors'],
              opacity: float = _defaults['opacity'],
              tmux: bool = _defaults['tmux'],
              **kwargs):
    """
    Return a normalized version of the settings configuration.
    Raise InvalidSettingsError if the settings are invalid.
    """
    if len(kwargs) > 0:
        raise InvalidSettingsError(f'unexpected attributes {kwargs}')
    if len(colors) not in _valid_colors_lengths:
        raise InvalidSettingsError(f'colors length ({len(colors)}) ' \
                                   'must be one of {_valid_colors_lengths}')
    _opacity = _normalize_number(opacity, 100)
    if _opacity is None:
        raise InvalidSettingsError(
            f'opacity ({opacity}) must be a percentage number')
    return {
        'shell': _normalize_type(expandvars(shell), str, 'shell'),
        'home': _normalize_type(expandvars(home), str, 'home'),
        'font': _normalize_font(font),
        'colors': [_normalize_color(c) for c in colors],
        'opacity': _opacity,
        'tmux': _normalize_bool(tmux, 'tmux'),
    }

def _normalize_type(value, type, name):
    if isinstance(value, type):
        return value
    raise InvalidSettingsError(f'{name} ({value}) must be {type}')

def _normalize_font(font):
    if isinstance(font, Pango.FontDescription):
        return font
    elif isinstance(font, str):
        return Pango.font_description_from_string(font)
    raise InvalidSettingsError(
        f'font ({font}) must be a string font description')

def _normalize_color(color):
    if isinstance(color, Gdk.RGBA):
        return color
    elif isinstance(color, str):
        c = Gdk.RGBA()
        if c.parse(color):
            return c
    elif isinstance(color, list):
        if len(color) == 1:
            value = _normalize_number(color[0], 255)
            if value is not None:
                return Gdk.RGBA(value, value, value)
        elif len(color) == 3 or len(color) == 4:
            values = [_normalize_number(n, 255) for n in color]
            if all(v is not None for v in values):
                return Gdk.RGBA(*values)
    raise InvalidSettingsError(
        f'color ({color}) must be a string or list of RGBA values')

def _normalize_number(number, intmax):
    """ Return 0.0 <= number <= 1.0 or None if the number is invalid. """
    if isinstance(number, float) and 0.0 <= number <= 1.0:
        return number
    elif isinstance(number, int) and 0 <= number <= intmax:
        return number / intmax
    return None

def _normalize_bool(value, name):
    if isinstance(value, bool):
        return value
    raise InvalidSettingsError(f'{name} ({value}) must be a boolean')

class InvalidSettingsError(Exception):
    """ Indicates that the settings configuration is invalid. """
    pass
