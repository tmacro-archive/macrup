import requests
from .log import Log

_log = Log('notify')

def push(token, type, **kwargs):
    _log.debug(kwargs)
    kwargs['type'] = type
    headers = {'Content-type': 'application/json', 'Access-Token': token}
    resp = requests.post('https://api.pushbullet.com/v2/pushes', json=kwargs, headers=headers)
    if not resp.status_code == 200:
        _log.error('Failed to push note with error %s'%resp.json().get('error'))
        return False
    return True