""" Build backend wrapper to expand template files before invoking setuptools. """

from os import walk
from datetime import date
from pathlib import Path
from string import Template
from functools import wraps
from ast import parse, Name, Assign, literal_eval
from typing import Callable
from setuptools import build_meta

_attr_mapping = {'__version__': 'VERSION',
                 '__description__': 'DESCRIPTION',
                 '__license__': 'LICENSE',
                 '__author__': 'AUTHOR',
                 '__email__': 'EMAIL',
                 '__url__': 'URL'}
with open('terminalle/__init__.py', 'r') as file:
    _mapping = {name: literal_eval(node.value)
                for node in parse(file.read()).body
                if isinstance(node, Assign)
                for attr, name in _attr_mapping.items()
                if any(isinstance(target, Name) and target.id == attr
                       for target in node.targets)}
_mapping['DATE'] = date.today().strftime('%Y-%m-%d')
del _attr_mapping

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
