import os
from setuptools import setup

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(THIS_DIR, 'README.md')) as f:
    long_description = f.read()

setup(
	name='dist-builder',
	version='0.2.4',
	description='Build a wheel and source distribution and bundle with other files in a zip',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/dnut/dist-builder/',
	author='Drew Nutter',
	author_email='drew@drewnutter.com',
	license='GPLv3',
	py_modules=['dist_builder'],
	install_requires=[],
	zip_safe=False
)
