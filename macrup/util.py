from datetime import timedelta
import click


def convert_delta(interval):
	'''
		Converts a timespan represented as a space seperated string 
		Xy Xd Xh Xm Xs to a datetime.timedelta object
		all segments are optional eg '2d 12h', '10m 30s', '1y 30s'
	'''
	seg_map = dict( h='hours',
					m='minutes',
					s='seconds',
					y='years',
					d='days')
	segs = interval.split(' ')
	kwargs = { seg_map[seg[-1]]: int(seg[:-1]) for seg in segs }
	return timedelta(**kwargs)

class RequiredIf(click.Option):
    def __init__(self, *args, **kwargs):
        self._required_if = kwargs.pop('required_if')
        assert self._required_if, "'required_if' parameter required"
        kwargs['help'] = (kwargs.get('help', '') +
            ' NOTE: This argument is required if %s is specified' %
            self._required_if
        ).strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self._required_if in opts and not self.name in opts:
            raise click.BadArgumentUsage(
                "`%s` is required if `%s` is specified"%(self.name, self._required_if)
            )
        return super().handle_parse_result(ctx, opts, args)


class NotRequiredIf(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop('not_required_if')
        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs['help'] = (kwargs.get('help', '') +
            ' NOTE: This argument is mutually exclusive with %s' %
            self.not_required_if
        ).strip()
        super(NotRequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        we_are_present = self.name in opts
        other_present = self.not_required_if in opts

        if other_present:
            if we_are_present:
                raise click.UsageError(
                    "Illegal usage: `%s` is mutually exclusive with `%s`" % (
                        self.name, self.not_required_if))
            else:
                self.prompt = None

        return super(NotRequiredIf, self).handle_parse_result(
            ctx, opts, args)