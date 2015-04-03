import re
import redis
import pickle
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse

import errors


red = redis.StrictRedis(host='localhost', port=6379, db=0)
try:
    red.get('test')
except ConnectionError:
    red = None

_POST_COMMENT_URL = \
    'https://telopeapark.managebac.com/groups/{}/messages/{}/comments'
_CACHE_EXPIRE = 5 * 60  # 5min


class Messages(list):
    '''
    Represents the :class:`Message` s for a given class on managebac

    Gets the messages as :class:`LazyMessage` s

    Raises:
        BadToken, ManageBacCommunicationException
    '''

    def __init__(self, url, token):
        r = requests.get(url + '/archive', cookies=token)

        if r.ok and r.status_code == 200:
            soup = BeautifulSoup(r.text)

            class_name = soup.h1.div.next_sibling.next_sibling.text

            for topic in soup.findAll(class_='topic'):
                url = topic.a['href']

                self.append(LazyMessage(
                    id_=int(re.search('/messages/([0-9]+)', url).group(1)),
                    class_id=int(re.search(
                        '/[classesgroups]+/([0-9]+)/', url).group(1)),
                    class_name=class_name,
                    by=re.search('by\n(.+)', topic.label.text).group(1),
                    title=topic.a.text
                ))
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException

class Message():
    '''
    Represents a message that you post on managebac

    The constructor downloads a message and fill the object

    Args:
        * `url` (str) - url of the message
        * `token` - returned by :func:`managebac.login`

    Sets Values:
        * `id_` (int)
        * `title` (string)
        * `by` (string)
        * `text` (string) - just a string, no HTML
        * `time` (:class:`datetime.datetime`)
        * `avatar` (string): a image URL
        * `comments` (list of :class:`Comment`)
        * `class_name` (string)
        * `class_id` (int)

    Raises:
        BadToken, ManageBacCommunicationException
    '''

    def __init__(self, url, token):
        r = requests.get(url, cookies=token)

        if r.ok and r.status_code == 200:
            self.id_ = int(re.search('/messages/([0-9]+)', url).group(1))
            self.class_id = int(re.search(
                '/[classesgroups]+/([0-9]+)/', url).group(1))

            soup = BeautifulSoup(r.text)

            self.class_name = soup.h1.div.next_sibling.next_sibling.text
            message = soup.find(class_='reply_target')
            self.avatar = message.img['src']
            self.time = parse(message.find(class_='time').text)
            self.by = message.strong.text.strip()
            self.title = message.a.text
            self.text = message.find(class_='content').text

            self.comments = []
            for el in message.find_next_siblings(class_='topic'):
                self.comments.append(Comment(
                    avatar=el.img['src'],
                    time=parse(el.find(class_='time').text),
                    by=el.strong.text.strip(),
                    text=el.find(class_='content').text
                ))

            self.loaded = True
            if red:
                cache_id = 'cache:message:{}'.format(self.id_)
                red.set(cache_id, pickle.dumps(self))
                red.expire(cache_id, _CACHE_EXPIRE)
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException

    def post_comment(self, text, token):
        '''
        Post a comment below the message on managebac.

        Args:
            * `text` (str) - plain text to post
            * `token` - the users login from :func:`managebac.login`
        '''
        r = requests.post(_POST_COMMENT_URL.format(self.class_id, self.id_),
                          cookies=token, data={'post[body]': text})

        if r.ok and r.status_code == 200:
            return
        elif r.status_code == 302:
            raise errors.BadToken
        else:
            raise errors.ManageBacCommunicationException

    def __unicode__(self):
        return u'Message({} said "{}":"{}" ({}), at {} in {} ({}), {})'.format(
            self.by, self.title, self.text, self.id_, self.time,
            self.class_name, self.class_id, map(unicode, self.comments))


class LazyMessage(Message):
    '''
    A lazy loaded message class

    By default, it only includes the following attributes:
        * `id_` (int)
        * `title` (string)
        * `by` (string)
        * `class_name` (str)
        * `class_id` (int)

    It also introduces the `loaded` (bool) attribute
    '''

    def __init__(self, **kwargs):
        self.loaded = False
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        if red:
            old = red.get('cache:message:{}'.format(self.id_))
            if old:
                self = pickle.loads(old)
                self.loaded = True

    def load(self, token):
        '''
        Same as :class:`Message`, but with the URL autogenerated
        '''
        Message.__init__(self, 'https://telopeapark.managebac.com/groups/{}'
                         '/messages/{}'.format(self.class_id, self.id_),
                         token)

    def __unicode__(self):
        if self.loaded:
            return Message.__unicode__(self)
        return u'LazyMessage({} said {} ({}), in {} ({}))'.format(
            self.by, self.title, self.id_, self.class_name, self.class_id)


class Comment():
    '''
    A (dumb) object that represents a comment on a :class:`Message`

    The constructor makes a new Comment from the kwargs.  Expects the
    same args as a :class:`Message`, but without the `id_`,
    `title` or `class_*`
    '''

    def __init__(self, **kwargs):
        '''
        '''
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __unicode__(self):
        return u'Comment({} said "{}", at {})'.format(
            self.by, self.text, self.time)
