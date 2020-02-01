from setuptools import setup

setup(name='terminalle',
      version='1.0',
      author='Will Noble',
      author_email='code@will.party',
      description='A fancy drop-down terminal emulateur',
      url='https://github.com/wm-noble/terminalle',
      packages=['terminalle'],
      package_data={'terminalle': ['org.gnome.Terminalle.service']},
      python_requires='>=3.6')
