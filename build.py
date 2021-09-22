""" Build backend wrapper to expand template files before invoking setuptools. """

from os import walk
from datetime import date
from pathlib import Path
from string import Template
from functools import wraps
from typing import Callable
from setuptools import build_meta

import terminalle

_mapping = {
    'VERSION': terminalle.__version__,
    'DESCRIPTION': terminalle.__description__,
    'LICENSE': terminalle.__license__,
    'AUTHOR': terminalle.__author__,
    'EMAIL': terminalle.__email__,
    'URL': terminalle.__url__,
    'DATE': date.today().strftime('%Y-%m-%d'),
}

def _render_templates_first(f: Callable) -> Callable:
    @wraps(f)
    def aux(*args, **kwargs):
        for root, _, filenames in walk('.'):
            for filepath in map(Path, filenames):
                if filepath.suffix == '.in':
                    filepath = Path(root).joinpath(filepath)
                    with open(filepath, 'r') as file:
                        template = Template(file.read())
                    with open(filepath.with_suffix(''), 'w') as file:
                        file.write(template.substitute(_mapping))
        return f(*args, **kwargs)
    return aux

build_wheel = _render_templates_first(build_meta.build_wheel)
build_sdist = _render_templates_first(build_meta.build_sdist)
get_requires_for_build_wheel = build_meta.get_requires_for_build_wheel
get_requires_for_build_sdist = build_meta.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = build_meta.prepare_metadata_for_build_wheel
