# ManageBacToTheFuture: ManageBac for Humans
# Copyright (C) 2015 Sam Parkinson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse

import errors


_URL_FORMAT = ('https://telopeapark.managebac.com/classes/{0}'
               '/assets?group_id={0}&page={1}&q[s]=created_at+asc{2}').format

class Files(list):
    '''
    Represents a list of files from managebac

    The constructor create a new files list from a given managebac url

    Args:
        * `url` (str) - url of the files page, in the format::

                https://telopeapark.managebac.com/classes/{int}/assets

        * `token` - returned by :func:`managebac.login`
        * `page` (int, optional) - the page number, starts from 1
        * `folder_id` (int, optional) - the folder id to get files from

    Raises:
        BadToken, ManageBacCommunicationException
    '''

    def __init__(self, url, token, page=1, folder_id=None):
        '''
        '''

        self.class_id = int(re.search('/classes/([0-9]+)/', url).group(1))
        self.folder_id = folder_id
        f = '&folder_id={}'.format(self.folder_id) if self.folder_id else ''

        r = requests.get(_URL_FORMAT(self.class_id, page, f), cookies=token)
        if r.ok and r.status_code == 200:
            soup = BeautifulSoup(r.text)
            root = soup.find(class_='assets-layout')

            for folder in root.findAll(class_='folder'):
                a = folder.find(class_='folder-name')
                id_ = re.search('folder_id=([0-9]+)', a['href']).group(1)

                self.append(Folder(
                    id_=int(id_),
                    name=a.text,
                    time=parse(folder.find(class_='time-cell').text)
                ))

            for file_ in root.findAll(class_='file'):
                a = file_.find(class_='file-name')
                details = file_.find(class_='details').text

                # The "Task: ..." under the name
                grey = file_.find(class_='grey')

                self.append(File(
                    url=a['href'],
                    name=a.text,
                    by=re.search('by\n(.+)', details).group(1),
                    size=file_.find(class_='size-cell').text,
                    time=parse(file_.find(class_='time-cell').text),
                    related=grey['href'] if grey else None
                ))

            self.sort(key=lambda x: x.time)
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException


class Folder():
    '''
    A object that is a child of :class:`Files`

    The constructor makes a new Folder from the kwargs.

    Args (as kwargs):
        * `id_` (int)
        * `name` (str)
        * `time` (:class:`datetime.datetime`)
    '''

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __unicode__(self):
        return u'Folder({} ({}), modified at {})'.format(
            self.name, self.id_, self.time)

class File():
    '''
    A object that is a child of :class:`Files`

    The constructor akes a new File from the kwargs.

    Args (as kwargs):
        * `url` (str)
        * `name` (str)
        * `time` (:class:`datetime.datetime`)
        * `by` (str)
        * `size` (str)
        * `related` (str) - url of a related event, can be `None`
    '''

    def __init__(self, **kwargs):
        '''
        '''
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __unicode__(self):
        return u'File({} <{}>, modified at {} by {}, related: {})'.format(
            self.name, self.url, self.time, self.by, self.related)
