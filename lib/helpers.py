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

from enum import Enum


class ObjectType(Enum):
    '''
    Represents any object on managebac (that the api will deal with)
    '''
    event = 0
    message = 1
    unknown = 2
    files = 3
    file_ = 4


def get_type_from_url(url):
    '''
    Guesses the object type from the url

    Returns:
        An :class:`ObjectType` emum
    '''
    if 'events' in url:
        return ObjectType.event

    if 'messages' in url:
        return ObjectType.message

    if 'cf.managebac.com' in url:
        return ObjectType.file_

    if 'assets' in url:
        return ObjectType.file

    return ObjectType.unknown
    
