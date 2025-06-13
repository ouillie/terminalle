from ast import Assign, Constant, Name, parse, walk
from datetime import date
from os.path import join as join_path

from setuptools import setup
from setuptools.command.build_py import build_py

class BuildPreprocessed(build_py):
    def run(self):
        # Format the man page template
        # with the version from `__init__.py` and the current date.
        with open('terminalle.1.in', 'r') as man_template:
            man = man_template.read()
        man = man.format(
            version=read_version(join_path('terminalle', '__init__.py')),
            date=date.today().isoformat(),
        )
        with open('terminalle.1', 'w') as man_file:
            man_file.write(man)

        # Continue to the normal build process using the generated man page.
        super().run()

def read_version(path):
    """
    Read the module version from an `__init__.py` file.

    Parses the file source rather than importing the module
    because importing would require satisfying dependencies.
    """
    with open(path, 'r') as init_file:
        init = init_file.read()
    for node in walk(parse(init)):
        if isinstance(node, Assign):
            if any(
                isinstance(target, Name) and target.id == '__version__'
                for target in node.targets
            ):
                if isinstance(node.value, Constant) and isinstance(node.value.value, str):
                    return node.value.value
                else:
                    raise RuntimeError('Cannot handle complex expression for __version__')

setup(cmdclass={'build_py': BuildPreprocessed})
