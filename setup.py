from setuptools import setup

setup(
	name='dist-builder',
	version='0.2.0',
	description='Build a wheel and source distribution and bundle with other files in a zip',
	url='https://github.com/dnut/dist-builder/',
	author='Drew Nutter',
	author_email='drew@drewnutter.com',
	license='GPLv3',
	py_modules=['dist_builder'],
	install_requires=[],
	zip_safe=False
)
