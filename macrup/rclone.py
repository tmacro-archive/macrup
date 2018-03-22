from .conf import config
import subprocess
from threading import Thread, Event
import shlex
from .log import Log
import urllib.request

_log = Log('rclone.process')




# Sync local to remote,  'deletes' files if they're deleted localy
# rclone

class RClone:
	def __init__(self, remote, dry_run = False):
		self._remote = remote
		self._dry_run = dry_run

	def _build_excludes(self, *args):
		return ' '.join(["--exclude '%s'"%ex for ex in args])

	def _mkdir(self, bucket):
		cmd = '/usr/bin/rclone mkdir %s:%s'%(self._remote, bucket)
		proc = WatchProcess(cmd)
		return proc.wait()

	def _sync(self, src, dest, excludes = [], verbose = True):
		dry_run = '--dry-run' if self._dry_run else ''
		cmd = '/usr/bin/rclone %s %s sync %s %s'%(dry_run, self._build_excludes(*excludes), src, dest)

		def _on_exit(rc):
			if rc == 0:
				_log.info('Done Syncing')

		def _on_error(rc):
			_log.error('rclone exited with %s, using cmd %s'%(rc, cmd))

		_log.info('Syncing %s to %s'%(src, dest))
		_log.debug('Using command "%s"'%cmd)
		proc = WatchProcess(cmd, on_exit = _on_exit, on_error = _on_error)
		proc.wait()
		return proc.wait() == 0

	def _push(self, local, bucket, excludes = []):
		return self._sync(local, '%s:%s'%(self._remote, bucket), excludes)

	def _pull(self, local, bucket, excludes = []):
		return self._sync('%s:%s'%(self._remote, bucket), local, excludes)



class WatchedProcess(Thread):
	"""
		A light wrapper around a Popen object

		all args are passed through to the Popen constructor

		2 additional keyword arguments are added
			on_exit
			on_error
		These should contain a callable object taking 1 arguement return_code
		on_exit will always be called when the process exits
		on_error will be called when the process exits with return_code != 0
	"""

	def __init__(self, *args, on_exit = None, on_error = None, **kwargs):
		super().__init__()
		self.daemon = True
		self._proc = None
		self._started = Event()
		self._args = args
		self._kwargs = kwargs
		self._on_exit = on_exit
		self._on_error = on_error
		self._proc = subprocess.Popen(*self._args, **self._kwargs)

	def __call__(self):
		"""for convenience return the popen object when called"""
		return self._proc

	def run(self):
		self._started.set()
		self._proc.wait()
		rc = self._proc.returncode
		if self._on_exit:
			self._on_exit(rc)
		if self._on_error and rc != 0:
			self._on_error(rc)

	def terminate(self):
		return self._proc.terminate()

	def kill(self):
		return self._proc.kill()

	@property
	def status(self):
		if self._proc:
			return self._proc.poll()

	def wait(self):
		self._started.wait()
		# print(self._proc)
		return self._proc.wait() if self._proc else None


def WatchProcess(cmd, start = True, **kwargs):
	_log.debug('Creating watched process, "%s"'%cmd)
	wp = WatchedProcess(shlex.split(cmd), **kwargs)
	if start:
		_log.debug("Starting process...")
		wp.start()
	return wp
