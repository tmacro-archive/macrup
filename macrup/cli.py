import click
# from .user import Backup
from .backup import Backup
import macrup.notify as notify
import yaml
import urllib.request
from .log import Log
from .conf import config
from .util import RequiredIf
_log = Log('cli')

def checkConnection():
	try:
		urllib.request.urlopen('https://google.com')
	except Exception as e:
		return False
	return True

@click.group()
@click.option('--remote', '-r', type = str, default = None)
@click.option('--watched', '-w', type = str, default = None, multiple = True)
@click.option('--exclude', '-x', type = str, default = None, multiple = True)
@click.option('--prefix', '-p', type = str, default = None)
@click.option('--notify', '-n', is_flag = True)
@click.option('--dry-run', is_flag = True)
@click.pass_context
@Backup
def macrup(ctx):
	# _log.debug(list(ctx.obj.watched))
	pass

@macrup.command()
@click.pass_context
def backup(ctx):
	'''Backup a directory'''
	if not checkConnection():
		click.echo('No internet connection detected, delaying backup.')
		exit(0)
	if not ctx.obj.watched:
		click.echo('No watched directories')
	if not list(ctx.obj.outdated):
		click.echo('Up to date!')
		return 0
	failed = []
	for directory in ctx.obj.outdated:
		if not directory.push():
			failed.append(directory)
	ctx.obj.save()
	if failed:
		click.echo("Some directories failed to sync!")
		if ctx.obj.notify:
			if config.pushbullet is None:
				click.echo('You must supply a Pushbullet API key to enable push notifications!')
				exit(1)
			print(config.pushbullet)
			notify.push(config.pushbullet, 'note', title = 'Macrup', body = 'Failed Sync\n' + '\n'.join([d.name for d in failed]))
	else:
		if ctx.obj.notify:
			if config.pushbullet is None:
				click.echo('You must supply a Pushbullet API key to enable push notifications!')
				exit(1)
			notify.push(config.pushbullet, 'note', title = 'Macrup', body = 'Successful Sync')
			


@macrup.command()
@click.pass_obj
@click.option('--bucket', '-b', help = 'bucket to pull from', required = False)
@click.option('--dest', '-d', cls = RequiredIf, help = 'destination directory', required_if = 'bucket')
def restore(backup, bucket, dest):
	'''Restore a bucket to a directory'''
	if not checkConnection():
		click.echo('No internet connection detected, can not restore.')
		exit(0)
	# if bucket and not dest:
	# 	raise click.BadArgumentUsage('You must provide a destination if a bucket is specified!')
	if not backup.watched:
		click.echo('No watched directories')
	failed = []
	for directory in backup.watched:
		if not directory.pull():
			failed.append(directory)
	if failed:
		click.echo("Some directories failed to sync!")
		if backup.notify:
			if config.pushbullet is None:
				click.echo('You must supply a Pushbullet API key to enable push notifications!')
				exit(1)
			notify.push(config.pushbullet, 'note', title = 'Macrup', body = 'Failed Sync\n' + '\n'.join([d.name for d in failed]))
	else:
		if backup.notify:
			if config.pushbullet is None:
				click.echo('You must supply a Pushbullet API key to enable push notifications!')
				exit(1)
			notify.push(config.pushbullet, 'note', title = 'Macrup', body = 'Successful Sync')

@macrup.command()
def delete():
	'''Delete backups of a directory'''
	pass

@macrup.command()
def watch():
	'''Watch for changes to a directory recursively'''
	pass

@macrup.command()
def forget():
	'''Stop watching a directory for changes'''
	pass

@macrup.command()
@click.pass_context
def ls(ctx):
	'''List watched directories and last sync time'''
	for dir in ctx.obj.watched:
		click.echo('%s\t%s'%(dir.synced, dir.name))
