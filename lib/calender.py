import json
import requests
from enum import Enum
from datetime import datetime
from dateutil.parser import parse

import errors


def _calender_json_hook(d):
    if 'allDay' in d:
        cat_name = d['category_label'].lower()
        try:
            cat = CalenderCategory[cat_name]
        except KeyError:
            cat = CalenderCategory.unknown

        return LazyEvent(
            title=d['title'],
            description=d['description'].strip(),
            where=d['where'],
            time=parse(d['start']),
            end=parse(d['end']) if d['end'] else None,
            raw=d,
            all_day=d['allDay'],
            bg_color=d['bgcolor'],
            fg_color=d['fgcolor'],
            category=cat,
            url=d['url']
        )
    return d


class Calender(list):
    '''
    A list of calender :class:`LazyEvent` s for a given class

    Args:
        * `id_` (int): the classes id
        * `token` - from :func:`__init__.login`
        * `start` (int or :class:`datetime.datetime`) -
            defaults to the begining of the world
        * `end` (int or :class:`datetime.datetime`) -
            defaults to the (foreseeable) end of time
    '''

    def __init__(self, id_, token, start=0, end=3000000000):
        if isinstance(start, datetime):
            start = (start - datetime(1970, 1, 1)).total_seconds()
        if isinstance(end, datetime):
            end = (end - datetime(1970, 1, 1)).total_seconds()
        

        r = requests.get('https://telopeapark.managebac.com/groups/{}'
                         '/events?start={}&end={}'.format(id_, start, end),
                         # Managebac REQUIRED those headers :)
                         cookies=token, headers={
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json'
                         })
        if r.ok and r.status_code == 200:
            map(self.append,
                json.loads(r.text, object_hook=_calender_json_hook))
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException


class CalenderCategory(Enum):
    '''
    Category for Calender Events
    '''
    event = 0
    project = 1
    task = 2
    examination = 3
    unknown = 4


class LazyEvent():
    '''
    The events are a big part of managebac, so there is more info than the
    calender gives us.  This class just has the info from the calender.

    Attributes:
        * `title` (str)
        * `description` (str) - raw, no HTML
        * `where` (str)
        * `start` (:class:`datetime.datetime`)
        * `end` (:class:`datetime.datetime` or None)

        * `raw` (dict) - raw json representation
        * `all_day` (bool)
        * `bg_color` (str) - hex color
        * `fg_color` (str) - hex color
        * `category` (:class:`CalenderCategory`)
        * `url` (str)
    '''

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __unicode__(self):
        return 'LazyEvent([{}] {} ({}) <{}> at {}, from {} - {}, all day: {})' \
            .format(self.category, self.title, self.description, self.url,
                    self.where, self.time, self.end, self.all_day)
