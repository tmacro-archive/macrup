from .error import RequiredArguementError
from .rclone import RClone
from .conf import config, loadYAML
from itertools import chain
from datetime import datetime
from .util import convert_delta
import yaml
import getpass
from hashlib import blake2b
from pathlib import PosixPath
from os.path import expanduser

class Directory(RClone):
	def __init__(self, path = None, ts = None, exclude = [], prefix = None, remote = None, dry_run = False, bucket = None):
		if not path:
			raise RequiredArguementError('You must provide a directory path!')
		if not remote:
			raise RequiredArguementError('You must provide a remote!')
		
		self._path = path
		self._last_sync = ts
		self._exclude = exclude
		self._prefix = prefix
		self._bucket = bucket
		super().__init__(remote, dry_run)
		
	def __repr__(self):
		return 'Directory(path=%s, synced=%s, bucket=%s)'%(self.name, self.synced, self.bucket)
	@property
	def bucket(self):
		if not self._bucket:
			return '%s-%s'%(self._prefix, self._path.name)
		return self._bucket

	@property
	def synced(self):
		if self._last_sync is not None:
			return self._last_sync
		return datetime(month=1, day=1, year=1)

	def push(self):
		if self._push(self.name, self.bucket, excludes = self._exclude):
			self._last_sync = datetime.now()
			return True
		return False
			
	def pull(self):
		if self._pull(self.name, self.bucket, excludes = self._exclude):
			self._last_sync = datetime.now()
			return True
		return False

	@property
	def name(self):
		if self._path.is_absolute():
			return self._path.as_posix()
		return self._path.home().joinpath(self._path).as_posix()

	@property
	def path(self):
		if self._path.is_absolute():
			return self._path
		return self._path.home().joinpath(self._path)

class Backup:
	def __init__(self, func):
		self._func = func
		self._user = getpass.getuser()
		self._statefile = expanduser(config.state_path)
		
		
	def __call__(self, ctx, remote, watched = [], exclude = [], prefix = None, notify = False, dry_run = False, freq = None):
		self._remote = remote if remote else config.remote
		self._exclude = config.exclude
		prefix = prefix if prefix else config.prefix
		if prefix is None:
			prefix = blake2b(self._user.encode('utf-8')).hexdigest()[:10]
		self._prefix = prefix
		self._dry_run = dry_run
		self._notify = notify if notify else getattr(config, 'pushbullet', None) is not None
		self._watched = self._build_watched(watched, exclude) 
		freq = config.frequency if not freq else freq
		self._freq = convert_delta(freq)

		ctx.obj = self
		return self._func(ctx)

	def _load_state(self):
		saved = loadYAML(self._statefile)
		if saved is None:
			return []
		loaded = []
		for directory in saved:
			loaded.append(Directory(path = directory['path'], ts = directory['synced'], bucket = directory['bucket'], remote = self._remote))
		return loaded
		

	def _save_state(self):
		with open(self._statefile, 'w') as state_file:
			yaml.dump([dict(
				path = d.path,
				bucket = d.bucket, 
				synced = d.synced) for d in self.watched],
				state_file,
				default_flow_style=False)

	def _load_watched(self):
		in_conf = getattr(config, 'watched', [])
		configured = []
		for p in in_conf:
			if p.is_absolute():
				configured.append(p)
			else:
				configured.append(p.home().joinpath(p))
		watched = {d.name:d for d in self._load_state()}
		for entry in configured:
			if not entry.resolve().as_posix() in watched:
				watched[entry] = Directory(path = entry, prefix=self._prefix, remote=self._remote, dry_run=self._dry_run)
		return watched

	def _build_watched(self, extra, exclude):
		extra = {PosixPath(d).resolve().as_posix(): exclude for d in extra}
		common = dict(prefix = self._prefix, remote = self._remote, dry_run = self._dry_run)
		watched = self._load_watched()
		for path, exclude in extra.items():
			if not path in watched:
				watched[path] = Directory(path = path, exclude = exclude, **common)
		return list(watched.values())

	@property
	def watched(self): 
		for directory in self._watched:
			yield directory

	@property
	def outdated(self):
		now = datetime.now()
		for directory in self.watched:
			if  now - directory.synced > self._freq:
				yield directory

	@property
	def notify(self):
		return self._notify

	def save(self):
		self._save_state()



