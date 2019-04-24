from setuptools import setup

setup(
	name='dist-builder',
	version='0.1',
	description='Build a wheel and source distribution and bundle with other files in a zip',
	url='https://github.com/dnut/dist-builder/',
	author='Drew Nutter',
	author_email='n/a',
	license='GPLv3',
	packages=[],
	scripts=['dist_builder.py'],
	install_requires=[],
	zip_safe=False
)
