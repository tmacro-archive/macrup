import yaml
import sys
import logging
import os
import os.path
from collections import namedtuple
from .error import NoConfigError
from datetime import datetime
from pathlib import PosixPath

# These can be overridden in the config file.
# They are just here some sensible defaults
# so the module shill functions
BUILT_IN_DEFAULTS = {
			'meta':{
				"version": "dev_build",
				"app" : "macrup",
				},
			'logging': {
				"logfile" : None,
				"loglvl" : "debug",
				"log_rotation": False,
				"logfmt" : '%(asctime)s %(name)s %(levelname)s: %(message)s',
				"datefmt" : '%d-%m-%y %I:%M:%S %p',
				'whitelist': [],
				'blacklist': []
				},
			'_dump': True	# If True and the loaded config is empty
}							# 	Write out BUILT_IN_DEFAULTS and APP_DEFAULTS to the config after merging
							# Keys prefaced with a '_' will not be written

# Intert default values for app config here
# instead of mixing them with BUILT_IN_DEFAULTS
# These can be use to override BUILT_IN_DEFAULTS as well
APP_DEFAULTS = {
	'remote': None,
	'watched': [],
	'exclude': [],
	'prefix': None,
	'notify': False,
	'pushbullet': None,
	'frequency': '1d',
	'timestamp': '%y:%m:%d:%H:%M:%S'
}

BUILT_IN_DEFAULTS.update(APP_DEFAULTS)

def parseLogLevel(text, default = 30):
	text = text.lower()
	levelValues = dict(
				critical = logging.CRITICAL,
				error = logging.ERROR,
				warning = logging.WARNING,
				info = logging.INFO,
				debug = logging.DEBUG
				)
	return levelValues.get(text, default)

def recursivelyUpdateDict(orig, new):
	updated = orig.copy()
	updateFrom = new.copy()
	for key, value in updated.items():
		if key in new:
			if not isinstance(value, dict):
				updated[key] = updateFrom.pop(key)
			else:
				updated[key] = recursivelyUpdateDict(value, updateFrom.pop(key))
	for key, value in updateFrom.items():
		updated[key] = value
	return updated

def createNamespace(mapping, name = 'config'):
	data = {}
	for key, value in mapping.items():
		if not isinstance(value, dict):
			data[key] = value
		else:
			data[key] = createNamespace(value, key)
	nt = namedtuple(name, list(data.keys()))
	return nt(**data)

def loadYAML(path):
	try:
		with open(path) as configFile:
			return yaml.load(configFile)
	except Exception as e:
		pass
	return None

def loadConfig(path = None):
	defaults = {k: v for k, v in BUILT_IN_DEFAULTS.items() if not k[0] == '_'}
	loadedConfig = loadYAML(path) if path is not None else {}
	if loadedConfig is None and BUILT_IN_DEFAULTS['_dump'] and path:
		loadedConfig = {}
		with open(path, 'w') as cf:
			yaml.dump(defaults, cf, default_flow_style=False)
	config = recursivelyUpdateDict(defaults, loadedConfig)
	config['logging']['loglvl'] = parseLogLevel(config['logging']['loglvl']) # Parse the loglvl
	return createNamespace(config) # Return the config for good measure

path = os.path.expanduser('~') + '/.macrup.yaml'


config_path = os.path.expanduser('~') + '/.macrup.yaml'
config = loadConfig(config_path)

class YAMLTime(yaml.YAMLObject):
	yaml_tag = '!timestamp'
	ts_format = '%y:%m:%d:%H:%M:%S'

	def __init__(self, timestamp):
		self._timestamp = timestamp

	def __repr__(self):
		return self._timestamp.strftime(YAMLTime.ts_format)

	@classmethod
	def to_yaml(cls, dumper, data):
		return dumper.represent_scalar('!timestamp', data._timestamp.strftime(YAMLTime.ts_format))

	@classmethod
	def from_yaml(cls, loader, node):
		ts = loader.construct_scalar(node)
		return cls(datetime.strptime(ts, YAMLTime.ts_format))

class YAMLPath(yaml.YAMLObject):
	yaml_tag = '!path'

	def __init__(self, path):
		self.path = path

	def __repr__(self):
		return self.path.as_posix()

	@classmethod
	def to_yaml(cls, dumper, data):
		return dumper.represent_scalar('!path', data.path.as_posix())

	@classmethod
	def from_yaml(cls, loader, node):
		path = loader.construct_scalar(node)
		return cls(PosixPath(path))

class DirBackup(yaml.YAMLObject):
	yaml_tag = '!backup'
	def __init__(self, **kwargs):
		self.path = kwargs.get('path')
		self.last_synced = kwargs.get('last_synced')
		self.bucket = kwargs.get('bucket')

	def __repr__(self):
		return '%s(path=%s, last_synced=%s, bucket=%s'%(self.__class__.__name__,
							self.path, self.last_synced, self.bucket)

	@classmethod
	def to_yaml(cls, dumper, data):
		return dumper.represent_mapping('!backup', dict(path = data.path, 
										last_synced = data.last_synced,
										bucket = data.bucket))

	@classmethod
	def from_yaml(cls, loader, node):
		dir = loader.construct_mapping(node)
		return cls(**dir)
