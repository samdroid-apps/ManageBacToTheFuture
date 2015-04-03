import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

from files import Files
from message import Messages
from calender import Calender
import errors


def login(username, password):
    '''
    Logs into ManageBac

    Returns a token

    Raises:
        ManageBacCommunicationException, BadLogin
    '''
    r = requests.post('https://telopeapark.managebac.com/sessions',
                      data={'login': username, 'password': password})

    if r.ok and r.status_code == 200:
        if 'Invalid login or password, please try again.' in r.text:
            # I wish managebac was more RESTful
            raise errors.BadLogin
        else:
            return {'_managebac_session': r.cookies['_managebac_session']}
    else:
        raise errors.ManageBacCommunicationException


class Class():
    '''
    Represents a class on managebac
    '''

    def __init__(self, id_, name=None):
        self.id_ = id_
        self.name = name

    def get_files(self, token):
        '''
        Get the class's files section

        Returns :class:`managebac.files.Files`
        '''
        return Files('https://telopeapark.managebac.com/classes/'
                     '{}/assets'.format(self.id_), token)

    def get_messages(self, token):
        '''
        Get the class's files section

        Returns :class:`managebac.message.Messages`
        '''
        return Messages('https://telopeapark.managebac.com/classes/'
                     '{}/messages'.format(self.id_), token)

    def get_calender(self, token, start=0, end=3000000000):
        '''
        Get the class's calender section

        Returns :class:`managebac.calender.Calender`
        '''
        return Calender(self.id_, token, start=start, end=end)

    def get_merged(self, token):
        fil = self.get_files(token)
        msg = self.get_messages(token)
        cal = self.get_calender(token)

        for m in msg:
            if not m.loaded:
                m.load(token)

        l = fil + msg + cal

        # <HACK>
        # Naive convertion between tz and non-tz objects
        for x in l:
            x.time = x.time.replace(tzinfo=None)
        # </HACK>

        l.sort(key=lambda x: x.time)
        l.reverse()
        return l


class Classes(list):
    '''
    Gets and holds a list of :class:`Class` es for a given user

    Downloads the classes of the user behind the token.

    Raises:
        BadToken, ManageBacCommunicationException
    '''

    def __init__(self, token):
        r = requests.get('https://telopeapark.managebac.com/home',
                         cookies=token)

        if r.ok and r.status_code == 200:
            soup = BeautifulSoup(r.text)

            # Dashboard | Profile | MYP | [Classes] | Groups
            menu = soup.find(id='menu').findAll('li')[3]

            # The 1st a is just a link to a classes list
            for a in menu.findAll('a')[1:]:
                self.append(Class(
                    id_=int(re.search(
                        '/classes/([0-9]+)', a['href']).group(1)),
                    name=a.text[len('\nIB MYP\n\n'):].strip('\n')
                ))
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException
