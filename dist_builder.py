import ast
import imp
import os
import re
import shutil
import sys
import zipfile
from collections import namedtuple
from contextlib import contextmanager
from io import StringIO
try:
	from configparser import ConfigParser
except ImportError:
	from ConfigParser import ConfigParser
	ConfigParser.read_file = ConfigParser.readfp


def main(args=sys.argv[1:]):
	config = load_config(args)
	with temporarily_cd_to(config.repo_root):
		builder = Builder(**config.build._asdict())
		build_result = builder.build()
		bundler = bundler_factory(build_result, config.bundle)
		bundler.bundle()


def load_config(args):
	# todo command line arguments for everything in build.ini
	# todo don't create a bundle if it's only going to be a wheel inside? maybe
	#  this should be the default, but if the user expicitly wants a zip, then zip
	config = ConfigParser()
	defaults = u'''
		[repo]
		root = .
		
		[build]
		dist_dir  = dist/
		setup_py  = setup.py
		
		[bundle]
		format =
		include_source = false
		dirs:
		files:
	'''.replace('\t', '')
	config.read_file(StringIO(defaults))
	try:
		build_ini = find_build_ini(args)
	except OSError:
		print('No build.ini found, using defaults.')
		workdir = os.getcwd()
	else:
		config.read(build_ini)
		workdir = os.path.dirname(build_ini)
	repo_root = os.path.abspath(os.path.join(workdir, config.get('repo', 'root')))
	return Config(
		repo_root=repo_root,
		build=BuildConfig(
			dist_dir=config.get('build', 'dist_dir'),
			setup_py=os.path.join(repo_root, config.get('build', 'setup_py')),
		),
		bundle=BundleConfig(
			format=config.get('bundle', 'format').lower(),
			include_source=config.getboolean('bundle', 'include_source'),
			dirs=[f for f in config.get('bundle', 'dirs').splitlines() if f != ''],
			files=[f for f in config.get('bundle', 'files').splitlines() if f != ''],
		)
	)


def find_build_ini(args):
	if len(args) == 0:
		return find('.', 'build.ini')
	elif len(args) == 1:
		if os.path.isfile(args[0]):
			return args[0]
		else:
			raise OSError('File not found: {}'.format(args[0]))
	raise ValueError('Too many cli arguments: {}'.format(args))
	

def bundler_factory(build_result, config):
	files = config.files + [build_result.wheel]
	target = build_result.wheel.rstrip('.whl')
	if config.include_source is True:
		files.append(build_result.source)
	return Bundler(target, config.format, config.dirs, files)


Config = namedtuple('Config', 'repo_root build bundle')
BuildConfig = namedtuple('BuildConfig', 'dist_dir setup_py')
BundleConfig = namedtuple('BundleConfig', 'format include_source dirs files')
BuildResult = namedtuple('BuildResult', 'wheel source')


class BundleFormat:
	ZIP = 'zip'
	NONE = ''


class Builder(object):
	def __init__(self, dist_dir, setup_py):
		self.dist_dir = dist_dir
		self.setup_py = setup_py
		self.dist_name = SetupPyParser(setup_py).get_dist_name()

	def build(self):
		underscore_dist_name = self.dist_name.replace('-', '_')
		setup_py_dir = os.path.split(self.setup_py)[0]
		abs_dist_dir = os.path.abspath(self.dist_dir)
		with temporarily_cd_to(setup_py_dir):
			self.setup('sdist', '--dist-dir=' + abs_dist_dir, 'clean', '--all')
			self.setup('bdist_wheel', '--dist-dir=' + abs_dist_dir, 'clean', '--all')
			try:
				deleteme = find('.', underscore_dist_name + '.egg-info')
			except OSError:
				pass
			else:
				shutil.rmtree(deleteme)
		return BuildResult(
			self._find_dist(underscore_dist_name, '.whl'),
			self._find_dist(self.dist_name, '.tar.gz'),
		)
	
	def setup(self, *args):
		orig_argv = sys.argv
		sys.argv[1:] = args
		try:
			imp.load_source('setup', self.setup_py)
		finally:
			sys.argv = orig_argv
	
	def _find_dist(self, underscore_dist_name, extension):
		return find(self.dist_dir, '{}-.*{}'.format(underscore_dist_name, extension))


class Bundler(object):
	def __init__(self, target, format, dirs, files):
		# todo: handle (source, target) using arcname
		self.target = target
		self.format = format
		self.dirs = dirs
		self.files = files
	
	def bundle(self):
		# todo add tar.gz, maybe implement formats with plugin classes
		if self.format == BundleFormat.ZIP:
			self.build_zip(self.target, self.dirs, self.files)
		elif self.format == BundleFormat.NONE:
			print('bundle format NONE, skipping bundle step')
		else:
			raise ValueError('Invalid format selected: ' + self.format)
	
	@classmethod
	def build_zip(cls, target, dirs, files):
		with zipfile.ZipFile(target + '.zip', mode='w') as z:
			for dir_ in dirs:
				cls.zipdir(z, dir_)
			for file_ in files:
				z.write(file_)
	
	@staticmethod
	def zipdir(z, path):
		for root, dirs, files in os.walk(path):
			for file in files:
				z.write(os.path.join(root, file))


def find(direc, pattern):
	# todo recursive, handle multiple
	for file_ in os.listdir(direc):
		fullpath = os.path.join(direc, file_)
		if re.match(pattern, file_) and os.path.exists(fullpath):
			return fullpath
	raise OSError('No file found matching ' + pattern)


@contextmanager
def temporarily_cd_to(directory):
	original_working_directory = os.getcwd()
	os.chdir(directory)
	try:
		yield
	finally:
		os.chdir(original_working_directory)


class SetupPyParser(object):
	def __init__(self, path):
		with open(path) as f:
			s = f.read()
		self.ast_root = ast.parse(s, filename=os.path.basename(path))
	
	def get_dist_name(self):
		call = self._locate_setup_call(self.ast_root)
		return self._get_name_from_setup_call(call)
	
	@staticmethod
	def _locate_setup_call(ast_node):
		# todo find setup() even if it's not assigned the name "setup"
		# todo search recursively
		for item in ast_node.body:
			if isinstance(item, ast.Expr) and isinstance(item.value, ast.Call):
				if item.value.func.id == 'setup':
					return item.value
	
	@staticmethod
	def _get_name_from_setup_call(setup_call):
		for kwarg in setup_call.keywords:
			if kwarg.arg == 'name':
				return kwarg.value.s
		raise KeyError('setup() call has no kwarg called name')


if __name__ == '__main__':
	main()
