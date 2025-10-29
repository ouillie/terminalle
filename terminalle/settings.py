"""Loading and validating settings configurations."""

from os import getcwd, getenv
from os.path import expandvars

from gi.repository import Gdk, Pango
from yaml import safe_load

_defaults = {
    # (string) path to shell binary e.g. `${HOME}/bash`
    'shell': getenv('SHELL', '/bin/sh'),
    # (string) initial home directory e.g. `${HOME}` or `/tmp`
    'home': getcwd(),
    # (string) must be valid input for `Pango.font_description_from_string()`
    'font': 'monospace 13',
    # (array) must have length either 8, 16, 232, or 256:
    # - first 8 are the main colors
    # - next 8 are the bright colors
    # - next 216 are the 6x6x6 color cube
    # - next 24 are grayscale
    # each color is either:
    # - a valid string for Gdk.RGBA().parse()
    # - a list of 1 (R=G=B, A=1), 3 (A=1), or 4 number values
    # each number being either:
    # - an integer between 0 and 255
    # - a float between 0.0 and 1.0
    # default: solarized dark with pure black background
    # and brighter high-intensity black
    'colors': [
        '#000000',  # black
        '#dc322f',  # red
        '#859900',  # green
        '#b58900',  # yellow
        '#268bd2',  # blue
        '#d33682',  # magenta
        '#2aa198',  # cyan
        '#eee8d5',  # white
        # high-intensity
        '#4e4e61',  # black
        '#cb4b16',  # red
        '#586e75',  # green
        '#657b83',  # yellow
        '#839496',  # blue
        '#6c71c4',  # magenta
        '#93a1a1',  # cyan
        '#fdf6e3',  # white
    ],
    # (number) window opacity beween 0.0 and 1.0 or 0 and 100
    'opacity': 0.75,
    # (bool) whether to automatically hide the window when it loses keyboard focus
    'autohide': True,
    # (bool) whether to enable recommended hardwired tmux shortcuts
    'tmux': False,
}
_valid_colors_lengths = {8, 16, 232, 256}


def load(path: str):
    """Return normalized settings loaded from a YAML file."""
    try:
        with open(path) as f:
            attrs = safe_load(f)
        assert isinstance(attrs, dict)
    except Exception:
        return _normalize()
    # change hyphenated-keys to underscored_keys
    return _normalize(**{key.replace('-', '_'): value for key, value in attrs.items()})


def _normalize(
    shell: str = _defaults['shell'],
    home: str = _defaults['home'],
    font: str = _defaults['font'],
    colors: list = _defaults['colors'],
    opacity: float = _defaults['opacity'],
    autohide: bool = _defaults['autohide'],
    tmux: bool = _defaults['tmux'],
    **kwargs,
):
    """
    Return a normalized version of the settings configuration.
    Raise `InvalidSettingsError` if the settings are invalid.
    """
    if len(kwargs) > 0:
        raise InvalidSettingsError(f'unexpected attributes {kwargs}')
    if len(colors) not in _valid_colors_lengths:
        raise InvalidSettingsError(
            f'colors length ({len(colors)}) must be one of {{_valid_colors_lengths}}'
        )
    _opacity = _normalize_number(opacity, 100)
    if _opacity is None:
        raise InvalidSettingsError(f'opacity ({opacity}) must be a percentage number')
    return {
        'shell': _normalize_type(expandvars(shell), str, 'shell'),
        'home': _normalize_type(expandvars(home), str, 'home'),
        'font': _normalize_font(font),
        'colors': [_normalize_color(c) for c in colors],
        'opacity': _opacity,
        'autohide': _normalize_bool(autohide, 'autohide'),
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
    raise InvalidSettingsError(f'font ({font}) must be a string font description')


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
        f'color ({color}) must be a string or list of RGBA values'
    )


def _normalize_number(number, intmax):
    if isinstance(number, float) and 0.0 <= number <= 1.0:
        return number
    elif isinstance(number, int) and 0 <= number <= intmax:
        return number / intmax
    return None  # the number is invalid


def _normalize_bool(value, name):
    if isinstance(value, bool):
        return value
    raise InvalidSettingsError(f'{name} ({value}) must be a boolean')


class InvalidSettingsError(Exception):
    """Indicates that the settings configuration is invalid."""

    pass
