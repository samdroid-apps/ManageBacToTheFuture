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

from requests import TooManyRedirects
from flask import Flask, jsonify, request
from managebac.files import Folder, File
from managebac.calender import LazyEvent
from managebac.message import LazyMessage, Message
from managebac import login, Class, Classes
from managebac.errors import BadLogin, BadToken, ManageBacCommunicationException

app = Flask(__name__)

@app.after_request
def cross_domain(response):
    h = response.headers
    h['Access-Control-Allow-Origin'] = '*'
    h['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS, POST'
    h['Access-Control-Allow-Headers'] = 'X-Token'
    h['Access-Control-Max-Age'] = '0'
    return response


def catch_errors(f):
    def closure(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BadLogin:
            return jsonify(type='BadLogin',
                           text='Incorrect username or password'), 403
        except (BadToken, TooManyRedirects):
            return jsonify(type='BadToken',
                           text='Please reauthenticate'), 403
        except ManageBacCommunicationException:
            return jsonify(type='ManageBacCommunicationException',
                           text='Can\'t reach managebac right now'), 500
    closure.__name__ = 'error_hardened_' + f.__name__
    return closure


def authenticated(f):
    def closure(*args, **kwargs):
        if not 'X-Token' in request.headers:
            raise BadToken
        else:
            kwargs['token'] = \
                {'_managebac_session': request.headers['X-Token']}
            return f(*args, **kwargs)
    closure.__name__ = 'authenticated_' + f.__name__
    return closure

@app.route('/login', methods=['POST'])
@catch_errors
def login_endpoint(*args, **kwargs):
    cookies = login(request.form['username'], request.form['password'])
    token = cookies['_managebac_session']
    return jsonify(token=token)


@app.route('/classes')
@catch_errors
@authenticated
def classes_endpoint(token, *args, **kwargs):
    l = []
    for c in Classes(token):
        d = c.__dict__
        d['id'] = d['id_']
        del d['id_']
        l.append(d)
    return jsonify(classes=l)


@app.route('/classes/<int:class_id>')
@catch_errors
@authenticated
def class_endpoint(class_id, token, *args, **kwargs):
    objs = Class(class_id).get_merged(token)
    dicts = []

    for x in objs:
        d = x.__dict__

        if isinstance(x, Folder):
            d['__name__'] = 'Folder'
            x.load(token)
            d['files'] = [f.__dict__ for f in x]
            d['id'] = d['id_']
            del d['id_']
        if isinstance(x, File):
            d['__name__'] = 'File'
        if isinstance(x, LazyEvent):
            d['__name__'] = 'Event'
            d['__lazy__'] = True
            d['end'] = x.end.isoformat() if x.end else None
            d['category'] = x.category.name
            del d['raw']
        if isinstance(x, LazyMessage):
            d['__name__'] = 'Message'
            d['__lazy__'] = True
            d['comments'] = [c.__dict__ for c in x.comments]
            d['id'] = d['id_']
            del d['id_']

        d['time'] = x.time.isoformat()

        dicts.append(d)

    return jsonify(items=dicts)


@app.route('/classes/<int:class_id>/messages/<int:id_>/comments',
            methods=['POST'])
@catch_errors
@authenticated
def post_comment(class_id, id_, token, *args, **kwargs):
    m = Message('https://telopeapark.managebac.com/groups/{}'
                '/messages/{}'.format(class_id, id_), token)
    m.post_comment(request.form['body'], token)
    return jsonify(ok=True)

@app.route('/classes/<int:class_id>/messages/<int:id_>')
@catch_errors
@authenticated
def get_message(class_id, id_, token, *args, **kwargs):
    m = Message('https://telopeapark.managebac.com/groups/{}'
                '/messages/{}'.format(class_id, id_), token)

    d = m.__dict__
    d['__name__'] = 'Message'
    d['comments'] = [c.__dict__ for c in m.comments]
    d['id'] = d['id_']
    del d['id_']
    return jsonify(message=d)


if __name__ == '__main__':
    # print '-' * 80
    # for rule in app.url_map.iter_rules():
    #     print '{:18s} {:45s} {}'.format(
    #         ', '.join(rule.methods), rule.endpoint, rule)
    # print '-' * 80

    app.run(debug=True)
