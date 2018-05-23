import getpass
from hashlib import blake2b
from pathlib import PosixPath

from yaml.scanner import ScannerError

from .conf import config
from .error import InvalidConfigError, NoConfigError, UnknownError
from .log import Log
from .rclone import RClone

_log = Log('user')

class User:
	def __init__(self, watched = [], exclude = [], prefix = None, notify = None, dryrun = False):
			self._dry_run = dry_run
			self._home = PosixPath.home()
			self._user = user = getpass.getuser()
			self._watched = [self._home.joinpath(p) for p in config.watched]
			self._exclude = config.exclude if config.exclude else []
			self._prefix = config.prefix if config.prefix else blake2b(user.encode('utf-8')).hexdigest()[:10]
			self._notify = config.pushbullet if config.notify else None











class Backup:
	def __init__(self, dry_run = False):
		try:
			self.setRemote(config.remote)
		except FileNotFoundError as fnf:
			raise NoConfigError from fnfe
		except ScannerError as se:
			raise InvalidConfigError from se
		except Exception as e:
			raise UnknownError from e

	@property
	def watched(self):
		return self._watched

	@property
	def notify(self):
		return self._notify is not None

	@property
	def pushbullet(self):
		return self._notify

	def _bucket_for(self, path):
		# buckets are generated in the format prefix-user-path
		return '-'.join([self._prefix, self._user, path.name])

	def _backup(self, path, bucket = None):
		bucket = self._bucket_for(path) if bucket is None else bucket
		return self._rclone._push(path, bucket, excludes = self._exclude)

	def _restore(self, path, bucket = None):
		bucket = self._bucket_for(path) if bucket is None else bucket
		return self._rclone._pull(path, bucket, excludes = self._exclude)

	def _add_watch(self, path):
		self._watched.append(self._home.joinpath(path))

	def addWatched(self, p):
		return self._add_watch(p)

	def setRemote(self, remote):
		self._remote = remote
		self._rclone = RClone(remote, dry_run = self._dry_run)
