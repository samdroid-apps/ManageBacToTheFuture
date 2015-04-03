# -*- coding: utf8 -*-

import unittest
import httpretty
from dateutil.parser import parse

from __init__ import login
from mailbox import get_notifications
from message import Message
from files import Files, File, Folder
from calender import Calender, CalenderCategory
import errors


class TestLogin(unittest.TestCase):

    @httpretty.activate
    def test_good_login(self):
        httpretty.register_uri(
            httpretty.POST, 'https://telopeapark.managebac.com/sessions',
            status=200, body='You are being redirected',
            set_cookie=('_managebac_session=TOKEN; path=/; '
                        'expires=Fri, 03 Apr 2015 08:34:55 -0000; HttpOnly'))

        t = login('username', 'lolz')
        self.assertIn('_managebac_session', t, 'Dict has the token cookie')
        self.assertEqual(t['_managebac_session'], 'TOKEN',
                         'Token is as returned')

        body = httpretty.last_request().parsed_body
        self.assertEqual(body['login'], ['username'], 'Sent the right login')
        self.assertEqual(body['password'], ['lolz'], 'Sent the right password')

    @httpretty.activate
    def test_bad_login(self):
        httpretty.register_uri(
            httpretty.POST, 'https://telopeapark.managebac.com/sessions',
            status=200, body='Invalid login or password, please try again.')

        with self.assertRaises(errors.BadLogin):
            login('wrong', 'not')


_NOTIFICATIONS_BODY = '''$("#mailbox-container").html("<div id=\'mailbox-overlay\' syle=\'display: none\'><\/div>\n<div id=\'mailbox\'>\n<div class=\'wrapper\'>\n<div id=\'mailbox-overview\'>\n<div class=\'fr\' id=\'close-mailbox\'>\n<span class=\'i sprite-close\' ><\/span>\nClose\n<\/div>\n<h2 class=\'title\'>Message Notifications<\/h2>\n<div id=\'mailbox-header\'>\nSelect:\n<div class=\'tool-button\'>\n<a href=\"#\" onclick=\"Mailbox.toggleGroupSelection(&#39;all&#39;); return false;\">All<\/a>\n<\/div>\n<span style=\'color: #ccc\'>\n/\n<\/span>\n<div class=\'tool-button\'>\n<a href=\"#\" onclick=\"Mailbox.toggleGroupSelection(&#39;none&#39;); return false;\">None<\/a>\n<\/div>\n<span class=\'pipe\'>&ensp;<\/span>\n<div class=\'tool-button disabled toggleable\' id=\'move-to-trash\'>\n<span class=\'i sprite-trash\' ><\/span>\n<a href=\"#\" onclick=\"Mailbox.moveSelectedToTrash();; return false;\" style=\"color: #c00\">Delete Selected<\/a>\n<\/div>\n<span class=\'pipe\'>&ensp;<\/span>\n<div class=\'tool-button disabled toggleable\' id=\'mark-as-read\'>\n<span class=\'i sprite-check\' ><\/span>\n<a href=\"#\" onclick=\"Mailbox.markSelectedAsRead();; return false;\" style=\"color: green\">Mark as Read<\/a>\n<\/div>\n<img alt=\"Spinner\" class=\"spinner\" id=\"messages_bulk_actions_spinner\" src=\"//assets-2.managebac.com/assets/spinner-2aa6231d8d490b0b96740aef4ea644c1.gif\" style=\"display:none; vertical-align:middle\" />\n<\/div>\n<table class=\'wide clean nosideborders messages\'>\n<thead>\n<tr>\n<th class=\'vab\' style=\'width: 10px\'><\/th>\n<th>Subject<\/th>\n<th>From<\/th>\n<th>Received<\/th>\n<\/tr>\n<\/thead>\n<tbody>\n<tr class=\'eor message-row\' message_id=\'47801611\'>\n<td class=\'tac vac\'><input class=\"message-select\" id=\"mark_message_47801611\" name=\"mark_message_47801611\" type=\"checkbox\" value=\"1\" /><\/td>\n<td class=\'message-data\'>[IB MYP GEOGRAPHY Year 9 (Line 7) (Year 9)] Grades Posted<\/td>\n<td class=\'message-data nowrap\'>\nManagebac\n<\/td>\n<td class=\'message-data nowrap\'>Apr 02, 2015<\/td>\n<\/tr>\n<tr class=\'eor message-row\' message_id=\'47792433\'>\n<td class=\'tac vac\'><input class=\"message-select\" id=\"mark_message_47792433\" name=\"mark_message_47792433\" type=\"checkbox\" value=\"1\" /><\/td>\n<td class=\'message-data\'>[IB MYP 2015 YEAR 9 SCIENCE (Year 9)] Excursion<\/td>\n<td class=\'message-data nowrap\'>\nTeacher\n<\/td>\n<td class=\'message-data nowrap\'>Apr 02, 2015<\/td>\n<\/tr>\n<\/tbody>\n<\/table>\n<div id=\'bottom-links\'>\n\n<\/div>\n<\/div>\n<\/div>\n<script type=\'text/javascript\'>\n  //<![CDATA[\n    jQuery(function() {\n      Mailbox.initialize(1);\n    })\n  //]]>\n<\/script>\n<\/div>\n");
$('#mailbox_spinner').hide();'''


class TestMailbox(unittest.TestCase):

    @httpretty.activate
    def test_bad_token(self):
        httpretty.register_uri(
            httpretty.GET, 'https://telopeapark.managebac.com/mailboxes.js',
            status=302, body='You are being redirected')

        with self.assertRaises(errors.BadToken):
            get_notifications({})

    @httpretty.activate
    def test_good_token(self):
        httpretty.register_uri(
            httpretty.GET, 'https://telopeapark.managebac.com/mailboxes.js',
            status=200, body=_NOTIFICATIONS_BODY)

        n = get_notifications({'_managebac_session': 'TOKEN'})
        self.assertEqual(len(n), 2, 'Right number of notifications')

        self.assertEqual(n[0].id_, 47801611)
        self.assertEqual(n[0].title, 'Grades Posted')
        self.assertEqual(n[0].class_name, 'IB MYP GEOGRAPHY Year 9 (Line 7) (Year 9)')
        self.assertEqual(n[0].by, 'Managebac')

        self.assertIn('_managebac_session=TOKEN',
                      httpretty.last_request().headers['Cookie'],
                      'Sent the token as a cookie')


_MESSAGE_URL = ('https://telopeapark.managebac.com/groups/10363123'
                '/messages/11047944')
_MESSAGE_BODY = u'''<h1>
<div class="sub-header"><a href="https://telopeapark.managebac.com/">School</a></div>
<a href="/classes/10363123">Class Name</a>
</h1>

<div id="messages-layout">
<div class="topic clearfix reply_target"><div class="frame"><div class="img-shadow avatar tiny"><img alt="User tiny" src="//assets-0.managebac.com/assets/user_tiny-0529def52d87ff66c070f6c6daecc3ed.png"></div></div><div class="content-wrapper"><div class="topic-description"><strong>Oli</strong><div class="time">Wed, 4 Mar at 9:45 AM</div></div><a class="title" href="/groups/10363123/messages/11047944">Friendly Reminder</a><div class="content"><p>Just reminding you all to submit your assignments tomorrow!</p></div></div></div>

<h2 class="section-header" style="color: #999;">4 comments</h2>

<div class="topic clearfix compact"><div class="frame"><div class="img-shadow avatar tiny"><img alt="User tiny" src="//assets-0.managebac.com/assets/user_tiny-0529def52d87ff66c070f6c6daecc3ed.png"></div></div><div class="content-wrapper"><div class="reply-description"><strong>A</strong><div class="time">Wed, 4 Mar at 9:46 AM</div></div><div class="content"><p>( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)( ͡° ͜ʖ ͡°)</p></div></div></div>

<div class="topic clearfix compact"><div class="frame"><div class="img-shadow avatar tiny"><img alt="Tiny laamma original" src="https://cf.managebac.com/uploads/photo/file/16045554/tiny_laamma_original.jpg?&amp;Expires=1428012567&amp;Signature=MrvuGA9m2INdbT-8y-9iwNMbM7Gk0d18d0pRJvtKTDwI5bdA2kLIZKkbpC1uoLScUb~jUhukvMu2irPC51ZZXsVo4a0hb6zXqEWmU8~krR8mtjKqPJMqXUXygOriPkqzMbGrSm9-hmNRmbY6khn1vwFEbfkAULVYGTynrI4hTb1150V20877NlRZUe0fwMdXo5MIR7E3YXpSVVKQXOfxCW1q2oZLCDZ-ELJtvx8ZOZnyQv8awHDYUFXB7cL9NAKUqcuApaEVUl6dAk8M5VdcJZY6TeQNjyxSOAQXgFTesCobvQsAJuogVaVM1kyem~zvFkU2lt-JqpR3Ir7Fn4yRLw__&amp;Key-Pair-Id=APKAIONV4W2WDGROD6WA"></div></div><div class="content-wrapper"><div class="reply-description"><strong>Cham</strong><div class="time">Wed, 4 Mar at 7:48 PM</div></div><div class="content"><p>( ͡° ͜ʖ ͡°)</p></div></div></div>

<div class="topic clearfix compact"><div class="frame"><div class="img-shadow avatar tiny"><img alt="User tiny" src="//assets-0.managebac.com/assets/user_tiny-0529def52d87ff66c070f6c6daecc3ed.png"></div></div><div class="content-wrapper"><div class="reply-description"><strong>V-man</strong><div class="time">Wed, 4 Mar at 7:53 PM</div></div><div class="content"><p>I've joined the thread ( ͡° ͜ʖ ͡°)</p></div></div></div>

<div class="topic clearfix compact"><div class="frame"><div class="img-shadow avatar tiny"><img alt="User tiny" src="//assets-0.managebac.com/assets/user_tiny-0529def52d87ff66c070f6c6daecc3ed.png"></div></div><div class="content-wrapper"><div class="reply-description"><strong>Ish</strong><div class="time">Thu, 5 Mar at 12:04 AM</div></div><div class="content"><p>well ¯\_(ツ)_/¯</p></div></div></div></div>'''

class TestMessage(unittest.TestCase):

    @httpretty.activate
    def test_bad_token(self):
        httpretty.register_uri(
            httpretty.GET, _MESSAGE_URL,
            status=302, body='You are being redirected')

        with self.assertRaises(errors.BadToken):
            Message(_MESSAGE_URL, {})

    @httpretty.activate
    def test_good_token(self):
        httpretty.register_uri(
            httpretty.GET, _MESSAGE_URL,
            status=200, body=_MESSAGE_BODY)

        m = Message(_MESSAGE_URL, {'_managebac_session': 'TOKEN'})

        self.assertEqual(m.id_, 11047944)
        self.assertEqual(m.class_name, 'Class Name')
        self.assertEqual(m.class_id, 10363123)
        self.assertEqual(m.title, 'Friendly Reminder')
        self.assertEqual(m.by, 'Oli')
        self.assertEqual(m.text, 'Just reminding you all to submit '
                         'your assignments tomorrow!')
        self.assertEqual(m.avatar, '//assets-0.managebac.com/assets'
                        '/user_tiny-0529def52d87ff66c070f6c6daecc3ed.png')
        self.assertEqual(len(m.comments), 4)

        self.assertEqual(m.comments[1].by, 'Cham')
        self.assertEqual(m.comments[1].text, u'( ͡° ͜ʖ ͡°)')

        self.assertIn('_managebac_session=TOKEN',
                      httpretty.last_request().headers['Cookie'],
                      'Sent the token as a cookie')

    @httpretty.activate
    def test_post_comment(self):
        httpretty.register_uri(
            httpretty.GET, _MESSAGE_URL,
            status=200, body=_MESSAGE_BODY)
        httpretty.register_uri(
            httpretty.POST, _MESSAGE_URL + '/comments',
            status=200, body='OK')

        m = Message(_MESSAGE_URL, {'_managebac_session': 'TOKEN'})
        m.post_comment('Hello World!', {'_managebac_session': 'TOKEN'})

        body = httpretty.last_request().parsed_body
        self.assertEqual(body['post[body]'], ['Hello World!'])
        self.assertIn('_managebac_session=TOKEN',
                      httpretty.last_request().headers['Cookie'],
                      'Sent the token as a cookie')


_FILES_URL = 'https://telopeapark.managebac.com/classes/10363179/assets'
with open('test_files_page.html') as f:
    _FILES_BODY = f.read()

class TestFiles(unittest.TestCase):

    @httpretty.activate
    def test_bad_token(self):
        httpretty.register_uri(
            httpretty.GET, _FILES_URL,
            status=302, body='You are being redirected')

        with self.assertRaises(errors.BadToken):
            Files(_FILES_URL, {})

    def assert_body(self, f):
        self.assertEqual(f[0].name, 'CREST_Timeline2015.doc')
        self.assertIsInstance(f[0], File)

        self.assertEqual(f[1].name, 'CREST 2015')
        self.assertEqual(f[1].id_, 97558)
        self.assertIsInstance(f[1], Folder)

    @httpretty.activate
    def test_good_token(self):
        httpretty.register_uri(httpretty.GET,
            _FILES_URL + '?group_id=10363179&page=1&q[s]=created_at+asc',
            status=200, body=_FILES_BODY)

        f = Files(_FILES_URL, {'_managebac_session': 'TOKEN'})
        self.assert_body(f)

        self.assertIn('_managebac_session=TOKEN',
                      httpretty.last_request().headers['Cookie'],
                      'Sent the token as a cookie')

    @httpretty.activate
    def test_folder_get(self):
        httpretty.register_uri(httpretty.GET,
            _FILES_URL + '?group_id=10363179&page=1&q[s]=created_at+asc'
            '&folder_id=123', status=200, body=_FILES_BODY)

        f = Files(_FILES_URL, {'_managebac_session': 'TOKEN'}, folder_id=123)
        self.assert_body(f)


_CALENDER_URL = ('https://telopeapark.managebac.com/groups/10363179/events?'
                 'start=1427634000&end=1431266400')
_CALENDER_CLASS = 10363179
_CALENDER_BODY = '[{"id":12860660,"title":"Draft Practical Report - aim, hypothesis, method","where":null,"start":"2015-03-31T09:00:00.000+11:00","end":null,"allDay":false,"className":"indicator project","description":"DRAFT only - outlining what you intend to do, what data you are collecting and how you intend to collect it.\\r\\nUse the Investigation Planner provided - Q1-7.\\r\\nSubmit a hard copy to the teacher by Tuesday 31 March, Wk9 Term 1.","url":"/classes/10363179/events/12860660","hint_url":"/classes/10363179/events/12860660/hint","editable":false,"resizable":false,"ia_copy":false,"bgcolor":"#528C00","fgcolor":"#fff","category_label":"Project","is_group_root":true,"has_children":false,"group_root_id":null,"orig_editable":false},{"id":12895588,"title":"Brain & Kidney Dissections","where":"Science lab 2","start":"2015-03-31T09:00:00.000+11:00","end":null,"allDay":false,"className":"indicator event","description":"Dissect the brain \\r\\nhttp://www.hometrainingtools.com/a/brain-dissection-project\\r\\nIdentify the parts of the brain (see attached pdf files)\\r\\n\\r\\nDissect a kidney\\r\\nWatch audiovisual first - https://www.youtube.com/watch?v=IPnEN8t1Rjk\\r\\nComplete attached questions worksheet","url":"/classes/10363179/events/12895588","hint_url":"/classes/10363179/events/12895588/hint","editable":false,"resizable":false,"ia_copy":false,"bgcolor":"#339933","fgcolor":"#fff","category_label":"Event","is_group_root":true,"has_children":false,"group_root_id":null,"orig_editable":false},{"id":12900364,"title":"Ecosystems - flow of energy in an ecosystem","where":"Science Lab 2","start":"2015-04-01T10:00:00.000+11:00","end":null,"allDay":false,"className":"indicator event","description":"Science Dimensions Bk 3 - chapter 6.1\\r\\nClass discussion: energy in ecosystems, conservation of matter, food pyramids\\r\\nAnswer all questions p158-9","url":"/classes/10363179/events/12900364","hint_url":"/classes/10363179/events/12900364/hint","editable":false,"resizable":false,"ia_copy":false,"bgcolor":"#339933","fgcolor":"#fff","category_label":"Event","is_group_root":true,"has_children":false,"group_root_id":null,"orig_editable":false}]'


class TestCalender(unittest.TestCase):

    @httpretty.activate
    def test_bad_token(self):
        httpretty.register_uri(
            httpretty.GET, _CALENDER_URL,
            status=302, body='You are being redirected')

        with self.assertRaises(errors.BadToken):
            Calender(_CALENDER_CLASS, {}, start=1427634000, end=1431266400)

    @httpretty.activate
    def test_good_token(self):
        httpretty.register_uri(httpretty.GET, _CALENDER_URL,
            status=200, body=_CALENDER_BODY)

        c = Calender(_CALENDER_CLASS, {'_managebac_session': 'TOKEN'},
                     start=1427634000, end=1431266400)
        self.assertEqual(len(c), 3)

        self.assertEqual(c[0].category, CalenderCategory.project)
        self.assertEqual(c[0].title,
                         'Draft Practical Report - aim, hypothesis, method')
        self.assertEqual(c[0].all_day, False)
        self.assertEqual(c[0].time, parse('2015-03-31 09:00:00+11:00'))
        self.assertEqual(c[0].end, None)

        self.assertIn('_managebac_session=TOKEN',
                      httpretty.last_request().headers['Cookie'],
                      'Sent the token as a cookie')

if __name__ == '__main__':
    unittest.main()
