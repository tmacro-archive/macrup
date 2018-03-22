import click
from .user import Backup
from .notify import push
import yaml
import urllib.request

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
def macrup(ctx, remote, watched, exclude, prefix, notify, dry_run):
	ctx.obj = Backup(dry_run = dry_run)
	print(remote, watched, exclude, prefix, notify)
	if remote:
		ctx.obj.setRemote(remote)
	if watched:
		for w in watched:
			ctx.obj.addWatched(w)
	if exclude:
		for e in exclude:
			ctx.obj._exclude.append(e)
	if prefix:
		ctx.obj._prefix = prefix
	if notify:
		ctx.obj._notify = notify

@macrup.command()
@click.pass_context
def backup(ctx):
	'''Backup a directory'''
	if not checkConnection():
		click.echo('No internet connection detected, delaying backup.')
		exit(0)
	if not ctx.obj.watched:
		click.echo('No watched directories')
	failed = []
	for dir in ctx.obj.watched:
		if not ctx.obj._backup(dir):
			failed.append(dir)
	if failed:
		click.echo("Some directories failed to sync!")
		click.echo('\n'.join([d.as_posix() for d in failed]))
		if ctx.obj.notify:
			if ctx.obj.pushbullet is None:
				click.echo('You must supply a Pushbullet API key to enable push notifications!')
				exit(1)
			push(ctx.obj.pushbullet, 'note', title = 'Macrup', body = 'Failed Sync\n' + '\n'.join([d.as_posix() for d in failed]))
	else:
		if ctx.obj.notify:
			if ctx.obj.pushbullet is None:
				click.echo('You must supply a Pushbullet API key to enable push notifications!')
				exit(1)
			push(ctx.obj.pushbullet, 'note', title = 'Macrup', body = 'Successful Sync')


@macrup.command()
@click.pass_context
# @click.argument('bucket')
# @click.argument('dest')
def restore(ctx):
	'''Restore a bucket to a directory'''
	if not checkConnection():
		click.echo('No internet connection detected, can not restore.')
		exit(0)
	if not ctx.obj.watched:
		click.echo('No watched directories')
	failed = []
	for dir in ctx.obj.watched:
		if not ctx.obj._restore(dir):
			failed.append(dir)

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
		click.echo(dir)
