import re
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse

import errors
import helpers


_BODY_START = len('$("#mailbox-container").html("')
_BODY_END = -1 - len('");\n$(\'#mailbox_spinner\').hide();')

def _get_body(text):
    # This is legit the weirdest api
    text = text[_BODY_START:_BODY_END]
    return text.replace('\\n', '\n').replace('\\\'', '\'') \
               .replace('\\"', '"').replace('\\/', '/')


def get_notifications(token):
    '''
    Get your notifications/messages from managebac

    Args:
        * token - the token from :func:`managebac.login`

    Returns:
        * list of :class:`Notification` objects for the user behind the token

    Raises:
        BadToken, ManageBacCommunicationException
    '''
    r = requests.get('https://telopeapark.managebac.com/mailboxes.js',
                     cookies=token)

    if r.ok and r.status_code == 200:
        soup = BeautifulSoup(_get_body(r.text))
        notifications = []

        for row in soup.tbody.findAll('tr'):
            # .contents has lots of new lines
            raw_title = row.contents[3].text
            match = re.match('\[(.*)\] (.*)', raw_title)
            if match:
                title = match.group(2)
                class_name = match.group(1)
            else:
                title = raw_title
                class_name = None

            notifications.append(Notification(
                id_=int(row['message_id']),
                title=title,
                class_name=class_name,
                by=row.contents[5].text.strip(),
                date=parse(row.contents[7].text)
            ))

        return notifications             
    elif r.status_code == 302:
        raise errors.BadToken
    else:
        raise errors.ManageBacCommunicationException


_BODY_URL_FORMAT = \
    'https://telopeapark.managebac.com/mailboxes/view_body?id={}'
DEPTH_METADATA = 0
DEPTH_BODY = 1

class Notification():
    '''
    A representation of a managebac notification/message

    Args (as kwargs):
        * `id_` (int)
        * `title` (str) - a sanitised title, does not include class_name
        * `class_name` (str) - 
            the name of the class this is related to,
            `None` if unknown
        * `by` (str) - who made this notification
        * `date` (:class:`datetime.datetime`)
    '''

    def __init__(self, **kwargs):
        self.depth = DEPTH_METADATA

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def get_body_url(self):
        '''
        Get a link to a HTML representation of the message contents
        '''
        return _BODY_URL_FORMAT.format(self.id_)

    def get_body_data(self, token):
        '''
        Downloads the message to find more data

        Sets Values:
            * `type` (int) - the :class:`managebac.helpers.ObjectType`
                of the message
            * `referenced_url` (str) - url of the referenced object
            * `referenced` (object) - the representation of the referenced object

        Raises
            BadToken, ManageBacCommunicationException
        '''
        r = requests.get(self.get_body_url(), cookies=token)

        if r.ok and r.status_code == 200:
            soup = BeautifulSoup(r.text)

            full_details = soup.find('a', text='View full details')
            click_here = soup.find('a', text='Click here')
            if full_details is not None:
                self.referenced_url = full_details['href']
            elif click_here is not None:
                self.referenced_url = click_here['href']
            else:
                self.referenced_url = soup.a['href']

            self.type = helpers.get_type_from_url(self.referenced_url)
            self.depth = DEPTH_METADATA
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException
    
    
    def __unicode__(self):
        return 'Notification([{}] {} ({}) by {}, {} <{}>)'.format(
            self.class_name, self.title, self.id_, self.by, self.date,
            self.get_body_url())
