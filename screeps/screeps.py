
# Copyright @dzhu
# https://gist.github.com/dzhu/d6999d126d0182973b5c

import json

from base64 import b64decode
from collections import OrderedDict
from cStringIO import StringIO
from gzip import GzipFile

import requests

## Python before 2.7.10 or so has somewhat broken SSL support that throws a warning; suppress it
import warnings; warnings.filterwarnings('ignore', message='.*true sslcontext object.*')

class ScreepsConnection(object):
    def req(self, func, path, **args):
        r = func(self.prefix + path, headers={'X-Token': self.token, 'X-Username': self.token}, **args)
        self.token = r.headers.get('X-Token', self.token)
        try:
            return json.loads(r.text, object_pairs_hook=OrderedDict)
        except ValueError:
            print 'JSON failure:', r.text
        return None

    def get(self, _path, **args): return self.req(requests.get, _path, params=args)
    def post(self, _path, **args): return self.req(requests.post, _path, json=args)

    def __init__(self, u=None, p=None, ptr=False):
        self.ptr = ptr
        self.prefix = 'https://screeps.com/ptr/api/' if ptr else 'https://screeps.com/api/'
        self.token = None
        if u is not None and p is not None:
            self.token = self.post('auth/signin', email=u, password=p)['token']


    #### miscellaneous user methods

    def me(self):
        return self.get('auth/me')

    def overview(self, interval=8, statName='energyHarvested'):
        return self.get('user/overview', interval=interval, statName=statName)
        
    def stats(self,id,interval=8):
        return self.get('user/stats',id=id,interval=interval)

    def user_find(self, username):
        return self.get('user/find', username=username)

    def memory(self, path=''):
        ret = self.get('user/memory', path=path)
        if 'data' in ret:
            ret['data'] = json.load(GzipFile(fileobj=StringIO(b64decode(ret['data'][3:]))))
        return ret

    def set_memory(self, path, value):
        return self.post('user/memory', path=path, value=value)

    def console(self, cmd):
        return self.post('user/console', expression=cmd)


    #### room info methods

    def room_overview(self, room, interval=8):
        return self.get('game/room-overview', interval=interval, room=room)

    def room_terrain(self, room, encoded=False):
        return self.get('game/room-terrain', room=room, encoded=('1' if encoded else None))

    def room_status(self, room):
        return self.get('game/room-status', room=room)


    #### leaderboard methods

    ## omit season to get current season
    def board_list(self, limit=10, offset=0, season=None, mode='world'):
        if season is None:
            ## find current season (the one with max start time among all seasons)
            seasons = self.board_seasons['seasons']
            season = max(seasons, key=lambda s: s['date'])['_id']

        ret = self.get('leaderboard/list', limit=limit, offset=offset, mode=mode, season=season)
        for d in ret['list']:
            d['username'] = ret['users'][d['user']]['username']
        return ret

    ## omit season to get all seasons
    def board_find(self, username, season=None, mode='world'):
        return self.get('leaderboard/find', mode=mode, season=season, username=username)

    def board_seasons(self):
        return self.get('leaderboard/seasons')


    #### messaging methods

    def msg_index(self):
        return self.get('user/messages/index')

    def msg_list(self, respondent):
        return self.get('user/messages/list', respondent=respondent)

    def msg_send(self, respondent, text):
        return self.post('user/messages/send', respondent=respondent, text=text)


    #### world manipulation methods

    def gen_unique_name(self, type):
        return self.post('game/gen-unique-object-name', type=type)

    def flag_create(self, room, x, y, name=None, color='white', secondaryColor=None):
        if name is None:
            name = self.gen_unique_name('flag')['name']
        if secondaryColor is None:
            secondaryColor = color

        return self.post('game/create-flag', room=room, x=x, y=y, name=name, color=color, secondaryColor=secondaryColor)

    def flag_change_pos(self, _id, room, x, y):
        return self.post('game/change-flag', _id=_id, room=room, x=x, y=y)

    def flag_change_color(self, _id, color, secondaryColor=None):
        if secondaryColor is None:
            secondaryColor = color

        return self.post('game/change-flag-color', _id=_id, color=color, secondaryColor=secondaryColor)

    def create_site(self, typ, room, x, y):
        return self.post('game/create-construction', structureType=typ, room=room, x=x, y=y)


    #### other methods

    def time(self):
        return self.get('game/time')['time']

    def map_stats(self, rooms, statName):
        return self.post('game/map-stats', rooms=rooms, statName=statName)

    def history(self, room, tick):
        return self.get('../room-history/%s/%s.json' % (room, tick - (tick % 20)))

    def activate_ptr(self):
        if self.ptr:
            return self.post('user/activate-ptr')
